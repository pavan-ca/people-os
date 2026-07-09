"""
Leave Service — business logic for leave type detection, balance management,
and transactional approval.
"""
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from app.models.leave import LeaveBalance, LeaveRequest
from app.models.employee import Employee


LEAVE_TYPE_DEFAULTS = {
    "casual": 12.0,
    "earned": 15.0,
    "sick": 7.0,
    "annual": 0.0,
    "maternity": 90.0,
    "paternity": 15.0,
    "unpaid": 0.0,
}


def auto_detect_leave_type(start_date: date, end_date: date, total_days: float) -> str:
    """
    Simple heuristic: 
    - <= 2 days → casual
    - 3-5 days  → earned
    - > 5 days  → annual
    """
    if total_days <= 2:
        return "casual"
    elif total_days <= 5:
        return "earned"
    else:
        return "annual"


def count_working_days(start: date, end: date) -> float:
    """Count weekdays (Mon–Fri) between start and end (inclusive)."""
    from datetime import timedelta
    total = 0
    current = start
    while current <= end:
        if current.weekday() < 5:  # Mon=0 … Fri=4
            total += 1
        current += timedelta(days=1)
    return float(total)


def get_balance(db: Session, employee_id, leave_type: str, year: int) -> Optional[LeaveBalance]:
    return (
        db.query(LeaveBalance)
        .filter(
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.leave_type == leave_type,
            LeaveBalance.year == year,
        )
        .first()
    )


def ensure_leave_balances(db: Session, employee: Employee):
    """Create default leave balances for a new employee."""
    year = date.today().year
    for leave_type, total in LEAVE_TYPE_DEFAULTS.items():
        existing = get_balance(db, employee.id, leave_type, year)
        if not existing:
            bal = LeaveBalance(
                employee_id=employee.id,
                leave_type=leave_type,
                total_days=total,
                used_days=0,
                pending_days=0,
                carry_forward=0,
                year=year,
            )
            db.add(bal)
    db.flush()


def reserve_leave(db: Session, leave_request: LeaveRequest):
    """Move days from available → pending on submit."""
    year = leave_request.start_date.year
    bal = get_balance(db, leave_request.employee_id, leave_request.leave_type, year)
    if not bal:
        raise ValueError(f"No balance found for {leave_request.leave_type}")
    available = float(bal.total_days) + float(bal.carry_forward) - float(bal.used_days) - float(bal.pending_days)
    if available < float(leave_request.total_days) and leave_request.leave_type != "unpaid":
        raise ValueError(f"Insufficient leave balance. Available: {available}, Requested: {leave_request.total_days}")
    bal.pending_days = float(bal.pending_days) + float(leave_request.total_days)
    db.flush()


def approve_leave(db: Session, leave_request: LeaveRequest):
    """Move days from pending → used on approval."""
    year = leave_request.start_date.year
    bal = get_balance(db, leave_request.employee_id, leave_request.leave_type, year)
    if bal:
        bal.pending_days = max(0.0, float(bal.pending_days) - float(leave_request.total_days))
        bal.used_days = float(bal.used_days) + float(leave_request.total_days)
        db.flush()


def reject_leave(db: Session, leave_request: LeaveRequest):
    """Release pending days back to available on rejection."""
    year = leave_request.start_date.year
    bal = get_balance(db, leave_request.employee_id, leave_request.leave_type, year)
    if bal:
        bal.pending_days = max(0.0, float(bal.pending_days) - float(leave_request.total_days))
        db.flush()
