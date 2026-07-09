"""
Dashboard Router — role-aware contextual dashboard data.
Returns a completely different payload per role.
"""
from datetime import date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.employee import Employee
from app.models.leave import LeaveBalance, LeaveRequest
from app.models.onboarding import OnboardingRun, OnboardingTask
from app.models.expense import Expense
from app.models.notification import Notification
from app.models.document import Document, DocumentAcknowledgement
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _leave_balance_summary(db: Session, employee_id) -> List[dict]:
    year = date.today().year
    balances = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == employee_id,
        LeaveBalance.year == year,
    ).all()
    return [
        {
            "leave_type": b.leave_type,
            "total_days": float(b.total_days),
            "used_days": float(b.used_days),
            "pending_days": float(b.pending_days),
            "available_days": b.available_days,
        }
        for b in balances
    ]


def _upcoming_leaves(db: Session, employee_id) -> List[dict]:
    today = date.today()
    leaves = (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.status == "approved",
            LeaveRequest.start_date >= today,
        )
        .order_by(LeaveRequest.start_date)
        .limit(3)
        .all()
    )
    return [
        {
            "id": str(l.id),
            "leave_type": l.leave_type,
            "start_date": l.start_date.isoformat(),
            "end_date": l.end_date.isoformat(),
            "total_days": float(l.total_days),
        }
        for l in leaves
    ]


def _pending_expense_count(db: Session, employee_id) -> dict:
    submitted = db.query(Expense).filter(
        Expense.employee_id == employee_id,
        Expense.status.in_(["submitted", "with_manager", "with_finance"]),
    ).count()
    return {"count": submitted}


