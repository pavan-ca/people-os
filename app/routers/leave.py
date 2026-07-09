"""
Leave Router — apply leave, approve/reject, balances, team calendar.
All role enforcement is done server-side.
"""
from datetime import date, datetime, timezone
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.employee import Employee
from app.models.leave import LeaveBalance, LeaveRequest
from app.schemas.leave import LeaveBalanceOut, LeaveApplyRequest, LeaveActionRequest, LeaveRequestOut
from app.auth.dependencies import get_current_user, require_min_role, require_roles
from app.services.leave_service import (
    auto_detect_leave_type, count_working_days,
    reserve_leave, approve_leave, reject_leave,
)
from app.services.notification_service import notify_leave_applied, notify_leave_resolved
from app.services.audit_service import log_action

router = APIRouter(prefix="/leave", tags=["Leave"])


# ── Balances ─────────────────────────────────────────────────────────────────

@router.get("/balances", response_model=List[LeaveBalanceOut])
def my_leave_balances(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    year = date.today().year
    balances = (
        db.query(LeaveBalance)
        .filter(LeaveBalance.employee_id == current_user.id, LeaveBalance.year == year)
        .all()
    )
    return [LeaveBalanceOut.from_orm(b) for b in balances]


@router.get("/balances/{employee_id}", response_model=List[LeaveBalanceOut])
def employee_leave_balances(
    employee_id: UUID,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """View another employee's balances. Managers see their reports; HR sees all."""
    if current_user.role == "employee" and str(current_user.id) != str(employee_id):
        raise HTTPException(status_code=403, detail="Access denied")

    if current_user.role == "manager":
        emp = db.query(Employee).filter(Employee.id == employee_id).first()
        if emp and str(emp.manager_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")

    year = date.today().year
    balances = (
        db.query(LeaveBalance)
        .filter(LeaveBalance.employee_id == employee_id, LeaveBalance.year == year)
        .all()
    )
    return [LeaveBalanceOut.from_orm(b) for b in balances]


# ── Apply Leave ───────────────────────────────────────────────────────────────

@router.post("/apply", response_model=LeaveRequestOut, status_code=201)
def apply_leave(
    payload: LeaveApplyRequest,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    # Validate dates
    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=400, detail="end_date must be >= start_date")

    total_days = count_working_days(payload.start_date, payload.end_date)
    if total_days == 0:
        raise HTTPException(status_code=400, detail="No working days in selected range")

    # Auto-detect leave type if not provided
    leave_type = payload.leave_type or auto_detect_leave_type(payload.start_date, payload.end_date, total_days)

    # Check for overlapping requests
    overlap = (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.employee_id == current_user.id,
            LeaveRequest.status.in_(["pending", "approved"]),
            LeaveRequest.start_date <= payload.end_date,
            LeaveRequest.end_date >= payload.start_date,
        )
        .first()
    )
    if overlap:
        raise HTTPException(status_code=400, detail="Overlapping leave request exists")

    # Determine approver (manager or HR admin)
    approver = None
    if current_user.manager_id:
        approver = db.query(Employee).filter(Employee.id == current_user.manager_id).first()
    if not approver:
        approver = db.query(Employee).filter(Employee.role == "hr_admin").first()

    leave_req = LeaveRequest(
        employee_id=current_user.id,
        leave_type=leave_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        total_days=total_days,
        status="pending",
        approver_id=approver.id if approver else None,
        reason=payload.reason,
    )
    db.add(leave_req)
    db.flush()

    # Reserve pending days
    try:
        reserve_leave(db, leave_req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Notify approver
    if approver:
        notify_leave_applied(db, approver.id, current_user.name, leave_req.id)

    log_action(db, current_user.id, "apply_leave", "leave_request", leave_req.id,
               {"leave_type": leave_type, "days": float(total_days)})
    db.commit()
    db.refresh(leave_req)
    out = LeaveRequestOut.model_validate(leave_req, from_attributes=True)
    out.employee_name = current_user.name
    return out


# ── My Leave Requests ─────────────────────────────────────────────────────────

@router.get("/requests/mine", response_model=List[LeaveRequestOut])
def my_leave_requests(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    query = db.query(LeaveRequest).filter(LeaveRequest.employee_id == current_user.id)
    if status_filter:
        query = query.filter(LeaveRequest.status == status_filter)
    requests = query.order_by(LeaveRequest.applied_at.desc()).all()
    result = []
    for r in requests:
        out = LeaveRequestOut.model_validate(r, from_attributes=True)
        out.employee_name = current_user.name
        result.append(out)
    return result


@router.get("/requests/{request_id}", response_model=LeaveRequestOut)
def get_leave_request(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    req = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Leave request not found")

    # RBAC: employee sees only own; manager sees reports; HR sees all
    if current_user.role == "employee" and str(req.employee_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    if current_user.role == "manager":
        emp = db.query(Employee).filter(Employee.id == req.employee_id).first()
        if emp and str(emp.manager_id) != str(current_user.id) and str(req.employee_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")

    out = LeaveRequestOut.model_validate(req, from_attributes=True)
    out.employee_name = req.employee.name if req.employee else None
    return out


# ── Approval Queue (Manager + HR Admin) ──────────────────────────────────────

@router.get("/requests/pending/queue", response_model=List[LeaveRequestOut])
def pending_approvals(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_min_role("manager")),
):
    """Manager sees their team's pending leaves. HR sees all pending."""
    query = db.query(LeaveRequest).filter(LeaveRequest.status == "pending")
    if current_user.role == "manager":
        query = query.filter(LeaveRequest.approver_id == current_user.id)
    requests = query.order_by(LeaveRequest.applied_at).all()
    result = []
    for r in requests:
        out = LeaveRequestOut.model_validate(r, from_attributes=True)
        out.employee_name = r.employee.name if r.employee else None
        result.append(out)
    return result


@router.post("/requests/{request_id}/action", response_model=LeaveRequestOut)
def action_leave_request(
    request_id: UUID,
    payload: LeaveActionRequest,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_min_role("manager")),
):
    """Approve or reject a leave request. Manager/HR Admin only — enforced server-side."""
    if payload.action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="action must be 'approve' or 'reject'")

    req = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Leave request not found")
    if req.status != "pending":
        raise HTTPException(status_code=400, detail=f"Request is already {req.status}")

    # Manager can only act on their own approvals (unless HR admin)
    if current_user.role == "manager" and str(req.approver_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="You are not the approver for this request")

    req.status = payload.action + "d" if payload.action == "approve" else "rejected"
    req.status = "approved" if payload.action == "approve" else "rejected"
    req.note = payload.note
    req.resolved_at = datetime.now(timezone.utc)
    req.approver_id = current_user.id

    if payload.action == "approve":
        approve_leave(db, req)
    else:
        reject_leave(db, req)

    notify_leave_resolved(db, req.employee_id, req.status, req.id)
    log_action(db, current_user.id, f"leave_{req.status}", "leave_request", req.id,
               {"employee_id": str(req.employee_id), "action": payload.action})
    db.commit()
    db.refresh(req)
    out = LeaveRequestOut.model_validate(req, from_attributes=True)
    out.employee_name = req.employee.name if req.employee else None
    return out


@router.delete("/requests/{request_id}", status_code=204)
def cancel_leave_request(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    req = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Leave request not found")
    if str(req.employee_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    if req.status not in ("pending",):
        raise HTTPException(status_code=400, detail="Can only cancel pending requests")
    req.status = "cancelled"
    reject_leave(db, req)   # release pending balance
    db.commit()


# ── Team Calendar ─────────────────────────────────────────────────────────────

@router.get("/team/calendar")
def team_leave_calendar(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020),
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """
    Returns approved leaves for the team in the given month.
    Employees see their dept; managers see their team; HR sees all.
    """
    from datetime import date
    start = date(year, month, 1)
    import calendar as cal
    last_day = cal.monthrange(year, month)[1]
    end = date(year, month, last_day)

    query = (
        db.query(LeaveRequest)
        .join(Employee, LeaveRequest.employee_id == Employee.id)
        .filter(
            LeaveRequest.status == "approved",
            LeaveRequest.start_date <= end,
            LeaveRequest.end_date >= start,
        )
    )
    if current_user.role == "employee":
        query = query.filter(Employee.department_id == current_user.department_id)
    elif current_user.role == "manager":
        query = query.filter(Employee.manager_id == current_user.id)

    leaves = query.all()
    return [
        {
            "id": str(r.id),
            "employee_id": str(r.employee_id),
            "employee_name": r.employee.name if r.employee else None,
            "leave_type": r.leave_type,
            "start_date": r.start_date.isoformat(),
            "end_date": r.end_date.isoformat(),
            "total_days": float(r.total_days),
        }
        for r in leaves
    ]


# ── HR Admin — All Requests ───────────────────────────────────────────────────

@router.get("/requests/all/list", response_model=List[LeaveRequestOut])
def all_leave_requests(
    status_filter: Optional[str] = Query(None, alias="status"),
    employee_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_roles("hr_admin")),
):
    """HR Admin — view all leave requests."""
    query = db.query(LeaveRequest)
    if status_filter:
        query = query.filter(LeaveRequest.status == status_filter)
    if employee_id:
        query = query.filter(LeaveRequest.employee_id == employee_id)
    requests = query.order_by(LeaveRequest.applied_at.desc()).all()
    result = []
    for r in requests:
        out = LeaveRequestOut.model_validate(r, from_attributes=True)
        out.employee_name = r.employee.name if r.employee else None
        result.append(out)
    return result
