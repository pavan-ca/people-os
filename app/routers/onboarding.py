"""
Onboarding Router — templates, runs, and task management.
"""
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.employee import Employee
from app.models.onboarding import OnboardingTemplate, OnboardingRun, OnboardingTask
from app.schemas.onboarding import (
    OnboardingTemplateCreate, OnboardingTemplateOut,
    OnboardingRunOut, OnboardingTaskOut, TaskCompleteRequest
)
from app.auth.dependencies import get_current_user, require_roles, require_min_role
from app.services.onboarding_engine import instantiate_onboarding, check_and_unlock_tasks
from app.services.audit_service import log_action

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


# ── Templates (HR Admin) ──────────────────────────────────────────────────────

@router.get("/templates", response_model=List[OnboardingTemplateOut])
def list_templates(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_roles("hr_admin")),
):
    return db.query(OnboardingTemplate).filter(OnboardingTemplate.is_active == True).all()


@router.post("/templates", response_model=OnboardingTemplateOut, status_code=201)
def create_template(
    payload: OnboardingTemplateCreate,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_roles("hr_admin")),
):
    steps_data = [s.model_dump() for s in payload.steps]
    template = OnboardingTemplate(
        name=payload.name,
        role_target=payload.role_target,
        department_id=payload.department_id,
        employment_type=payload.employment_type,
        steps=steps_data,
        created_by=current_user.id,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.delete("/templates/{template_id}", status_code=204)
def deactivate_template(
    template_id: UUID,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_roles("hr_admin")),
):
    t = db.query(OnboardingTemplate).filter(OnboardingTemplate.id == template_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    t.is_active = False
    db.commit()


# ── Runs ──────────────────────────────────────────────────────────────────────

def _run_to_schema(run: OnboardingRun) -> OnboardingRunOut:
    tasks = [OnboardingTaskOut.model_validate(t, from_attributes=True) for t in run.tasks]
    total = len(tasks)
    done = sum(1 for t in tasks if t.status in ("completed", "skipped"))
    progress = round((done / total * 100), 1) if total > 0 else 0.0

    return OnboardingRunOut(
        id=run.id,
        employee_id=run.employee_id,
        template_id=run.template_id,
        started_at=run.started_at,
        completed_at=run.completed_at,
        status=run.status,
        due_date=run.due_date,
        tasks=tasks,
        employee_name=run.employee.name if run.employee else None,
        template_name=run.template.name if run.template else None,
        progress_pct=progress,
    )


@router.get("/runs/mine", response_model=List[OnboardingRunOut])
def my_onboarding(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """New hire views their own onboarding checklist."""
    runs = (
        db.query(OnboardingRun)
        .filter(OnboardingRun.employee_id == current_user.id)
        .all()
    )
    return [_run_to_schema(r) for r in runs]


@router.get("/runs/all", response_model=List[OnboardingRunOut])
def all_runs(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_roles("hr_admin")),
):
    """HR Admin pipeline view — all active onboarding runs."""
    query = db.query(OnboardingRun)
    if status_filter:
        query = query.filter(OnboardingRun.status == status_filter)
    else:
        query = query.filter(OnboardingRun.status == "in_progress")
    runs = query.order_by(OnboardingRun.started_at.desc()).all()
    return [_run_to_schema(r) for r in runs]


@router.get("/runs/team", response_model=List[OnboardingRunOut])
def team_runs(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_min_role("manager")),
):
    """Manager sees onboarding runs for their direct reports."""
    direct_report_ids = [
        e.id for e in db.query(Employee).filter(Employee.manager_id == current_user.id).all()
    ]
    runs = (
        db.query(OnboardingRun)
        .filter(OnboardingRun.employee_id.in_(direct_report_ids))
        .all()
    )
    return [_run_to_schema(r) for r in runs]


@router.get("/runs/{run_id}", response_model=OnboardingRunOut)
def get_run(
    run_id: UUID,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    run = db.query(OnboardingRun).filter(OnboardingRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Onboarding run not found")

    # RBAC
    if current_user.role == "employee" and str(run.employee_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    if current_user.role == "manager":
        emp = db.query(Employee).filter(Employee.id == run.employee_id).first()
        if emp and str(emp.manager_id) != str(current_user.id) and str(run.employee_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")

    return _run_to_schema(run)


@router.post("/runs/{employee_id}/trigger", response_model=OnboardingRunOut, status_code=201)
def trigger_onboarding(
    employee_id: UUID,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_roles("hr_admin")),
):
    """Manually trigger onboarding for an employee (HR Admin only)."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    run = instantiate_onboarding(db, employee, current_user.id)
    log_action(db, current_user.id, "trigger_onboarding", "onboarding_run", run.id)
    db.commit()
    db.refresh(run)
    return _run_to_schema(run)


# ── Tasks ─────────────────────────────────────────────────────────────────────

@router.get("/tasks/mine", response_model=List[OnboardingTaskOut])
def my_assigned_tasks(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Tasks assigned to the current user across all onboarding runs."""
    tasks = (
        db.query(OnboardingTask)
        .filter(
            OnboardingTask.owner_id == current_user.id,
            OnboardingTask.status.in_(["pending", "in_progress"]),
        )
        .all()
    )
    return [OnboardingTaskOut.model_validate(t, from_attributes=True) for t in tasks]


@router.post("/tasks/{task_id}/complete", response_model=OnboardingTaskOut)
def complete_task(
    task_id: UUID,
    payload: TaskCompleteRequest,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Mark a task as complete. Owner or HR Admin can complete."""
    task = db.query(OnboardingTask).filter(OnboardingTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # RBAC: only the assigned owner or HR admin can complete
    if current_user.role != "hr_admin" and str(task.owner_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="You are not the owner of this task")

    if task.status == "completed":
        raise HTTPException(status_code=400, detail="Task already completed")

    task.status = "completed"
    task.completed_at = datetime.now(timezone.utc)
    task.notes = payload.notes
    db.flush()

    # Unlock dependent tasks
    run = db.query(OnboardingRun).filter(OnboardingRun.id == task.run_id).first()
    if run:
        check_and_unlock_tasks(db, run, task.step_index)

    log_action(db, current_user.id, "complete_onboarding_task", "onboarding_task", task_id)
    db.commit()
    db.refresh(task)
    return OnboardingTaskOut.model_validate(task, from_attributes=True)
