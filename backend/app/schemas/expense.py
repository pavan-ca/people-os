from __future__ import annotations
from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class ExpenseCreate(BaseModel):
    amount: float
    currency: str = "INR"
    category: str
    description: str


class ExpenseActionRequest(BaseModel):
    action: str     # "approve" | "reject" | "mark_paid"
    note: Optional[str] = None
    payment_ref: Optional[str] = None


class ExpenseOut(BaseModel):
    id: UUID
    employee_id: UUID
    amount: float
    currency: str
    category: str
    description: str
    receipt_url: Optional[str] = None
    receipt_filename: Optional[str] = None
    status: str
    approver_id: Optional[UUID] = None
    finance_admin_id: Optional[UUID] = None
    submitted_at: datetime
    resolved_at: Optional[datetime] = None
    rejection_note: Optional[str] = None
    payment_date: Optional[date] = None
    payment_ref: Optional[str] = None
    employee_name: Optional[str] = None
    model_config = {"from_attributes": True}
