import uuid
from sqlalchemy import (
    Column, String, Date, DateTime, ForeignKey,
    Text, Numeric, Integer, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    leave_type = Column(String(50), nullable=False)
    total_days = Column(Numeric(5, 1), nullable=False, default=0)
    used_days = Column(Numeric(5, 1), nullable=False, default=0)
    pending_days = Column(Numeric(5, 1), nullable=False, default=0)
    carry_forward = Column(Numeric(5, 1), nullable=False, default=0)
    year = Column(Integer, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    employee = relationship("Employee", back_populates="leave_balances")

    @property
    def available_days(self):
        return float(self.total_days) + float(self.carry_forward) - float(self.used_days) - float(self.pending_days)


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    leave_type = Column(String(50), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    total_days = Column(Numeric(5, 1), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    approver_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    reason = Column(Text)
    note = Column(Text)
    applied_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))

    employee = relationship("Employee", back_populates="leave_requests", foreign_keys=[employee_id])
    approver = relationship("Employee", foreign_keys=[approver_id])
