"""
Documents Router — personal vault, company docs, versioning, acknowledgements.
"""
import os
import uuid
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.employee import Employee
from app.models.document import Document, DocumentAcknowledgement
from app.schemas.document import DocumentOut, DocumentAckOut
from app.auth.dependencies import get_current_user, require_roles, require_min_role
from app.services.notification_service import notify_document_uploaded, notify_policy_updated
from app.services.audit_service import log_action

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = "uploads/documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _check_doc_access(doc: Document, current_user: Employee):
    """Enforces document-level RBAC. Raises 403 if access denied."""
    # Company-wide: check role visibility
    if doc.is_company_wide:
        if current_user.role not in (doc.visible_to_roles or []):
            raise HTTPException(status_code=403, detail="Access denied to this document")
        return

    # Personal doc: must be the owner, their manager, or HR admin
    if current_user.role == "hr_admin":
        return
    if str(doc.owner_id) == str(current_user.id):
        return
    if current_user.role == "manager":
        owner = doc.owner
        if owner and str(owner.manager_id) == str(current_user.id):
            return
    raise HTTPException(status_code=403, detail="Access denied to this document")


@router.get("/vault", response_model=List[DocumentOut])
def my_document_vault(
    doc_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Employee's personal document vault."""
    query = db.query(Document).filter(
        Document.owner_id == current_user.id,
        Document.is_company_wide == False,
    )
    if doc_type:
        query = query.filter(Document.doc_type == doc_type)
    docs = query.order_by(Document.created_at.desc()).all()

    result = []
    for doc in docs:
        out = DocumentOut.model_validate(doc, from_attributes=True)
        # Check if employee has acknowledged
        ack = db.query(DocumentAcknowledgement).filter(
            DocumentAcknowledgement.document_id == doc.id,
            DocumentAcknowledgement.employee_id == current_user.id,
        ).first()
        out.acknowledged = ack is not None
        result.append(out)
    return result


@router.get("/company", response_model=List[DocumentOut])
def company_documents(
    doc_type: Optional[str] = Query(None),
    q: Optional[str] = Query(None, description="Full-text search"),
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    """Company-wide documents accessible to the user's role."""
    query = db.query(Document).filter(
        Document.is_company_wide == True,
        Document.visible_to_roles.any(current_user.role),
    )
    if doc_type:
        query = query.filter(Document.doc_type == doc_type)
    if q:
        query = query.filter(Document.title.ilike(f"%{q}%"))
    docs = query.order_by(Document.created_at.desc()).all()


    result = []
    for doc in docs:
        out = DocumentOut.model_validate(doc, from_attributes=True)
        ack = db.query(DocumentAcknowledgement).filter(
            DocumentAcknowledgement.document_id == doc.id,
            DocumentAcknowledgement.employee_id == current_user.id,
        ).first()
        out.acknowledged = ack is not None
        result.append(out)
    return result


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    _check_doc_access(doc, current_user)
    log_action(db, current_user.id, "view_document", "document", document_id)
    db.commit()

    out = DocumentOut.model_validate(doc, from_attributes=True)
    ack = db.query(DocumentAcknowledgement).filter(
        DocumentAcknowledgement.document_id == doc.id,
        DocumentAcknowledgement.employee_id == current_user.id,
    ).first()
    out.acknowledged = ack is not None
    return out


@router.post("/upload", response_model=DocumentOut, status_code=201)
async def upload_document(
    title: str = Form(...),
    doc_type: str = Form(...),
    description: Optional[str] = Form(None),
    owner_id: Optional[UUID] = Form(None),
    is_company_wide: bool = Form(False),
    requires_ack: bool = Form(False),
    visible_to_roles: str = Form("employee,manager,hr_admin"),
    changelog: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_min_role("manager")),
):
    """Upload a document. Managers+ for team docs; HR Admin for company-wide."""
    if is_company_wide and current_user.role != "hr_admin":
        raise HTTPException(status_code=403, detail="Only HR Admin can upload company-wide documents")

    # Save file locally
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_name = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    roles = [r.strip() for r in visible_to_roles.split(",")]

    doc = Document(
        owner_id=owner_id,
        doc_type=doc_type,
        title=title,
        description=description,
        storage_url=f"/{file_path}",
        file_name=file.filename or unique_name,
        file_size=len(content),
        mime_type=file.content_type,
        uploaded_by=current_user.id,
        visible_to_roles=roles,
        is_company_wide=is_company_wide,
        requires_ack=requires_ack,
        changelog=changelog,
    )
    db.add(doc)
    db.flush()

    # Notify affected employees
    if is_company_wide:
        affected = db.query(Employee).filter(
            Employee.role.in_(roles),
            Employee.employment_status == "active",
        ).all()
        for emp in affected:
            if doc_type in ("policy", "handbook", "compliance"):
                notify_policy_updated(db, emp.id, title, doc.id)
            else:
                notify_document_uploaded(db, emp.id, title, doc.id)
    elif owner_id:
        notify_document_uploaded(db, owner_id, title, doc.id)

    log_action(db, current_user.id, "upload_document", "document", doc.id,
               {"title": title, "doc_type": doc_type, "is_company_wide": is_company_wide})
    db.commit()
    db.refresh(doc)
    return DocumentOut.model_validate(doc, from_attributes=True)


@router.post("/{document_id}/acknowledge", response_model=DocumentAckOut)
def acknowledge_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    _check_doc_access(doc, current_user)

    existing = db.query(DocumentAcknowledgement).filter(
        DocumentAcknowledgement.document_id == document_id,
        DocumentAcknowledgement.employee_id == current_user.id,
    ).first()
    if existing:
        return DocumentAckOut.model_validate(existing, from_attributes=True)

    ack = DocumentAcknowledgement(document_id=document_id, employee_id=current_user.id)
    db.add(ack)
    log_action(db, current_user.id, "acknowledge_document", "document", document_id)
    db.commit()
    db.refresh(ack)
    return DocumentAckOut.model_validate(ack, from_attributes=True)


@router.get("/{document_id}/acknowledgements")
def get_acknowledgements(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_min_role("manager")),
):
    """HR Admin/Manager: view who has acknowledged a document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    acks = db.query(DocumentAcknowledgement).filter(
        DocumentAcknowledgement.document_id == document_id
    ).all()
    return [
        {
            "employee_id": str(a.employee_id),
            "employee_name": a.employee.name if a.employee else None,
            "acknowledged_at": a.acknowledged_at.isoformat(),
        }
        for a in acks
    ]


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(require_roles("hr_admin")),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    log_action(db, current_user.id, "delete_document", "document", document_id)
    db.commit()
