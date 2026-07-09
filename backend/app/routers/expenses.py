"""
Expenses Router — submit, approve, reject, finance export.
All RBAC enforced server-side.
"""
import os
import uuid
from datetime import date, datetime, timezone
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.employee import Employee
from app.models.expense import Expense
from app.schemas.expense import ExpenseCreate, ExpenseActionRequest, ExpenseOut
from app.auth.dependencies import get_current_user, require_min_role, require_roles
from app.services.notification_service import notify_expense_submitted, notify_expense_resolved
from app.services.audit_service import log_action

router = APIRouter(prefix="/expenses", tags=["Expenses"])

UPLOAD_DIR = "uploads/receipts"
os.makedirs(UPLOAD_DIR, exist_ok=True)

AMOUNT_THRESHOLD_FINANCE = 10000  # INR — above this goes to finance too


def _find_approver(db: Session, employee: Employee) -> Optional[Employee]:
    """Manager is the first approver."""
    if employee.manager_id:
        return db.query(Employee).filter(Employee.id == employee.manager_id).first()
    return db.query(Employee).filter(Employee.role == "hr_admin").first()


@router.post("/submit", response_model=ExpenseOut, status_code=201)
async def submit_expense(
    amount: float = Form(...),
    currency: str = Form("INR"),
    category: str = Form(...),
    description: str = Form(...),
    receipt: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Employee submits an expense claim with optional receipt upload."""
    receipt_url = None
    receipt_filename = None

    if receipt and receipt.filename:
        ext = os.path.splitext(receipt.filename)[1]
        unique_name = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_name)
        content = await receipt.read()
        with open(file_path, "wb") as f:
            f.write(content)
        receipt_url = f"/{file_path}"
        receipt_filename = receipt.filename

    approver = _find_approver(db, current_user)
    initial_status = "submitted"

    expense = Expense(
        employee_id=current_user.id,
        amount=amount,
        currency=currency,
        category=category,
        description=description,
        receipt_url=receipt_url,
        receipt_filename=receipt_filename,
        status=initial_status,
        approver_id=approver.id if approver else None,
    )
    db.add(expense)
    db.flush()

    if approver:
        notify_expense_submitted(db, approver.id, current_user.name, expense.id, amount)

    log_action(db, current_user.id, "submit_expense", "expense", expense.id,
               {"amount": amount, "category": category})
    db.commit()
    db.refresh(expense)
    out = ExpenseOut.model_validate(expense, from_attributes=True)
    out.employee_name = current_user.name
    return out


@router.get("/mine", response_model=List[ExpenseOut])
def my_expenses(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    query = db.query(Expense).filter(Expense.employee_id == current_user.id)
    if status_filter:
        query = query.filter(Expense.status == status_filter)
    expenses = query.order_by(Expense.submitted_at.desc()).all()
    result = []
    for e in expenses:
        out = ExpenseOut.model_validate(e, from_attributes=True)
        out.employee_name = current_user.name
        result.append(out)
    return result


@router.get("/queue", response_model=List[ExpenseOut])
def approval_queue(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_min_role("manager")),
):
    """
    Manager sees expenses assigned to them.
    HR Admin sees all pending expenses.
    """
    query = db.query(Expense)
    if current_user.role == "manager":
        query = query.filter(
            Expense.approver_id == current_user.id,
            Expense.status.in_(["submitted", "with_manager"]),
        )
    else:
        query = query.filter(Expense.status.in_(["submitted", "with_manager", "with_finance"]))

    expenses = query.order_by(Expense.submitted_at).all()
    result = []
    for e in expenses:
        out = ExpenseOut.model_validate(e, from_attributes=True)
        out.employee_name = e.employee.name if e.employee else None
        result.append(out)
    return result


@router.get("/{expense_id}", response_model=ExpenseOut)
def get_expense(
    expense_id: UUID,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    exp = db.query(Expense).filter(Expense.id == expense_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")

    # RBAC
    if current_user.role == "employee" and str(exp.employee_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    if current_user.role == "manager":
        emp = db.query(Employee).filter(Employee.id == exp.employee_id).first()
        is_own = str(exp.employee_id) == str(current_user.id)
        is_approver = str(exp.approver_id) == str(current_user.id)
        if not (is_own or is_approver):
            raise HTTPException(status_code=403, detail="Access denied")

    log_action(db, current_user.id, "view_expense", "expense", expense_id)
    db.commit()
    out = ExpenseOut.model_validate(exp, from_attributes=True)
    out.employee_name = exp.employee.name if exp.employee else None
    return out


@router.post("/{expense_id}/action", response_model=ExpenseOut)
def action_expense(
    expense_id: UUID,
    payload: ExpenseActionRequest,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_min_role("manager")),
):
    """
    Manager: approve or reject.
    HR Admin: approve, reject, or mark_paid.
    All enforced server-side.
    """
    exp = db.query(Expense).filter(Expense.id == expense_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expense not found")

    valid_actions = {"approve", "reject", "mark_paid"}
    if payload.action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Invalid action. Must be one of {valid_actions}")

    if payload.action == "mark_paid" and current_user.role != "hr_admin":
        raise HTTPException(status_code=403, detail="Only HR Admin can mark expenses as paid")

    if current_user.role == "manager":
        if str(exp.approver_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="You are not the approver for this expense")

    now = datetime.now(timezone.utc)

    if payload.action == "approve":
        if current_user.role == "manager":
            exp.status = "approved"  # simplified flow: manager approval is final
        else:
            exp.status = "approved"
        exp.resolved_at = now
        exp.approver_id = current_user.id
        notify_expense_resolved(db, exp.employee_id, "approved", exp.id)

    elif payload.action == "reject":
        exp.status = "rejected"
        exp.rejection_note = payload.note
        exp.resolved_at = now
        exp.approver_id = current_user.id
        notify_expense_resolved(db, exp.employee_id, "rejected", exp.id)

    elif payload.action == "mark_paid":
        if exp.status != "approved":
            raise HTTPException(status_code=400, detail="Can only mark approved expenses as paid")
        exp.status = "paid"
        exp.payment_date = date.today()
        exp.payment_ref = payload.payment_ref
        exp.finance_admin_id = current_user.id
        notify_expense_resolved(db, exp.employee_id, "paid", exp.id)

    log_action(db, current_user.id, f"expense_{payload.action}", "expense", expense_id,
               {"employee_id": str(exp.employee_id), "amount": float(exp.amount)})
    db.commit()
    db.refresh(exp)
    out = ExpenseOut.model_validate(exp, from_attributes=True)
    out.employee_name = exp.employee.name if exp.employee else None
    return out


@router.get("/export/approved")
def export_approved_expenses(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_roles("hr_admin")),
):
    """Finance export — all approved expenses ready for payment processing."""
    expenses = (
        db.query(Expense)
        .filter(Expense.status == "approved")
        .order_by(Expense.resolved_at.desc())
        .all()
    )
    log_action(db, current_user.id, "export_expenses", "expense", None,
               {"count": len(expenses)})
    db.commit()
    return [
        {
            "id": str(e.id),
            "employee_name": e.employee.name if e.employee else None,
            "amount": float(e.amount),
            "currency": e.currency,
            "category": e.category,
            "description": e.description,
            "status": e.status,
            "submitted_at": e.submitted_at.isoformat(),
            "resolved_at": e.resolved_at.isoformat() if e.resolved_at else None,
        }
        for e in expenses
    ]


@router.get("/all/list", response_model=List[ExpenseOut])
def all_expenses(
    status_filter: Optional[str] = Query(None, alias="status"),
    employee_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_roles("hr_admin")),
):
    query = db.query(Expense)
    if status_filter:
        query = query.filter(Expense.status == status_filter)
    if employee_id:
        query = query.filter(Expense.employee_id == employee_id)
    expenses = query.order_by(Expense.submitted_at.desc()).all()
    result = []
    for e in expenses:
        out = ExpenseOut.model_validate(e, from_attributes=True)
        out.employee_name = e.employee.name if e.employee else None
        result.append(out)
    return result
