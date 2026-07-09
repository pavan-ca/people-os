from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.employee import Employee
from app.models.department import Department
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeOut, EmployeeProfileOut
from app.auth.dependencies import get_current_user, require_roles, require_min_role
from app.auth.jwt import hash_password
from app.services.leave_service import ensure_leave_balances
from app.services.onboarding_engine import instantiate_onboarding
from app.services.audit_service import log_action

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("", response_model=List[EmployeeOut])
def list_employees(
    role: Optional[str] = Query(None),
    department_id: Optional[UUID] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    q: Optional[str] = Query(None, description="Search by name"),
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_min_role("manager")),
):
    """List employees. Managers and HR admins only."""
    query = db.query(Employee)
    if role:
        query = query.filter(Employee.role == role)
    if department_id:
        query = query.filter(Employee.department_id == department_id)
    if status_filter:
        query = query.filter(Employee.employment_status == status_filter)
    if q:
        query = query.filter(Employee.name.ilike(f"%{q}%"))
    return query.order_by(Employee.name).all()


@router.get("/me/profile", response_model=EmployeeProfileOut)
def my_profile(current_user: Employee = Depends(get_current_user)):
    return current_user


@router.get("/{employee_id}", response_model=EmployeeProfileOut)
def get_employee(
    employee_id: UUID,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """
    Employees can only view their own profile.
    Managers can view their direct reports.
    HR admins can view anyone.
    """
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    # RBAC enforcement
    if current_user.role == "employee" and str(current_user.id) != str(employee_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if current_user.role == "manager":
        is_direct_report = str(emp.manager_id) == str(current_user.id)
        is_self = str(current_user.id) == str(employee_id)
        if not (is_direct_report or is_self):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    log_action(db, current_user.id, "view_employee", "employee", employee_id)
    db.commit()
    return emp


@router.post("", response_model=EmployeeProfileOut, status_code=201)
def create_employee(
    payload: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_roles("hr_admin")),
):
    """Create new employee. HR Admin only. Triggers onboarding automatically."""
    # Check email uniqueness
    if db.query(Employee).filter(Employee.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    employee = Employee(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        department_id=payload.department_id,
        manager_id=payload.manager_id,
        job_title=payload.job_title,
        phone=payload.phone,
        join_date=payload.join_date,
        employment_status=payload.employment_status,
    )
    db.add(employee)
    db.flush()

    # Event-driven: Create leave balances
    ensure_leave_balances(db, employee)

    # Event-driven: Instantiate onboarding workflow
    instantiate_onboarding(db, employee, created_by_id=current_user.id)

    log_action(db, current_user.id, "create_employee", "employee", employee.id,
               {"email": employee.email, "role": employee.role})
    db.commit()
    db.refresh(employee)
    return employee


@router.patch("/{employee_id}", response_model=EmployeeOut)
def update_employee(
    employee_id: UUID,
    payload: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Employees can update their own limited fields. HR admins can update anything."""
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    # RBAC: only HR admin can change role, status, manager_id
    if current_user.role != "hr_admin":
        if str(current_user.id) != str(employee_id):
            raise HTTPException(status_code=403, detail="Access denied")
        # Employees can only update their own phone/avatar
        allowed_fields = {"phone", "avatar_url"}
        for field, value in payload.model_dump(exclude_unset=True).items():
            if field not in allowed_fields:
                raise HTTPException(status_code=403, detail=f"Cannot update field: {field}")

    update_data = payload.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["password_hash"] = hash_password(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(emp, field, value)

    log_action(db, current_user.id, "update_employee", "employee", employee_id, update_data)
    db.commit()
    db.refresh(emp)
    return emp


@router.delete("/{employee_id}", status_code=204)
def deactivate_employee(
    employee_id: UUID,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_roles("hr_admin")),
):
    """Soft-delete: sets employment_status to terminated. HR Admin only."""
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    emp.employment_status = "terminated"
    log_action(db, current_user.id, "terminate_employee", "employee", employee_id)
    db.commit()


# ── Departments ─────────────────────────────────────────────────────────────

dept_router = APIRouter(prefix="/departments", tags=["Departments"])


@dept_router.get("", response_model=List[dict])
def list_departments(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    depts = db.query(Department).order_by(Department.name).all()
    return [{"id": str(d.id), "name": d.name} for d in depts]


@dept_router.post("", status_code=201)
def create_department(
    name: str,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_roles("hr_admin")),
):
    dept = Department(name=name)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return {"id": str(dept.id), "name": dept.name}
