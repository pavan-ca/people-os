"""
Audit Service — logs every permission-sensitive action to audit_logs table.
"""
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.audit import AuditLog


def log_action(
    db: Session,
    actor_id: Optional[UUID],
    action: str,
    resource_type: str,
    resource_id: Optional[UUID] = None,
    metadata: Optional[dict] = None,
    ip_address: Optional[str] = None,
):
    entry = AuditLog(
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        meta=metadata or {},
        ip_address=ip_address,
    )
    db.add(entry)
    db.flush()   # flush so it's part of current transaction
