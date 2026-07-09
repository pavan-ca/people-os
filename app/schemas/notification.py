from __future__ import annotations
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: UUID
    recipient_id: UUID
    type: str
    title: str
    body: Optional[str] = None
    link: Optional[str] = None
    read: bool
    created_at: datetime
    model_config = {"from_attributes": True}
