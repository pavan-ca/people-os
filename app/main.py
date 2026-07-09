"""
PeopleOS — FastAPI Backend Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.database import engine, Base
from app.routers import (
    auth_router,
    employees_router,
    departments_router,
    dashboard_router,
    leave_router,
    onboarding_router,
    documents_router,
    expenses_router,
    notifications_router,
    audit_router,
)

# ── Import all models so SQLAlchemy sees them before create_all ──────────────
import app.models  # noqa: F401

app = FastAPI(
    title="PeopleOS API",
    description="Smart HR Self-Service Platform — Role-aware, Event-driven",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static file serving for uploads ──────────────────────────────────────────
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router,          prefix="/api/v1")
app.include_router(employees_router,     prefix="/api/v1")
app.include_router(departments_router,   prefix="/api/v1")
app.include_router(dashboard_router,     prefix="/api/v1")
app.include_router(leave_router,         prefix="/api/v1")
app.include_router(onboarding_router,    prefix="/api/v1")
app.include_router(documents_router,     prefix="/api/v1")
app.include_router(expenses_router,      prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(audit_router,         prefix="/api/v1")


@app.on_event("startup")
def startup():
    """Create all tables on startup if they don't exist."""
    Base.metadata.create_all(bind=engine)
    os.makedirs("uploads/documents", exist_ok=True)
    os.makedirs("uploads/receipts", exist_ok=True)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": "PeopleOS API", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
