from __future__ import annotations
from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class LeaveBalanceOut(BaseModel):
    id: UUID
    employee_id: UUID
    leave_type: str
    total_days: float
    used_days: float
    pending_days: float
    carry_forward: float
    available_days: float
    year: int
    model_config = {"from_attributes": True}

    @classmethod
    def from_orm(cls, obj):
        data = {
            "id": obj.id,
            "employee_id": obj.employee_id,
            "leave_type": obj.leave_type,
            "total_days": float(obj.total_days),
            "used_days": float(obj.used_days),
            "pending_days": float(obj.pending_days),
            "carry_forward": float(obj.carry_forward),
            "available_days": obj.available_days,
            "year": obj.year,
        }
        return cls(**data)


class LeaveApplyRequest(BaseModel):
    start_date: date
    end_date: date
    leave_type: Optional[str] = None   # auto-detected if omitted
    reason: Optional[str] = None


class LeaveActionRequest(BaseModel):
    action: str                        # "approve" | "reject"
    note: Optional[str] = None


class LeaveRequestOut(BaseModel):
    id: UUID
    employee_id: UUID
    leave_type: str
    start_date: date
    end_date: date
    total_days: float
    status: str
    approver_id: Optional[UUID] = None
    reason: Optional[str] = None
    note: Optional[str] = None
    applied_at: datetime
    resolved_at: Optional[datetime] = None
    employee_name: Optional[str] = None
    model_config = {"from_attributes": True}
