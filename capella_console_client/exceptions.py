from typing import Dict, Any


class CapellaConsoleClientError(Exception):
    response = None
    data: Dict[str, Any] = {}
    message = "An unknown error occurred"

    def __init__(self, message=None, code=None, data={}, response=None):
        self.response = response
        if message:
            self.message = message
        if code:
            self.code = code
        if data:
            self.data = data


class AuthenticationError(CapellaConsoleClientError):
    pass


class NoValidStacIdsError(CapellaConsoleClientError):
    pass


class TaskNotCompleteError(CapellaConsoleClientError):
    pass


class InsufficientFundsError(CapellaConsoleClientError):
    pass


class OrderRejectedError(CapellaConsoleClientError):
    pass


class OrderExpiredError(CapellaConsoleClientError):
    pass


class OrderValidationError(CapellaConsoleClientError):
    pass


class ConnectError(CapellaConsoleClientError):
    pass


class CollectionAccessDeniedError(CapellaConsoleClientError):
    pass


class AuthorizationError(CapellaConsoleClientError):
    pass


class NoRefreshTokenError(CapellaConsoleClientError):
    pass


DEFAULT_ERROR_CODE = "GENERAL_API_ERROR"
INVALID_TOKEN_ERROR_CODE = "INVALID_TOKEN"
ORDER_EXPIRED_ERROR_CODE = "ORDER_EXPIRED"
COLLECTION_ACCESS_DENIED_ERROR_CODE = "COLLECTION_ACCESS_DENIED"
NOT_AUTHORIZED_ERROR_CODE = "NOT_AUTHORIZED"
ORDER_VALIDATION_ERROR_CODE = "ORDER_VALIDATION_ERROR"

UNAUTHORIZED_MESSAGE = "unauthorized"

ERROR_CODES = {
    INVALID_TOKEN_ERROR_CODE: AuthenticationError,
    ORDER_EXPIRED_ERROR_CODE: OrderExpiredError,
    COLLECTION_ACCESS_DENIED_ERROR_CODE: CollectionAccessDeniedError,
    NOT_AUTHORIZED_ERROR_CODE: AuthorizationError,
    ORDER_VALIDATION_ERROR_CODE: OrderValidationError,
}

ERROR_CODES_BY_MESSAGE_SNIP = {
    "order expired": ORDER_EXPIRED_ERROR_CODE,
    "not permitted to access any of the collection": COLLECTION_ACCESS_DENIED_ERROR_CODE,
    "not authorized to perform": NOT_AUTHORIZED_ERROR_CODE,
}

NON_RETRYABLE_ERROR_CODES = (
    INVALID_TOKEN_ERROR_CODE,
    COLLECTION_ACCESS_DENIED_ERROR_CODE,
    NOT_AUTHORIZED_ERROR_CODE,
)


def handle_error_response_and_raise(response):
    if not response.is_stream_consumed:
        response.read()
    error = response.json()
    try:
        if "error" in error:
            error = error["error"]

        message = error.get("message", error.get("Message"))
        code = error.get("code", DEFAULT_ERROR_CODE)
        data = {
            **error.get("data", {}),
            **error.get("detail", {}),
        }
    except Exception:
        message = error
        code = DEFAULT_ERROR_CODE
        data = {}

    if message is not None and message.lower() == UNAUTHORIZED_MESSAGE and code == DEFAULT_ERROR_CODE:
        code = INVALID_TOKEN_ERROR_CODE

    # try to assign some more meaningful exception class by message
    if code == DEFAULT_ERROR_CODE and message:
        try:
            code = next(v for k, v in ERROR_CODES_BY_MESSAGE_SNIP.items() if k in message.lower())
        except StopIteration:
            pass
    exc = ERROR_CODES.get(code, CapellaConsoleClientError)(message=message, code=code, data=data, response=response)
    raise exc
