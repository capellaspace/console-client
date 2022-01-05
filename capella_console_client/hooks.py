import logging
from typing import List
from dataclasses import dataclass

import httpx

from .exceptions import handle_error_response, NON_RETRYABLE_ERROR_CODES
from capella_console_client.exceptions import CapellaConsoleClientError

logger = logging.getLogger()


@dataclass
class RequestMeta:
    method: str
    url: httpx.URL


# do not log out the following requests
SILENCE_REQUESTS: List[RequestMeta] = []


def translate_error_to_exception(response):
    if response.is_error:
        handle_error_response(response)


def log_on_4xx_5xx(response):
    try:
        response.raise_for_status()
    except Exception:

        request = response.request
        cur = RequestMeta(request.method, request.url)
        if cur in SILENCE_REQUESTS:
            return

        logger.error(
            f"Request: {request.method} {request.url} - Status {response.status_code} - Response: {response.json()}"
        )
        return True


def retry_if_http_status_error(exception):
    """Return upon httpx.HTTPStatusError"""
    if getattr(exception, "code", None) in NON_RETRYABLE_ERROR_CODES:
        return False
    return isinstance(exception, CapellaConsoleClientError)
