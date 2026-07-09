import uuid
from sqlalchemy import (
    Column, String, DateTime, ForeignKey,
    Text, Boolean, Integer, BigInteger, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=True)
    doc_type = Column(String(50), nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    version = Column(Integer, nullable=False, default=1)
    storage_url = Column(Text, nullable=False)
    file_name = Column(Text, nullable=False)
    file_size = Column(BigInteger)
    mime_type = Column(String(100))
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False)
    visible_to_roles = Column(ARRAY(String), nullable=False, default=lambda: ["employee", "manager", "hr_admin"])
    is_company_wide = Column(Boolean, nullable=False, default=False)
    requires_ack = Column(Boolean, nullable=False, default=False)
    changelog = Column(Text)
    parent_doc_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("Employee", back_populates="documents", foreign_keys=[owner_id])
    uploader = relationship("Employee", foreign_keys=[uploaded_by])
    acknowledgements = relationship("DocumentAcknowledgement", back_populates="document", cascade="all, delete-orphan")
    previous_version = relationship("Document", remote_side="Document.id", foreign_keys=[parent_doc_id])


class DocumentAcknowledgement(Base):
    __tablename__ = "document_acknowledgements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    employee_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("Document", back_populates="acknowledgements")
    employee = relationship("Employee")
