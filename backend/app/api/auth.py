from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.company import CompanyRegistration
from app.services.auth_service import AuthService
from app.schemas.user import UserResponse
from app.api.dependencies import get_current_user
from app.schemas.auth import LoginRequest

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/register")
def register_company(
    request: CompanyRegistration,
    db: Session = Depends(get_db)
):

    try:
        return AuthService.register_company(
            db,
            request
        )

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.post("/login")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):

    try:

        return AuthService.login(
            db,
            request
        )

    except Exception as e:

        raise HTTPException(
            status_code=401,
            detail=str(e)
        )


@router.get("/me", response_model=UserResponse)
def me(current_user=Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "full_name": current_user.full_name,
        "email": current_user.email,
        "role": current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role),
        "is_active": current_user.is_active,
    }