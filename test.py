# import time

# from loguru import logger


# async def process_payment(order_id: int, amount: float, payment_method: str):
#     log = logger.bind(order_id=order_id)

#     logger.info(
#         "Starting payment process...",
#         order_id=order_id,
#         amount=amount,
#         payment_method=payment_method,
#     )
#     # Validar monto
#     if amount <= 0:
#         logger.warning("Invalid payment amount", amount=amount, reason="must be > 0")
#         # ¿Qué log pondrías acá?
#         raise InvalidAmountError(amount)

#     # Conectar a Mercado Pago API
#     # ¿Qué log pondrías acá?
#     logger.info(
#         "Calling Mercado Pago API",
#         amount=amount,
#         payment_method=payment_method,
#     )

#     start = time.perf_counter()

#     response = await mercadopago_client.charge(amount, payment_method)

#     elapsed_ms = (time.perf_counter() - start) * 1000

#     if response.status == "approved":
#         # ¿Qué log pondrías acá?
#         logger.info(
#             "Payment approved",
#             status=response.status,
#             transaction_id=response.id,
#             duration_ms=round(elapsed_ms, 2),
#         )
#         return {"status": "success", "transaction_id": response.id}
#     else:
#         logger.opt(exception=True).error(
#             "Payment failed - unexpected error",
#             error_type=e.__class__.__name__,
#         )  # ¿Qué log pondrías acá?
#         raise PaymentFailedError(response.error
