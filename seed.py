"""
PeopleOS - Database Seed Script
Run: python seed.py
Creates the DB schema and populates with realistic data for all roles.
"""
import sys
import os

# Fix Windows console encoding for Unicode
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, timedelta
from sqlalchemy import text
from app.database import engine, SessionLocal, Base
import app.models  # noqa - ensures all models are registered

from app.models.employee import Employee
from app.models.department import Department
from app.models.leave import LeaveBalance, LeaveRequest
from app.models.onboarding import OnboardingTemplate, OnboardingRun, OnboardingTask
from app.models.document import Document
from app.models.expense import Expense
from app.models.notification import Notification
from app.models.audit import AuditLog
from app.auth.jwt import hash_password
from app.services.leave_service import ensure_leave_balances, LEAVE_TYPE_DEFAULTS
from app.services.onboarding_engine import instantiate_onboarding, DEFAULT_STEPS

print(">>> PeopleOS Seed Script Starting...")


def create_tables():
    print("📦 Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created.")


def seed(db):
    # ── Departments ────────────────────────────────────────────────────────
    print("🏢 Seeding departments...")
    dept_names = ["Engineering", "Product", "Design", "HR & People", "Finance", "Sales", "Marketing", "Operations"]
    departments = {}
    for name in dept_names:
        d = db.query(Department).filter(Department.name == name).first()
        if not d:
            d = Department(name=name)
            db.add(d)
            db.flush()
        departments[name] = d
    print(f"   ✅ {len(departments)} departments ready.")

    # ── HR Admin ───────────────────────────────────────────────────────────
    print("👤 Seeding HR Admin...")
    hr_admin = db.query(Employee).filter(Employee.email == "priya.sharma@peopleos.io").first()
    if not hr_admin:
        hr_admin = Employee(
            name="Priya Sharma",
            email="priya.sharma@peopleos.io",
            password_hash=hash_password("Admin@123"),
            role="hr_admin",
            department_id=departments["HR & People"].id,
            job_title="Head of People",
            phone="+91-9800000001",
            join_date=date(2022, 1, 15),
            employment_status="active",
        )
        db.add(hr_admin)
        db.flush()
        ensure_leave_balances(db, hr_admin)

    # Update dept head
    departments["HR & People"].head_employee_id = hr_admin.id
    db.flush()

    # ── Engineering Manager ────────────────────────────────────────────────
    print("👤 Seeding Engineering Manager...")
    eng_manager = db.query(Employee).filter(Employee.email == "rahul.gupta@peopleos.io").first()
    if not eng_manager:
        eng_manager = Employee(
            name="Rahul Gupta",
            email="rahul.gupta@peopleos.io",
            password_hash=hash_password("Manager@123"),
            role="manager",
            department_id=departments["Engineering"].id,
            job_title="Engineering Manager",
            phone="+91-9800000002",
            join_date=date(2022, 6, 1),
            employment_status="active",
        )
        db.add(eng_manager)
        db.flush()
        ensure_leave_balances(db, eng_manager)
    departments["Engineering"].head_employee_id = eng_manager.id

    # ── Product Manager ────────────────────────────────────────────────────
    product_manager = db.query(Employee).filter(Employee.email == "ananya.iyer@peopleos.io").first()
    if not product_manager:
        product_manager = Employee(
            name="Ananya Iyer",
            email="ananya.iyer@peopleos.io",
            password_hash=hash_password("Manager@123"),
            role="manager",
            department_id=departments["Product"].id,
            job_title="Product Lead",
            phone="+91-9800000003",
            join_date=date(2023, 2, 1),
            employment_status="active",
        )
        db.add(product_manager)
        db.flush()
        ensure_leave_balances(db, product_manager)
    departments["Product"].head_employee_id = product_manager.id
    db.flush()

    # ── Engineers ──────────────────────────────────────────────────────────
    print("👥 Seeding employees...")
    employees_data = [
        {
            "name": "Arjun Mehta",
            "email": "arjun.mehta@peopleos.io",
            "password": "Emp@12345",
            "role": "employee",
            "dept": "Engineering",
            "manager_id": eng_manager.id,
            "job_title": "Senior Software Engineer",
            "join_date": date(2023, 8, 1),
        },
        {
            "name": "Kavya Nair",
            "email": "kavya.nair@peopleos.io",
            "password": "Emp@12345",
            "role": "employee",
            "dept": "Engineering",
            "manager_id": eng_manager.id,
            "job_title": "Software Engineer",
            "join_date": date(2024, 1, 15),
        },
        {
            "name": "Siddharth Rao",
            "email": "siddharth.rao@peopleos.io",
            "password": "Emp@12345",
            "role": "employee",
            "dept": "Product",
            "manager_id": product_manager.id,
            "job_title": "Product Manager",
            "join_date": date(2023, 11, 1),
        },
        {
            "name": "Meera Pillai",
            "email": "meera.pillai@peopleos.io",
            "password": "Emp@12345",
            "role": "employee",
            "dept": "Design",
            "manager_id": product_manager.id,
            "job_title": "UX Designer",
            "join_date": date(2024, 3, 1),
        },
        {
            "name": "Vikram Singh",
            "email": "vikram.singh@peopleos.io",
            "password": "Emp@12345",
            "role": "employee",
            "dept": "Finance",
            "manager_id": hr_admin.id,
            "job_title": "Finance Analyst",
            "join_date": date(2023, 7, 15),
        },
    ]

    created_employees = []
    for data in employees_data:
        emp = db.query(Employee).filter(Employee.email == data["email"]).first()
        if not emp:
            emp = Employee(
                name=data["name"],
                email=data["email"],
                password_hash=hash_password(data["password"]),
                role=data["role"],
                department_id=departments[data["dept"]].id,
                manager_id=data["manager_id"],
                job_title=data["job_title"],
                join_date=data["join_date"],
                employment_status="active",
            )
            db.add(emp)
            db.flush()
            ensure_leave_balances(db, emp)
        created_employees.append(emp)

    # ── New Hire (within last 30 days — triggers onboarding view) ──────────
    print("🆕 Seeding new hire...")
    new_hire = db.query(Employee).filter(Employee.email == "divya.krishnan@peopleos.io").first()
    if not new_hire:
        new_hire = Employee(
            name="Divya Krishnan",
            email="divya.krishnan@peopleos.io",
            password_hash=hash_password("NewHire@123"),
            role="employee",
            department_id=departments["Engineering"].id,
            manager_id=eng_manager.id,
            job_title="Junior Software Engineer",
            join_date=date.today() - timedelta(days=3),  # 3 days ago
            employment_status="active",
        )
        db.add(new_hire)
        db.flush()
        ensure_leave_balances(db, new_hire)

    db.commit()
    print("   ✅ All employees created.")

    # ── Onboarding Template ────────────────────────────────────────────────
    print("📋 Seeding onboarding template...")
    template = db.query(OnboardingTemplate).filter(OnboardingTemplate.name == "Default Onboarding").first()
    if not template:
        template = OnboardingTemplate(
            name="Default Onboarding",
            role_target=None,
            employment_type="full_time",
            steps=DEFAULT_STEPS,
            is_active=True,
            created_by=hr_admin.id,
        )
        db.add(template)
        db.flush()
        db.commit()

    # ── Trigger onboarding for new hire ────────────────────────────────────
    print("🔄 Triggering onboarding for new hire...")
    existing_run = db.query(OnboardingRun).filter(OnboardingRun.employee_id == new_hire.id).first()
    if not existing_run:
        run = instantiate_onboarding(db, new_hire, hr_admin.id)
        db.commit()
        print(f"   ✅ Onboarding run created: {run.id}")

    # ── Leave Requests ─────────────────────────────────────────────────────
    print("🏖️  Seeding leave requests...")
    arjun = db.query(Employee).filter(Employee.email == "arjun.mehta@peopleos.io").first()
    kavya = db.query(Employee).filter(Employee.email == "kavya.nair@peopleos.io").first()
    sidharth = db.query(Employee).filter(Employee.email == "siddharth.rao@peopleos.io").first()

    # Approved leave in the past
    if arjun and not db.query(LeaveRequest).filter(LeaveRequest.employee_id == arjun.id).first():
        approved_leave = LeaveRequest(
            employee_id=arjun.id,
            leave_type="casual",
            start_date=date.today() - timedelta(days=10),
            end_date=date.today() - timedelta(days=8),
            total_days=3,
            status="approved",
            approver_id=eng_manager.id,
            reason="Family event",
            resolved_at=date.today() - timedelta(days=11),
        )
        db.add(approved_leave)
        # Update balance
        bal = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == arjun.id,
            LeaveBalance.leave_type == "casual",
            LeaveBalance.year == date.today().year,
        ).first()
        if bal:
            bal.used_days = float(bal.used_days) + 3

        # Upcoming approved leave
        upcoming_leave = LeaveRequest(
            employee_id=arjun.id,
            leave_type="earned",
            start_date=date.today() + timedelta(days=5),
            end_date=date.today() + timedelta(days=9),
            total_days=5,
            status="approved",
            approver_id=eng_manager.id,
            reason="Vacation",
            resolved_at=date.today() - timedelta(days=2),
        )
        db.add(upcoming_leave)
        bal2 = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == arjun.id,
            LeaveBalance.leave_type == "earned",
            LeaveBalance.year == date.today().year,
        ).first()
        if bal2:
            bal2.used_days = float(bal2.used_days) + 5

    # Pending leave for Kavya (manager needs to approve)
    if kavya and not db.query(LeaveRequest).filter(LeaveRequest.employee_id == kavya.id).first():
        pending_leave = LeaveRequest(
            employee_id=kavya.id,
            leave_type="casual",
            start_date=date.today() + timedelta(days=2),
            end_date=date.today() + timedelta(days=3),
            total_days=2,
            status="pending",
            approver_id=eng_manager.id,
            reason="Personal work",
        )
        db.add(pending_leave)
        db.flush()
        # pending_days
        bal = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == kavya.id,
            LeaveBalance.leave_type == "casual",
            LeaveBalance.year == date.today().year,
        ).first()
        if bal:
            bal.pending_days = float(bal.pending_days) + 2

        # Notify manager
        from app.services.notification_service import notify_leave_applied
        notify_leave_applied(db, eng_manager.id, kavya.name, pending_leave.id)

    db.commit()
    print("   ✅ Leave requests seeded.")

    # ── Expenses ───────────────────────────────────────────────────────────
    print("💰 Seeding expenses...")
    if arjun and not db.query(Expense).filter(Expense.employee_id == arjun.id).first():
        # Approved expense
        exp1 = Expense(
            employee_id=arjun.id,
            amount=2500.00,
            currency="INR",
            category="travel",
            description="Cab to client office for project meeting",
            status="approved",
            approver_id=eng_manager.id,
            resolved_at=date.today() - timedelta(days=5),
        )
        db.add(exp1)

        # Pending expense
        exp2 = Expense(
            employee_id=arjun.id,
            amount=850.00,
            currency="INR",
            category="meals",
            description="Team lunch during sprint planning",
            status="submitted",
            approver_id=eng_manager.id,
        )
        db.add(exp2)
        db.flush()

        from app.services.notification_service import notify_expense_submitted
        notify_expense_submitted(db, eng_manager.id, arjun.name, exp2.id, 850.00)

    if kavya and not db.query(Expense).filter(Expense.employee_id == kavya.id).first():
        exp3 = Expense(
            employee_id=kavya.id,
            amount=15000.00,
            currency="INR",
            category="equipment",
            description="Mechanical keyboard for WFH setup",
            status="submitted",
            approver_id=eng_manager.id,
        )
        db.add(exp3)
        db.flush()
        from app.services.notification_service import notify_expense_submitted
        notify_expense_submitted(db, eng_manager.id, kavya.name, exp3.id, 15000.00)

    db.commit()
    print("   ✅ Expenses seeded.")

    # ── Company Documents ──────────────────────────────────────────────────
    print("📄 Seeding company documents...")
    docs_to_create = [
        {
            "title": "Employee Handbook 2026",
            "doc_type": "handbook",
            "description": "Complete guide to PeopleOS policies, culture, and processes.",
            "requires_ack": True,
            "changelog": "Updated leave policy section for 2026",
            "visible_to_roles": ["employee", "manager", "hr_admin"],
        },
        {
            "title": "Leave Policy v3.1",
            "doc_type": "policy",
            "description": "Comprehensive leave entitlements, accrual rules, and carry-forward guidelines.",
            "requires_ack": True,
            "changelog": "Added paternity leave update — 15 days effective July 2026",
            "visible_to_roles": ["employee", "manager", "hr_admin"],
        },
        {
            "title": "Remote Work Policy",
            "doc_type": "policy",
            "description": "Guidelines for remote and hybrid work arrangements.",
            "requires_ack": False,
            "visible_to_roles": ["employee", "manager", "hr_admin"],
        },
        {
            "title": "Expense Reimbursement Policy",
            "doc_type": "policy",
            "description": "Eligible categories, limits, approval chains, and timelines for expense claims.",
            "requires_ack": False,
            "visible_to_roles": ["employee", "manager", "hr_admin"],
        },
        {
            "title": "Code of Conduct",
            "doc_type": "compliance",
            "description": "PeopleOS code of ethics and professional conduct standards.",
            "requires_ack": True,
            "visible_to_roles": ["employee", "manager", "hr_admin"],
        },
    ]

    for doc_data in docs_to_create:
        existing = db.query(Document).filter(Document.title == doc_data["title"]).first()
        if not existing:
            doc = Document(
                owner_id=None,
                doc_type=doc_data["doc_type"],
                title=doc_data["title"],
                description=doc_data["description"],
                storage_url=f"/uploads/documents/sample_{doc_data['doc_type']}.pdf",
                file_name=f"{doc_data['title'].replace(' ', '_')}.pdf",
                file_size=1024 * 100,  # 100KB dummy
                mime_type="application/pdf",
                uploaded_by=hr_admin.id,
                visible_to_roles=doc_data["visible_to_roles"],
                is_company_wide=True,
                requires_ack=doc_data["requires_ack"],
                changelog=doc_data.get("changelog"),
            )
            db.add(doc)

    db.commit()
    print("   ✅ Company documents seeded.")

    # ── Payslips for Arjun ─────────────────────────────────────────────────
    print("📑 Seeding payslips...")
    if arjun:
        for month in range(1, 7):  # Jan–Jun 2026
            title = f"Payslip — {date(2026, month, 1).strftime('%B %Y')}"
            existing = db.query(Document).filter(
                Document.title == title,
                Document.owner_id == arjun.id
            ).first()
            if not existing:
                ps = Document(
                    owner_id=arjun.id,
                    doc_type="payslip",
                    title=title,
                    description=f"Monthly payslip for {date(2026, month, 1).strftime('%B %Y')}",
                    storage_url=f"/uploads/documents/payslip_arjun_{month}_2026.pdf",
                    file_name=f"payslip_{month}_2026.pdf",
                    file_size=1024 * 50,
                    mime_type="application/pdf",
                    uploaded_by=hr_admin.id,
                    visible_to_roles=["employee", "manager", "hr_admin"],
                    is_company_wide=False,
                    requires_ack=False,
                )
                db.add(ps)

    db.commit()
    print("   ✅ Payslips seeded.")

    # ── Notifications ──────────────────────────────────────────────────────
    print("🔔 Creating additional notifications...")
    if new_hire:
        from app.models.notification import Notification as Notif
        existing = db.query(Notif).filter(Notif.recipient_id == new_hire.id).first()
        if not existing:
            n1 = Notif(
                recipient_id=new_hire.id,
                type="welcome",
                title="👋 Welcome to PeopleOS, Divya!",
                body="Your onboarding checklist is ready. Start with IT Setup.",
                link="/onboarding",
                read=False,
            )
            n2 = Notif(
                recipient_id=new_hire.id,
                type="document_available",
                title="Employee Handbook is ready for you",
                body="Please read and acknowledge the employee handbook.",
                link="/documents/company",
                read=False,
            )
            db.add(n1)
            db.add(n2)

    db.commit()
    print("   ✅ Notifications seeded.")

    print("\n" + "="*60)
    print("✅ PeopleOS seed complete!")
    print("="*60)
    print("\n📋 Test Credentials:")
    print("  HR Admin:  priya.sharma@peopleos.io   / Admin@123")
    print("  Manager:   rahul.gupta@peopleos.io    / Manager@123")
    print("  Manager:   ananya.iyer@peopleos.io    / Manager@123")
    print("  Employee:  arjun.mehta@peopleos.io    / Emp@12345")
    print("  Employee:  kavya.nair@peopleos.io     / Emp@12345")
    print("  New Hire:  divya.krishnan@peopleos.io / NewHire@123")
    print("\n🌐 API Docs: http://localhost:8000/docs")
    print("="*60)


if __name__ == "__main__":
    create_tables()
    db = SessionLocal()
    try:
        seed(db)
    except Exception as e:
        db.rollback()
        print(f"❌ Seed failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()
