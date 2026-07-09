from __future__ import annotations
from datetime import date, datetime
from typing import Optional, List, Any, Dict
from uuid import UUID
from pydantic import BaseModel


class OnboardingStepSchema(BaseModel):
    index: int
    title: str
    description: Optional[str] = None
    owner_role: str = "hr_admin"
    depends_on: List[int] = []
    deadline_days: Optional[int] = None


class OnboardingTemplateCreate(BaseModel):
    name: str
    role_target: Optional[str] = None
    department_id: Optional[UUID] = None
    employment_type: str = "full_time"
    steps: List[OnboardingStepSchema] = []


class OnboardingTemplateOut(BaseModel):
    id: UUID
    name: str
    role_target: Optional[str] = None
    department_id: Optional[UUID] = None
    employment_type: str
    steps: List[Dict[str, Any]]
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class OnboardingTaskOut(BaseModel):
    id: UUID
    run_id: UUID
    step_index: int
    title: str
    description: Optional[str] = None
    owner_id: Optional[UUID] = None
    owner_role: Optional[str] = None
    depends_on: Optional[List[int]] = None
    deadline_days: Optional[int] = None
    status: str
    completed_at: Optional[datetime] = None
    due_date: Optional[date] = None
    notes: Optional[str] = None
    model_config = {"from_attributes": True}


class OnboardingRunOut(BaseModel):
    id: UUID
    employee_id: UUID
    template_id: UUID
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    due_date: Optional[date] = None
    tasks: List[OnboardingTaskOut] = []
    employee_name: Optional[str] = None
    template_name: Optional[str] = None
    progress_pct: Optional[float] = None
    model_config = {"from_attributes": True}


class TaskCompleteRequest(BaseModel):
    notes: Optional[str] = None
