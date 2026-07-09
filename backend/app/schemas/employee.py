from __future__ import annotations
from datetime import date, datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr


class DepartmentOut(BaseModel):
    id: UUID
    name: str
    model_config = {"from_attributes": True}


class EmployeeCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "employee"
    department_id: Optional[UUID] = None
    manager_id: Optional[UUID] = None
    job_title: Optional[str] = None
    phone: Optional[str] = None
    join_date: Optional[date] = None
    employment_status: str = "active"


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    department_id: Optional[UUID] = None
    manager_id: Optional[UUID] = None
    job_title: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    join_date: Optional[date] = None
    employment_status: Optional[str] = None


class EmployeeOut(BaseModel):
    id: UUID
    name: str
    email: str
    role: str
    department_id: Optional[UUID] = None
    manager_id: Optional[UUID] = None
    job_title: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    join_date: Optional[date] = None
    employment_status: str
    created_at: Optional[datetime] = None
    department: Optional[DepartmentOut] = None
    model_config = {"from_attributes": True}


class EmployeeProfileOut(EmployeeOut):
    """Extended profile — includes manager info."""
    manager: Optional[EmployeeOut] = None
    model_config = {"from_attributes": True}
