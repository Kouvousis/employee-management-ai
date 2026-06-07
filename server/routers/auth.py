import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select

from database import get_session
from models import Employee, User
from schemas.auth import TokenResponse
from security import create_access_token, decode_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    payload = decode_access_token(token)
    user_id = payload.get("sub") if payload else None

    if not isinstance(user_id, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = session.get(User, int(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    return user


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    """
    Authenticate with an employee email and password.

    Use the employee's email address in the **username** field.
    Returns a JWT bearer token to include in the `Authorization` header of subsequent requests.
    Token expires after the configured `ACCESS_TOKEN_EXPIRE_MINUTES` period.
    """
    user = session.exec(
        select(User)
        .join(Employee, User.employee_id == Employee.id)
        .where(Employee.email == form.username)
    ).first()

    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not bcrypt.checkpw(form.password.encode(), user.hashed_password.encode()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id), "access_rights": user.access_rights.value})
    return TokenResponse(access_token=token)


@router.get("/me")
def me(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """
    Return the profile of the currently authenticated user.

    Requires a valid bearer token. Returns the user's ID, access rights level,
    linked employee ID, and the employee's name (null for admin-only accounts).
    """
    employee = session.get(Employee, current_user.employee_id) if current_user.employee_id else None
    return {
        "id": current_user.id,
        "access_rights": current_user.access_rights,
        "employee_id": current_user.employee_id,
        "first_name": employee.first_name if employee else None,
        "last_name": employee.last_name if employee else None,
    }