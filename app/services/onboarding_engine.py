"""
Onboarding Engine — event-driven onboarding workflow instantiation.
Called automatically when a new employee record is created.
"""
from datetime import date, timedelta
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.onboarding import OnboardingTemplate, OnboardingRun, OnboardingTask
from app.services.notification_service import notify_onboarding_task


DEFAULT_STEPS = [
    {
        "index": 0,
        "title": "IT Setup — Laptop & Accounts",
        "description": "Provision laptop, email account, and access to core tools.",
        "owner_role": "hr_admin",
        "depends_on": [],
        "deadline_days": 1,
    },
    {
        "index": 1,
        "title": "Documentation — Offer Letter & NDA",
        "description": "Collect signed offer letter and NDA from new hire.",
        "owner_role": "hr_admin",
        "depends_on": [],
        "deadline_days": 1,
    },
    {
        "index": 2,
        "title": "Team Introduction",
        "description": "Schedule intro calls with team members and key stakeholders.",
        "owner_role": "manager",
        "depends_on": [0],
        "deadline_days": 3,
    },
    {
        "index": 3,
        "title": "Policy Acknowledgement",
        "description": "Employee reads and acknowledges company policies.",
        "owner_role": "employee",
        "depends_on": [1],
        "deadline_days": 3,
    },
    {
        "index": 4,
        "title": "Role-Specific Onboarding",
        "description": "Department-specific tools, processes, and initial projects.",
        "owner_role": "manager",
        "depends_on": [2],
        "deadline_days": 7,
    },
    {
        "index": 5,
        "title": "30-Day Check-in",
        "description": "HR/Manager 1:1 to assess onboarding experience and address gaps.",
        "owner_role": "hr_admin",
        "depends_on": [3, 4],
        "deadline_days": 30,
    },
]


def get_or_create_default_template(db: Session, created_by_id: UUID) -> OnboardingTemplate:
    """Returns the default active template, creating one if absent."""
    template = (
        db.query(OnboardingTemplate)
        .filter(OnboardingTemplate.is_active == True, OnboardingTemplate.name == "Default Onboarding")
        .first()
    )
    if not template:
        template = OnboardingTemplate(
            name="Default Onboarding",
            role_target=None,   # applies to all roles
            employment_type="full_time",
            steps=DEFAULT_STEPS,
            is_active=True,
            created_by=created_by_id,
        )
        db.add(template)
        db.flush()
    return template


def find_owner_for_role(db: Session, role: str, department_id: Optional[UUID]) -> Optional[Employee]:
    """Find an HR admin or manager to assign tasks to."""
    query = db.query(Employee).filter(
        Employee.role == role,
        Employee.employment_status == "active",
    )
    if department_id and role == "manager":
        query = query.filter(Employee.department_id == department_id)
    return query.first()


def instantiate_onboarding(db: Session, employee: Employee, created_by_id: Optional[UUID] = None):
    """
    Event-driven: called when a new employee record is created.
    Creates an OnboardingRun + OnboardingTask records automatically.
    """
    # Avoid duplicate runs
    existing = (
        db.query(OnboardingRun)
        .filter(OnboardingRun.employee_id == employee.id)
        .first()
    )
    if existing:
        return existing

    # Find the best matching template — prefer role-specific, then generic
    template = (
        db.query(OnboardingTemplate)
        .filter(
            OnboardingTemplate.is_active == True,
        )
        .filter(
            (OnboardingTemplate.role_target == employee.role) | (OnboardingTemplate.role_target == None)
        )
        .order_by(OnboardingTemplate.created_at)
        .first()
    )
    if not template:
        template = get_or_create_default_template(db, created_by_id or employee.id)

    # Calculate due date (30 days from join)
    join = employee.join_date or date.today()
    due = join + timedelta(days=30)

    run = OnboardingRun(
        employee_id=employee.id,
        template_id=template.id,
        status="in_progress",
        due_date=due,
    )
    db.add(run)
    db.flush()

    # Create tasks from template steps
    steps = template.steps or DEFAULT_STEPS
    tasks_created = []
    for step in steps:
        # Determine the task owner
        owner_role = step.get("owner_role", "hr_admin")
        owner = None
        if owner_role == "employee":
            owner = employee
        elif owner_role == "manager":
            owner = employee.manager or find_owner_for_role(db, "manager", employee.department_id)
        else:
            owner = find_owner_for_role(db, "hr_admin", None)

        deadline_days = step.get("deadline_days")
        due_date = (join + timedelta(days=deadline_days)) if deadline_days else None

        # Determine initial status based on dependencies
        depends_on = step.get("depends_on", [])
        initial_status = "pending" if depends_on else "in_progress"

        task = OnboardingTask(
            run_id=run.id,
            step_index=step["index"],
            title=step["title"],
            description=step.get("description"),
            owner_id=owner.id if owner else None,
            owner_role=owner_role,
            depends_on=depends_on or [],
            deadline_days=deadline_days,
            status=initial_status,
            due_date=due_date,
        )
        db.add(task)
        tasks_created.append((task, owner))

    db.flush()

    # Send notifications to task owners
    for task, owner in tasks_created:
        if owner and task.status == "in_progress" and owner.id != employee.id:
            notify_onboarding_task(
                db=db,
                owner_id=owner.id,
                task_title=task.title,
                employee_name=employee.name,
                task_id=task.id,
            )

    return run


def check_and_unlock_tasks(db: Session, run: OnboardingRun, completed_step_index: int):
    """
    After a task is completed, check if any blocked tasks can now be unlocked.
    Called within the same transaction as task completion.
    """
    all_tasks = run.tasks
    completed_indices = {t.step_index for t in all_tasks if t.status == "completed"}
    completed_indices.add(completed_step_index)

    for task in all_tasks:
        if task.status == "pending" and task.depends_on:
            if all(dep in completed_indices for dep in task.depends_on):
                task.status = "in_progress"
                # Notify the owner that their task is now unlocked
                if task.owner_id:
                    notify_onboarding_task(
                        db=db,
                        owner_id=task.owner_id,
                        task_title=task.title,
                        employee_name=run.employee.name,
                        task_id=task.id,
                    )

    db.flush()

    # Check if all tasks are done → mark run complete
    if all(t.status in ("completed", "skipped") for t in all_tasks):
        from datetime import datetime
        run.status = "completed"
        run.completed_at = datetime.utcnow()
        db.flush()
