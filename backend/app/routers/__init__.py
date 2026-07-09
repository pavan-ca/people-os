from app.routers.auth import router as auth_router
from app.routers.employees import router as employees_router, dept_router as departments_router
from app.routers.dashboard import router as dashboard_router
from app.routers.leave import router as leave_router
from app.routers.onboarding import router as onboarding_router
from app.routers.documents import router as documents_router
from app.routers.expenses import router as expenses_router
from app.routers.notifications import router as notifications_router
from app.routers.audit import router as audit_router

__all__ = [
    "auth_router",
    "employees_router",
    "departments_router",
    "dashboard_router",
    "leave_router",
    "onboarding_router",
    "documents_router",
    "expenses_router",
    "notifications_router",
    "audit_router",
]
