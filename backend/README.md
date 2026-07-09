# PeopleOS Backend

Smart HR Self-Service Portal — FastAPI + PostgreSQL Backend

## Setup

### Prerequisites
- Python 3.11+
- PostgreSQL running locally (port 5432)
- Database `peopleos` created

### Create the Database
```sql
psql -U postgres -c "CREATE DATABASE peopleos;"
```

### Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Environment Variables
Copy `.env` file (already pre-configured):
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=peopleos
DB_USER=postgres
DB_PASSWORD=root
SECRET_KEY=super-secret-key-change-in-production-32chars!!
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
```

### Initialize Schema & Seed Data
```bash
python seed.py
```

### Run the Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Test Credentials

| Role | Email | Password |
|------|-------|----------|
| HR Admin | priya.sharma@peopleos.io | Admin@123 |
| Manager | rahul.gupta@peopleos.io | Manager@123 |
| Manager | ananya.iyer@peopleos.io | Manager@123 |
| Employee | arjun.mehta@peopleos.io | Emp@12345 |
| Employee | kavya.nair@peopleos.io | Emp@12345 |
| New Hire | divya.krishnan@peopleos.io | NewHire@123 |

---

## RBAC Test Cases (Judge Verification)

1. **Employee → Manager endpoint** — `POST /api/v1/leave/requests/{id}/action` as employee → **403**
2. **Employee → Another employee's payslip** — `GET /api/v1/documents/{id}` → **403**
3. **Manager → HR Admin analytics** — `GET /api/v1/audit/logs` as manager → **403**
4. **New hire onboarding auto-trigger** — Create employee via `POST /api/v1/employees` → check `GET /api/v1/onboarding/runs/mine`

---

## API Endpoints Summary

### Authentication
- `POST /api/v1/auth/login` — Login, get JWT
- `GET /api/v1/auth/me` — Get current user

### Employees
- `GET /api/v1/employees` — List (manager+)
- `POST /api/v1/employees` — Create + trigger onboarding (hr_admin)
- `GET /api/v1/employees/{id}` — Profile (RBAC enforced)
- `PATCH /api/v1/employees/{id}` — Update
- `DELETE /api/v1/employees/{id}` — Deactivate (hr_admin)

### Dashboard
- `GET /api/v1/dashboard` — Role-aware contextual dashboard

### Leave
- `GET /api/v1/leave/balances` — My leave balances
- `POST /api/v1/leave/apply` — Apply leave
- `GET /api/v1/leave/requests/mine` — My leave history
- `GET /api/v1/leave/requests/pending/queue` — Approval queue (manager+)
- `POST /api/v1/leave/requests/{id}/action` — Approve/reject (manager+)
- `GET /api/v1/leave/team/calendar` — Team calendar
- `GET /api/v1/leave/requests/all/list` — All requests (hr_admin)

### Onboarding
- `GET /api/v1/onboarding/templates` — Templates (hr_admin)
- `POST /api/v1/onboarding/templates` — Create template (hr_admin)
- `GET /api/v1/onboarding/runs/mine` — My onboarding checklist
- `GET /api/v1/onboarding/runs/all` — Pipeline view (hr_admin)
- `GET /api/v1/onboarding/runs/team` — Team runs (manager+)
- `POST /api/v1/onboarding/tasks/{id}/complete` — Complete task

### Documents
- `GET /api/v1/documents/vault` — Personal document vault
- `GET /api/v1/documents/company` — Company documents
- `POST /api/v1/documents/upload` — Upload document (manager+)
- `POST /api/v1/documents/{id}/acknowledge` — Acknowledge document
- `GET /api/v1/documents/{id}/acknowledgements` — Acknowledgement report (manager+)

### Expenses
- `POST /api/v1/expenses/submit` — Submit expense (with receipt)
- `GET /api/v1/expenses/mine` — My expenses
- `GET /api/v1/expenses/queue` — Approval queue (manager+)
- `POST /api/v1/expenses/{id}/action` — Approve/reject/mark_paid
- `GET /api/v1/expenses/export/approved` — Finance export (hr_admin)

### Notifications
- `GET /api/v1/notifications` — My notifications
- `GET /api/v1/notifications/count` — Unread count
- `PATCH /api/v1/notifications/{id}/read` — Mark read
- `PATCH /api/v1/notifications/read-all` — Mark all read

### Audit
- `GET /api/v1/audit/logs` — Full audit trail (hr_admin)

---

## Architecture

```
FastAPI (Python)
  ├── app/main.py          — Entry point, CORS, router mounting
  ├── app/config.py        — Pydantic settings
  ├── app/database.py      — SQLAlchemy engine + session
  ├── app/models/          — ORM models (SQLAlchemy)
  ├── app/schemas/         — Pydantic request/response schemas
  ├── app/routers/         — Route handlers (RBAC enforced)
  ├── app/auth/            — JWT + role dependencies
  └── app/services/        — Business logic + event engine
```
