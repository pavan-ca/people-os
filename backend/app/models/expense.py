import uuid
from sqlalchemy import (
    Column, String, Date, DateTime, ForeignKey,
    Text, Numeric
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(5), nullable=False, default="INR")
    category = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    receipt_url = Column(Text)
    receipt_filename = Column(Text)
    status = Column(String(20), nullable=False, default="submitted")
    approver_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    finance_admin_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    rejection_note = Column(Text)
    payment_date = Column(Date)
    payment_ref = Column(String(100))

    employee = relationship("Employee", back_populates="expenses", foreign_keys=[employee_id])
    approver = relationship("Employee", foreign_keys=[approver_id])
    finance_admin = relationship("Employee", foreign_keys=[finance_admin_id])
