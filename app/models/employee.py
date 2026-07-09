import uuid
from datetime import date, datetime
from sqlalchemy import (
    Column, String, Date, DateTime, ForeignKey, Text, Boolean
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(Text, nullable=False)
    role = Column(String(20), nullable=False)          # employee | manager | hr_admin
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    manager_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    job_title = Column(String(150))
    phone = Column(String(30))
    avatar_url = Column(Text)
    join_date = Column(Date, nullable=False, default=date.today)
    employment_status = Column(String(30), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    department = relationship("Department", back_populates="employees", foreign_keys=[department_id])
    manager = relationship("Employee", remote_side="Employee.id", foreign_keys=[manager_id], backref="direct_reports")

    leave_balances = relationship("LeaveBalance", back_populates="employee", cascade="all, delete-orphan")
    leave_requests = relationship("LeaveRequest", back_populates="employee", foreign_keys="LeaveRequest.employee_id")
    onboarding_runs = relationship("OnboardingRun", back_populates="employee", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="owner", foreign_keys="Document.owner_id")
    expenses = relationship("Expense", back_populates="employee", foreign_keys="Expense.employee_id")
    notifications = relationship("Notification", back_populates="recipient", cascade="all, delete-orphan")
