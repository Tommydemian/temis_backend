# src/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes import api_router
from src.core.database import lifespan
from src.core.exceptions import AppException

app = FastAPI(
    title="ERP API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
        },
    )


# Middleware
@app.middleware("http")
async def log_middleware(request: Request, call_next):
    print(f"1️⃣ MIDDLEWARE START: {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        print(f"9️⃣ MIDDLEWARE END: {response.status_code}")
        return response
    except Exception as e:
        print(f"💥 MIDDLEWARE CAUGHT ERROR: {e}")
        raise


# Include all routes
app.include_router(api_router)


@app.get("/")
async def root():
    return {"message": "ERP API - FastAPI + PostgreSQL"}
