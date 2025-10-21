from fastapi import HTTPException
from jose import JWTError, jwt

from src.config import settings

ALGORITHM = "HS256"


async def get_current_user(authorization: str):
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        # Remover "Bearer " del header
        token = authorization.replace("Bearer ", "")

        # Decodificar JWT
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])

        # Extraer valores con validación
        user_id_str = payload.get("sub")
        tenant_id = payload.get("tenant_id")

        # Validar que existan antes de convertir
        if not user_id_str or tenant_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        return {"user_id": int(user_id_str), "tenant_id": tenant_id}

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
