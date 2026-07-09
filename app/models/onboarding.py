import uuid
from sqlalchemy import (
    Column, String, Date, DateTime, ForeignKey,
    Text, Boolean, Integer, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class OnboardingTemplate(Base):
    __tablename__ = "onboarding_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    role_target = Column(String(20))
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    employment_type = Column(String(30), default="full_time")
    steps = Column(JSONB, nullable=False, default=list)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    runs = relationship("OnboardingRun", back_populates="template")
    creator = relationship("Employee", foreign_keys=[created_by])


class OnboardingRun(Base):
    __tablename__ = "onboarding_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("onboarding_templates.id", ondelete="RESTRICT"), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    status = Column(String(20), nullable=False, default="in_progress")
    due_date = Column(Date)

    employee = relationship("Employee", back_populates="onboarding_runs")
    template = relationship("OnboardingTemplate", back_populates="runs")
    tasks = relationship("OnboardingTask", back_populates="run", cascade="all, delete-orphan", order_by="OnboardingTask.step_index")


class OnboardingTask(Base):
    __tablename__ = "onboarding_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("onboarding_runs.id", ondelete="CASCADE"), nullable=False)
    step_index = Column(Integer, nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    owner_role = Column(String(20))
    depends_on = Column(ARRAY(Integer), default=list)
    deadline_days = Column(Integer)
    status = Column(String(20), nullable=False, default="pending")
    completed_at = Column(DateTime(timezone=True))
    due_date = Column(Date)
    notes = Column(Text)

    run = relationship("OnboardingRun", back_populates="tasks")
    owner = relationship("Employee", foreign_keys=[owner_id])