@router.get("")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    today = date.today()
    role = current_user.role
    unread_notifs = db.query(Notification).filter(
        Notification.recipient_id == current_user.id,
        Notification.read == False,
    ).count()

    base = {
        "employee_id": str(current_user.id),
        "name": current_user.name,
        "role": role,
        "job_title": current_user.job_title,
        "department": current_user.department.name if current_user.department else None,
        "join_date": current_user.join_date.isoformat() if current_user.join_date else None,
        "unread_notifications": unread_notifs,
        "today": today.isoformat(),
    }

    # ── Employee view ────────────────────────────────────────────────────────
    if role == "employee":
        # Check if this is a new hire (within 30 days)
        is_new_hire = current_user.join_date and (today - current_user.join_date).days <= 30

        onboarding_data = None
        if is_new_hire:
            run = (
                db.query(OnboardingRun)
                .filter(
                    OnboardingRun.employee_id == current_user.id,
                    OnboardingRun.status == "in_progress",
                )
                .first()
            )
            if run:
                tasks = run.tasks
                total = len(tasks)
                done = sum(1 for t in tasks if t.status in ("completed", "skipped"))
                in_progress = [t for t in tasks if t.status == "in_progress"]
                next_task = in_progress[0] if in_progress else None
                onboarding_data = {
                    "run_id": str(run.id),
                    "progress_pct": round((done / total * 100), 1) if total else 0,
                    "total_tasks": total,
                    "completed_tasks": done,
                    "due_date": run.due_date.isoformat() if run.due_date else None,
                    "next_task": {
                        "id": str(next_task.id),
                        "title": next_task.title,
                        "step_index": next_task.step_index,
                    } if next_task else None,
                }

        # Policy docs pending acknowledgement
        unacked_policies = (
            db.query(Document)
            .filter(
                Document.is_company_wide == True,
                Document.requires_ack == True,
                ~Document.id.in_(
                    db.query(DocumentAcknowledgement.document_id)
                    .filter(DocumentAcknowledgement.employee_id == current_user.id)
                )
            )
            .count()
        )

        return {
            **base,
            "view": "new_hire" if is_new_hire else "employee",
            "is_new_hire": is_new_hire,
            "onboarding": onboarding_data,
            "leave_balances": _leave_balance_summary(db, current_user.id),
            "upcoming_leaves": _upcoming_leaves(db, current_user.id),
            "pending_expenses": _pending_expense_count(db, current_user.id),
            "unacknowledged_policies": unacked_policies,
        }

    # ── Manager view ─────────────────────────────────────────────────────────
    elif role == "manager":
        # Pending leave approvals
        pending_leaves = db.query(LeaveRequest).filter(
            LeaveRequest.approver_id == current_user.id,
            LeaveRequest.status == "pending",
        ).count()

        # Pending expense approvals
        pending_expenses = db.query(Expense).filter(
            Expense.approver_id == current_user.id,
            Expense.status.in_(["submitted", "with_manager"]),
        ).count()

        # Team availability this week
        week_start = today
        week_end = today + timedelta(days=6)
        team_on_leave = (
            db.query(LeaveRequest)
            .join(Employee, LeaveRequest.employee_id == Employee.id)
            .filter(
                Employee.manager_id == current_user.id,
                LeaveRequest.status == "approved",
                LeaveRequest.start_date <= week_end,
                LeaveRequest.end_date >= week_start,
            )
            .all()
        )

        # Direct report count
        direct_reports = db.query(Employee).filter(
            Employee.manager_id == current_user.id,
            Employee.employment_status == "active",
        ).count()

        # Delayed onboarding in team
        delayed_onboarding = (
            db.query(OnboardingRun)
            .join(Employee, OnboardingRun.employee_id == Employee.id)
            .filter(
                Employee.manager_id == current_user.id,
                OnboardingRun.status == "in_progress",
                OnboardingRun.due_date < today,
            )
            .count()
        )

        return {
            **base,
            "view": "manager",
            "pending_leave_approvals": pending_leaves,
            "pending_expense_approvals": pending_expenses,
            "direct_reports_count": direct_reports,
            "team_on_leave_this_week": [
                {
                    "employee_id": str(l.employee_id),
                    "employee_name": l.employee.name if l.employee else None,
                    "start_date": l.start_date.isoformat(),
                    "end_date": l.end_date.isoformat(),
                    "leave_type": l.leave_type,
                }
                for l in team_on_leave
            ],
            "delayed_onboarding_count": delayed_onboarding,
            "my_leave_balances": _leave_balance_summary(db, current_user.id),
            "my_upcoming_leaves": _upcoming_leaves(db, current_user.id),
        }

    # ── HR Admin view ─────────────────────────────────────────────────────────
    else:  # hr_admin
        # Active onboarding runs
        active_runs = db.query(OnboardingRun).filter(OnboardingRun.status == "in_progress").count()
        delayed_runs = db.query(OnboardingRun).filter(
            OnboardingRun.status == "in_progress",
            OnboardingRun.due_date < today,
        ).count()

        # Pending leave requests across org
        pending_leaves = db.query(LeaveRequest).filter(LeaveRequest.status == "pending").count()

        # Pending expenses across org
        pending_expenses = db.query(Expense).filter(
            Expense.status.in_(["submitted", "with_manager", "with_finance"])
        ).count()

        # Employees active
        total_employees = db.query(Employee).filter(Employee.employment_status == "active").count()
        new_hires_30d = db.query(Employee).filter(
            Employee.employment_status == "active",
            Employee.join_date >= today - timedelta(days=30),
        ).count()

        # Pending policy acknowledgements
        docs_requiring_ack = db.query(Document).filter(
            Document.is_company_wide == True,
            Document.requires_ack == True,
        ).count()

        # Recent hires needing onboarding attention
        recent_hires = (
            db.query(Employee)
            .filter(
                Employee.employment_status == "active",
                Employee.join_date >= today - timedelta(days=30),
            )
            .order_by(Employee.join_date.desc())
            .limit(5)
            .all()
        )

        return {
            **base,
            "view": "hr_admin",
            "total_active_employees": total_employees,
            "new_hires_last_30_days": new_hires_30d,
            "active_onboarding_runs": active_runs,
            "delayed_onboarding_runs": delayed_runs,
            "pending_leave_requests": pending_leaves,
            "pending_expense_claims": pending_expenses,
            "policies_requiring_acknowledgement": docs_requiring_ack,
            "recent_hires": [
                {
                    "id": str(e.id),
                    "name": e.name,
                    "job_title": e.job_title,
                    "department": e.department.name if e.department else None,
                    "join_date": e.join_date.isoformat() if e.join_date else None,
                }
                for e in recent_hires
            ],
        }
