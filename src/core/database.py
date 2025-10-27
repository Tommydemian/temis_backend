# src/database.py
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import asyncpg
from fastapi import FastAPI, Request
from loguru import logger

from src.core import settings

BASE_DIR = Path(__file__).resolve().parent.parent  # Sube 2 niveles desde database.py
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)  # Crear carpeta si no existe

DATABASE_URL = settings.DATABASE_URL


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Database connection pool lifecycle"""
    # Loguru default handler removed.
    logger.remove()

    logger.add(
        sink=sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG",  # Mostrar todo en dev
        colorize=True,
    )
    logger.add(
        sink=str(LOGS_DIR / "app.log"),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="INFO",
        rotation="10 MB",
        retention="1 week",
        compression="zip",
    )

    logger.info("Starting application")

    app.state.conn_pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=2,
        max_size=10,
    )

    logger.info("Database pool created", min_size=2, max_size=10)

    yield

    logger.info("Shutting down application")
    await app.state.conn_pool.close()
    logger.info("Database pool closed")


async def get_conn(request: Request):  # ✅ Cambiar FastAPI por Request
    """Dependency para obtener conexión del pool"""
    async with request.app.state.conn_pool.acquire() as conn:
        yield conn
