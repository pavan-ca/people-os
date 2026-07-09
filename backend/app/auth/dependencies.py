from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session
from app.auth.jwt import decode_token
from app.database import get_db
from app.models.employee import Employee

bearer_scheme = HTTPBearer()

ROLE_HIERARCHY = {
    "employee": 0,
    "manager": 1,
    "hr_admin": 2,
}


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Employee:
    """Validates JWT and returns the current employee. Raises 401 on failure."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials)
        employee_id: str = payload.get("sub")
        if employee_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if employee is None or employee.employment_status == "terminated":
        raise credentials_exception
    return employee


def require_roles(*allowed_roles: str):
    """
    FastAPI dependency factory — enforces role access server-side.
    Raises 403 if the current user's role is not in allowed_roles.
    """
    def _check(current_user: Employee = Depends(get_current_user)) -> Employee:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {list(allowed_roles)}",
            )
        return current_user
    return _check


def require_min_role(min_role: str):
    """
    Requires user role to be >= min_role in hierarchy.
    employee < manager < hr_admin
    """
    min_level = ROLE_HIERARCHY.get(min_role, 0)

    def _check(current_user: Employee = Depends(get_current_user)) -> Employee:
        user_level = ROLE_HIERARCHY.get(current_user.role, -1)
        if user_level < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Minimum role required: {min_role}",
            )
        return current_user
    return _check


# Convenience dependency shortcuts
def manager_or_above(current_user: Employee = Depends(require_min_role("manager"))) -> Employee:
    return current_user


def hr_admin_only(current_user: Employee = Depends(require_roles("hr_admin"))) -> Employee:
    return current_user
