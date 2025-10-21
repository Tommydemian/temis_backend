# from contextlib import asynccontextmanager
# from datetime import datetime, timedelta, timezone
# from decimal import Decimal

# # import time
# import asyncpg
# from fastapi import Depends, FastAPI, HTTPException, Request, status

# # from fastapi.responses import JSONResponse
# from jose import jwt
# from passlib.context import CryptContext

# from src.config import settings
# from src.models import (
#     Account,
#     AccountCreate,
#     ComponentAvailability,
#     LoginRequest,
#     OrderRequest,
#     OrderResponse,
#     OrderResponseItem,
#     TokenResponse,
# )

# # Config
# SECRET_KEY = settings.SECRET_KEY  # En producción: env variable
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 30

# pwd_context = CryptContext(schemes=["sha256_crypt", "argon2"], deprecated="auto")


# def hash_password(password: str) -> str:
#     return pwd_context.hash(password)


# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     return pwd_context.verify(plain_password, hashed_password)


# def create_access_token(data: dict) -> str:
#     to_encode = data.copy()
#     to_encode["exp"] = datetime.now(timezone.utc) + timedelta(
#         minutes=ACCESS_TOKEN_EXPIRE_MINUTES
#     )

#     token = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
#     return token


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     app.state.conn_pool = await asyncpg.create_pool(
#         user=settings.db_user,
#         password=settings.db_password,
#         database=settings.db_database,
#         host=settings.db_host,
#         port=settings.db_port,
#         min_size=2,
#         max_size=10,
#     )
#     yield
#     await app.state.conn_pool.close()


# app = FastAPI(lifespan=lifespan)


# # Middleware
# @app.middleware("http")
# async def log_middleware(request: Request, call_next):
#     print(f"1️⃣ MIDDLEWARE START: {request.method} {request.url.path}")
#     try:
#         response = await call_next(request)
#         print(f"9️⃣ MIDDLEWARE END: {response.status_code}")
#         return response
#     except Exception as e:
#         print(f"💥 MIDDLEWARE CAUGHT ERROR: {e}")
#         raise


# async def get_conn():
#     async with app.state.conn_pool.acquire() as conn:
#         yield conn


# @app.get("/orders/{order_id}", response_model=OrderResponse)
# async def get_order(order_id: int, conn=Depends(get_conn)):
#     print(order_id)
#     rows = await conn.fetch(
#         """
#         SELECT
#             o.id,
#             o.customer_name,
#             o.total_price,
#             o.status,
#             o.delivery_date,
#             op.product_id AS product_id,
#             op.quantity,
#             op.unit_price,
#             p.name,
#             p.category
#         FROM "order" o
#         JOIN order_product AS op ON o.id = op.order_id
#         JOIN product AS p ON p.id = op.product_id
#         WHERE o.id = $1
#         """,
#         order_id,
#     )

#     res_dict = OrderResponse(
#         order_id=order_id,
#         customer_name="",
#         total_price=Decimal("0.00"),
#         items=[],
#     )

#     for row in rows:
#         res_dict.customer_name = row.get("customer_name")
#         res_dict.total_price = row.get("total_price")
#         res_dict.items.append(
#             OrderResponseItem(
#                 product_id=row.get("product_id"),
#                 product_name=row.get("name"),
#                 quantity=row.get("quantity"),
#                 unit_price=row.get("unit_price"),
#                 subtotal=row.get("quantity") * row.get("unit_price"),
#             )
#         )

#     return res_dict


# @app.get("/products")
# async def get_products(
#     is_active: bool | None = None,
#     conn=Depends(get_conn),
# ):
#     if is_active is not None:
#         rows = await conn.fetch("SELECT * FROM product WHERE is_active = $1", is_active)
#     else:
#         rows = await conn.fetch("SELECT * FROM product")

#     return rows


# @app.post(
#     "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
# )
# async def register_account(account_data: AccountCreate, conn=Depends(get_conn)):
#     password_hashed = hash_password(account_data.password)
#     row = await conn.fetchrow(
#         """
#             INSERT INTO account (email, password_hash)
#             VALUES ($1, $2)
#             RETURNING id, email, password_hash, created_at, updated_at
#             """,
#         account_data.email,
#         password_hashed,
#     )

#     user = Account(**dict(row))

#     jwt = create_access_token(data={"sub": str(user.id)})

#     return {"access_token": jwt, "token_type": "bearer"}


# @app.post("/login", response_model=TokenResponse)
# async def login_acocunt(credentials: LoginRequest, conn=Depends(get_conn)):
#     user_row = await conn.fetchrow(
#         "SELECT * FROM account WHERE email = $1",
#         credentials.email,
#     )

#     if not user_row:
#         raise HTTPException(status_code=401, detail="Incorrect email or password")

#     user = Account(**dict(user_row))

#     valid_credentials = verify_password(
#         plain_password=credentials.password, hashed_password=user.password_hash
#     )

#     if not valid_credentials:
#         raise HTTPException(status_code=401, detail="Incorrect email or password")

#     jwt = create_access_token(data={"sub": str(user.id)})
#     return {"access_token": jwt, "token_type": "bearer"}


# @app.get("/production/check-availability")
# async def check_availability(product_name: str, quantity: int, conn=Depends(get_conn)):
#     if quantity <= 0:
#         raise HTTPException(400, {"error": "invalid_quantity"})

#     product = await conn.fetchrow(
#         "SELECT id FROM product WHERE name = $1", product_name
#     )
#     if not product:
#         raise HTTPException(404, {"error": "product_not_found"})

#     view = await conn.fetch(
#         "SELECT * FROM check_production_availability($1::TEXT, $2::INT)",
#         product_name,
#         quantity,
#     )
#     row_list = [ComponentAvailability(**row) for row in view]

#     return {
#         "detailed_data": row_list,
#         "can_produce": not any(not row.can_produce for row in row_list),
#     }


# @app.post("/orders", status_code=status.HTTP_201_CREATED)
# async def create_order(order: OrderRequest, conn=Depends(get_conn)):
#     delivery_date = order.delivery_date
#     if delivery_date:
#         if delivery_date.tzinfo is None:
#             delivery_date = delivery_date.replace(tzinfo=timezone.utc)
#     else:
#         delivery_date = datetime.now(timezone.utc) + timedelta(days=7)

#     async with conn.transaction():
#         # Insert order
#         print(f"delivery_date: {delivery_date}, tzinfo: {delivery_date.tzinfo}")
#         order_row = await conn.fetchrow(
#             """
#         INSERT INTO "order"(customer_name, customer_phone, delivery_date)
#         VALUES ($1, $2, $3)
#         RETURNING id, created_at
#         """,
#             order.customer_name,
#             order.customer_phone,
#             delivery_date,
#         )
#         order_id = order_row["id"]

#         # list of prod_ids
#         products_id = [item.product_id for item in order.items]

#         # get sale_val of prod
#         rows = await conn.fetch(
#             """
#             SELECT id, name, sale_price
#             FROM product
#             WHERE id = ANY($1)
#             """,
#             products_id,
#         )

#         # dict for lookups
#         products_dict = {row["id"]: dict(row) for row in rows}

#         print(f"✅ Order created: {order_id}, total: adasda")

#         # 3. Bulk insert order_product
#         order_items_data = [
#             (
#                 order_id,
#                 item.product_id,
#                 item.quantity,
#                 products_dict[item.product_id]["sale_price"],
#             )
#             for item in order.items
#         ]

#         await conn.executemany(
#             """
#         INSERT INTO order_product (order_id, product_id, quantity, unit_price)
#         VALUES ($1, $2, $3, $4)
#         """,
#             order_items_data,
#         )
#         # 4. Calculate total
#         total = sum(
#             products_dict[item.product_id]["sale_price"] * item.quantity
#             for item in order.items
#         )
#         print(f"✅ Order created: {order_id}, total: {total}")

#         # 5. Update order total
#         await conn.execute(
#             'UPDATE "order" SET total_price = $1 WHERE id = $2', total, order_id
#         )

#         return {
#             "order_id": order_id,
#             "customer_name": order.customer_name,
#             "status": "pending",
#             "total_price": float(total),
#             "items": [
#                 {
#                     "product_id": item.product_id,
#                     "product_name": products_dict[item.product_id]["name"],
#                     "quantity": item.quantity,
#                     "unit_price": float(products_dict[item.product_id]["sale_price"]),
#                     "subtotal": float(
#                         products_dict[item.product_id]["sale_price"] * item.quantity
#                     ),
#                 }
#                 for item in order.items
#             ],
#             "created_at": order_row["created_at"],
#         }

# src/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.database import lifespan
from src.routes import api_router

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
