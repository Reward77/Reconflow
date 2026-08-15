from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.user import User,UserRole

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)


class AuthService:

    @staticmethod
    def register_company(db: Session, data):

        company_exists = db.query(Company).filter(
            Company.company_email == data.company_email
        ).first()

        if company_exists:
            raise Exception("Company already exists.")

        user_exists = db.query(User).filter(
            User.email == data.admin_email
        ).first()

        if user_exists:
            raise Exception("Administrator email already exists.")

        company = Company(
            company_name=data.company_name,
            company_email=data.company_email,
            phone=data.phone,
            address=data.address
        )

        db.add(company)
        db.flush()

        admin = User(
            company_id=company.id,
            full_name=data.admin_name,
            email=data.admin_email,
            password_hash=hash_password(data.password),
            role=UserRole.ADMIN
        )

        db.add(admin)

        db.commit()
        db.refresh(company)

        return {
            "message": "Company registered successfully.",
            "company_id": str(company.id)
        }

    @staticmethod
    def login(db: Session, request):

        user = db.query(User).filter(
            User.email == request.email
        ).first()

        if not user:
            raise Exception("Invalid email or password.")

        if not verify_password(
            request.password,
            user.password_hash
        ):
            raise Exception("Invalid email or password.")

        token = create_access_token(
            {
                "sub": str(user.id),
                "email": user.email,
                "company_id": str(user.company_id),
                "role": user.role
            }
        )

        return {
            "access_token": token,
            "token_type": "Bearer"
        }