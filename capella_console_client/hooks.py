import logging

from .exceptions import handle_error_response, NON_RETRYABLE_ERROR_CODES
from capella_console_client.exceptions import CapellaConsoleClientError

logger = logging.getLogger()


def translate_error_to_exception(response):
    if response.is_error:
        handle_error_response(response)


def log_on_4xx_5xx(response):
    try:
        response.raise_for_status()
    except Exception:
        request = response.request
        logger.error(
            f"response event hook: {request.method} {request.url} - Status {response.status_code}"
        )
        logger.error(f"the following error occured: {response.json()}")


def retry_if_http_status_error(exception):
    """Return upon httpx.HTTPStatusError"""
    if getattr(exception, "code", None) in NON_RETRYABLE_ERROR_CODES:
        return False
    return isinstance(exception, CapellaConsoleClientError)
