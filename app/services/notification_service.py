"""
Notification Service — creates in-app notification records on events.
"""
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.notification import Notification


def create_notification(
    db: Session,
    recipient_id: UUID,
    type: str,
    title: str,
    body: Optional[str] = None,
    link: Optional[str] = None,
):
    notif = Notification(
        recipient_id=recipient_id,
        type=type,
        title=title,
        body=body,
        link=link,
    )
    db.add(notif)
    db.flush()
    return notif


def notify_leave_applied(db: Session, approver_id: UUID, employee_name: str, leave_request_id: UUID):
    create_notification(
        db=db,
        recipient_id=approver_id,
        type="leave_request",
        title=f"{employee_name} has applied for leave",
        body="Review and approve or reject the leave request.",
        link=f"/leave/requests/{leave_request_id}",
    )


def notify_leave_resolved(db: Session, employee_id: UUID, status: str, leave_request_id: UUID):
    emoji = "✅" if status == "approved" else "❌"
    create_notification(
        db=db,
        recipient_id=employee_id,
        type="leave_resolved",
        title=f"{emoji} Your leave request has been {status}",
        body="Your leave balance has been updated.",
        link=f"/leave/requests/{leave_request_id}",
    )


def notify_onboarding_task(db: Session, owner_id: UUID, task_title: str, employee_name: str, task_id: UUID):
    create_notification(
        db=db,
        recipient_id=owner_id,
        type="onboarding_task",
        title=f"Onboarding task assigned: {task_title}",
        body=f"Complete this task for new hire {employee_name}.",
        link=f"/onboarding/tasks/{task_id}",
    )


def notify_expense_submitted(db: Session, approver_id: UUID, employee_name: str, expense_id: UUID, amount: float):
    create_notification(
        db=db,
        recipient_id=approver_id,
        type="expense_submitted",
        title=f"Expense claim from {employee_name} — ₹{amount:,.2f}",
        body="Review the claim in your approval queue.",
        link=f"/expenses/{expense_id}",
    )


def notify_expense_resolved(db: Session, employee_id: UUID, status: str, expense_id: UUID):
    emoji = "✅" if status in ("approved", "paid") else "❌"
    create_notification(
        db=db,
        recipient_id=employee_id,
        type="expense_resolved",
        title=f"{emoji} Expense claim {status}",
        body="View the updated status in your expense history.",
        link=f"/expenses/{expense_id}",
    )


def notify_document_uploaded(db: Session, employee_id: UUID, doc_title: str, doc_id: UUID):
    create_notification(
        db=db,
        recipient_id=employee_id,
        type="document_available",
        title=f"New document available: {doc_title}",
        body="Check your document vault.",
        link=f"/documents/{doc_id}",
    )


def notify_policy_updated(db: Session, employee_id: UUID, policy_title: str, doc_id: UUID):
    create_notification(
        db=db,
        recipient_id=employee_id,
        type="policy_updated",
        title=f"Policy updated: {policy_title}",
        body="Review the changes and acknowledge.",
        link=f"/documents/{doc_id}",
    )
