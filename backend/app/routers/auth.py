from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.employee import Employee
from app.schemas.auth import LoginRequest, TokenResponse
from app.auth.jwt import verify_password, create_access_token
from app.auth.dependencies import get_current_user
from app.schemas.employee import EmployeeProfileOut

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.email == payload.email).first()
    if not employee or not verify_password(payload.password, employee.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if employee.employment_status == "terminated":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is no longer active",
        )
    token = create_access_token({"sub": str(employee.id), "role": employee.role})
    return TokenResponse(
        access_token=token,
        role=employee.role,
        employee_id=str(employee.id),
        name=employee.name,
    )


@router.get("/me", response_model=EmployeeProfileOut)
def get_me(current_user: Employee = Depends(get_current_user)):
    """Returns the authenticated user's own profile."""
    return current_user
