from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: UUID
    owner_id: Optional[UUID] = None
    doc_type: str
    title: str
    description: Optional[str] = None
    version: int
    storage_url: str
    file_name: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    uploaded_by: UUID
    visible_to_roles: List[str]
    is_company_wide: bool
    requires_ack: bool
    changelog: Optional[str] = None
    created_at: datetime
    acknowledged: Optional[bool] = None   # set per-request
    model_config = {"from_attributes": True}


class DocumentAckOut(BaseModel):
    document_id: UUID
    employee_id: UUID
    acknowledged_at: datetime
    model_config = {"from_attributes": True}
