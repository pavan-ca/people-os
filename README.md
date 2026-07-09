# PeopleOS — The Employee Experience Platform

**PeopleOS** is a next-generation HR self-service portal designed to put the employee first. By shifting workflows away from complex menus and configurations, PeopleOS offers context-aware, event-driven, and lightning-fast experiences for new hires, employees, managers, and HR administrators alike.

---

## 🚀 Key Features

*   **Boxless Showcase Split Login**: A gorgeous, minimal split-screen login page with custom, modern typography floating over animated space-mesh gradients.
*   **Onboarding Pipeline & Tasks**:
    *   **New Hire Checklist**: A vertical interactive milestone checklist that guides new hires step-by-step.
    *   **Management Pipeline View**: A comprehensive dashboard for HR admins and managers to monitor active onboarding runs, expand employee status cards, and mark action tasks complete to unlock next steps.
*   **Context-Aware Leave Management**:
    *   **Interactive Team Calendar**: An overlap calendar that lets employees and managers view who else is out this month.
    *   **Click-to-Apply**: Tap directly on any calendar day to automatically pre-populate the leave dates in the apply form.
    *   **Auto-Toggling Approvals**: Open the Leave page as a Manager or HR admin and instantly view the **Team Queue** approval panel by default.
*   **Expense Reimbursements**:
    *   Sleek file uploading for receipts.
    *   Auto-default tabs that focus on **Team Queue** for managers/admins to verify and approve expense claims.
    *   Clickable dashboard indicators that redirect instantly to active workflows.
*   **Audit Logging**: Every action (viewing, updating, or resolving requests) is monitored and tracked in the backend database.

---

## 🛠️ Technology Stack

*   **Backend**: Python, FastAPI, SQLAlchemy ORM, SQLite database.
*   **Frontend**: React, TypeScript, Vite, Vanilla CSS (rich custom glassmorphic design system).

---

## 📂 Project Directory Structure

```text
hackathon/
├── backend/
│   ├── app/
│   │   ├── auth/          # Authentication dependencies (min role checks)
│   │   ├── models/        # Database models (Employee, Leave, Expense, Onboarding)
│   │   ├── routers/       # API endpoints (Leave, Expense, Onboarding, Dashboard)
│   │   ├── schemas/       # Pydantic schemas for data serialization
│   │   ├── services/      # Business logic (Notification system, Onboarding engine)
│   │   ├── main.py        # FastAPI entrypoint
│   │   └── database.py    # Session and database configuration
│   ├── seed.py            # Database seeder script
│   └── requirements.txt   # Backend dependencies
├── frontend/
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── contexts/      # React contexts (Authentication)
│   │   ├── hooks/         # Custom React hooks (useApi)
│   │   ├── pages/         # Page components (Dashboard, Leave, Expenses, Onboarding, Login)
│   │   ├── App.tsx        # Routing setup
│   │   ├── index.css      # Core styles & variables
│   │   └── main.tsx       # Vite entrypoint
│   └── package.json       # Frontend dependencies
└── README.md              # Project documentation
```

---

## ⚙️ Installation & Setup

### 1. Backend Setup
Navigate to the `backend` folder:
```bash
cd backend
```

Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate
```

Install backend dependencies:
```bash
pip install -r requirements.txt
```

Seed the database (runs migrations and provisions default employees, balances, and onboarding pipelines):
```bash
python seed.py
```

Start the FastAPI local development server:
```bash
uvicorn app.main:app --reload
```
The API documentation will be available at `http://localhost:8000/docs`.

### 2. Frontend Setup
Open a new terminal session and navigate to the `frontend` folder:
```bash
cd frontend
```

Install dependencies:
```bash
npm install
```

Start the Vite hot-reloading development server:
```bash
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 🔑 Demo & Test Credentials

The database comes pre-seeded with the following roles to test the workflows:

| Name | Role | Email | Password |
| :--- | :--- | :--- | :--- |
| **Priya Sharma** | HR Admin | `priya.sharma@peopleos.io` | `Admin@123` |
| **Rahul Gupta** | Eng Manager | `rahul.gupta@peopleos.io` | `Manager@123` |
| **Divya Krishnan** | New Hire | `divya.krishnan@peopleos.io` | `NewHire@123` |
| **Arjun Mehta** | Employee | `arjun.mehta@peopleos.io` | `Employee@123` |
