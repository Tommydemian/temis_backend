from datetime import datetime, timedelta, timezone
from typing import cast

import asyncpg
from fastapi import HTTPException
from jose import jwt
from loguru import logger
from passlib.context import CryptContext

from src.api.schemas import (
    LoginRequest,
    TokenResponse,
    User,
    UserCreate,
)
from src.core.config import settings
from src.core.exceptions import NotFoundError

# ============================================================================
# AUTH CONFIG
# ============================================================================

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")


# ============================================================================
# AUTH SERVICES
# ============================================================================


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def register_user(
    user_data: UserCreate, conn: asyncpg.Connection
) -> TokenResponse:
    """Register new user and return JWT token"""
    password_hashed = hash_password(user_data.password)

    row = await conn.fetchrow(
        """
        INSERT INTO \"user\" (email, password_hash)
        VALUES ($1, $2, $3)
        RETURNING id, email, password_hash, created_at, updated_at, tenant_id
        """,
        user_data.email,
        password_hashed,
        4,
    )

    logger.debug(row)

    user = User(**cast(dict, row))
    tenant_id = user.tenant_id
    token = create_access_token(data={"sub": str(user.id), "tenant_id": tenant_id})

    # cast(int, tenant_id)

    if tenant_id is None:
        raise NotFoundError(identifier="Tenant", resource=str(user.id))

    return TokenResponse(
        access_token=token, token_type="bearer", tenant_id=tenant_id, user_id=user.id
    )


async def login_user(
    credentials: LoginRequest, conn: asyncpg.Connection
) -> TokenResponse:
    """Login user and return JWT token"""
    user_row = await conn.fetchrow(
        'SELECT * FROM "user" WHERE email = $1',
        credentials.email,
    )

    if not user_row:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    user = User(**dict(user_row))

    tenant_id = user.tenant_id

    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = create_access_token(data={"sub": str(user.id), "tenant_id": user.tenant_id})

    if tenant_id is None:
        raise NotFoundError(identifier="Tenant", resource=str(user.id))

    return TokenResponse(
        access_token=token, token_type="bearer", tenant_id=tenant_id, user_id=user.id
    )
