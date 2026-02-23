"""
Authentication API endpoints
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.infrastructure.database.engine import get_session
from app.core.services.auth_service import AuthService
from app.infrastructure.database.repositories import UserAccountRepository

# Create router
auth_router = APIRouter(prefix="/auth", tags=["auth"])


# ========== Schemas ==========

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserInfo(BaseModel):
    id: str
    email: str
    role: str
    tenant_id: str
    tenant_name: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


# ========== Endpoints ==========

@auth_router.post("/login", response_model=LoginResponse)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_session)
):
    """
    User login endpoint
    
    Authenticates user and returns JWT token
    """
    import traceback
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        user = await AuthService.authenticate_user(
            db=db,
            email=credentials.email,
            password=credentials.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Tenant is already loaded by UserAccountRepository via selectinload
        
        # Generate JWT token
        access_token = AuthService.generate_jwt_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            role=user.role
        )
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "tenant_id": user.tenant_id,
                "tenant_name": user.tenant.name if user.tenant else None
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in login endpoint: {e}", exc_info=True)
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


from app.interfaces.api.dependencies import get_current_tenant_id

# ========== Endpoints ==========
...
@auth_router.get("/me", response_model=UserInfo)
async def get_current_user(
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """
    Get current authenticated user info
    
    Requires valid JWT token
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    user_repo = UserAccountRepository(db)
    user = await user_repo.get(user_id, tenant_id=tenant_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserInfo(
        id=user.id,
        email=user.email,
        role=user.role,
        tenant_id=user.tenant_id,
        tenant_name=user.tenant.name if user.tenant else None
    )


@auth_router.put("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_session)
):
    """
    Change password for current authenticated user.
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    user_repo = UserAccountRepository(db)
    user = await user_repo.get(user_id, tenant_id=tenant_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account has no password set (legacy). Contact admin to reset."
        )

    if not AuthService.verify_password(payload.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    new_hash = AuthService.hash_password(payload.new_password)
    from app.infrastructure.database.models.tenant import UserAccount as UserModel
    from sqlalchemy import update as sa_update

    stmt = (
        sa_update(UserModel)
        .where(UserModel.id == user_id, UserModel.tenant_id == tenant_id)
        .values(password_hash=new_hash, updated_at=datetime.now(timezone.utc))
    )
    await db.execute(stmt)
    await db.commit()

    return {"message": "Password updated successfully"}
