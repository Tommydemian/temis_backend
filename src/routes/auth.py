# src/routes/auth.py
from fastapi import APIRouter, Depends, status

from src.database import get_conn
from src.models import LoginRequest, TokenResponse, UserCreate
from src.services.afip.services import login_user, register_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def register(account_data: UserCreate, conn=Depends(get_conn)):
    return await register_user(account_data, conn)


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest, conn=Depends(get_conn)):
    return await login_user(credentials, conn)
