class AppException(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(AppException):
    """Resource not found"""

    def __init__(self, resource: str, identifier: str | int):
        message = f"{resource} not found: {identifier}"
        super().__init__(message, status_code=404)
        self.resource = resource
        self.identifier = identifier


class InvalidQuantityError(AppException):
    def __init__(self, quantity: int):
        message = f"Invalid Quantity: {quantity}, (must be > 0)"
        super().__init__(message, status_code=400)
        self.quantity = quantity
