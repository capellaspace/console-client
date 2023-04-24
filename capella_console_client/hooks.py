from typing import List
from dataclasses import dataclass

import httpx

from capella_console_client.exceptions import (
    CapellaConsoleClientError,
    handle_error_response_and_raise,
    NON_RETRYABLE_ERROR_CODES,
)
from capella_console_client.logconf import logger


@dataclass
class RequestMeta:
    method: str
    url: httpx.URL


# do not log out the following requests
SILENCE_REQUESTS: List[RequestMeta] = []


def translate_error_to_exception(response):
    if response.status_code >= 400:
        handle_error_response_and_raise(response)


def log_on_4xx_5xx(response):
    try:
        response.raise_for_status()
    except httpx.HTTPError:
        request = response.request
        cur = RequestMeta(request.method, request.url)
        if cur in SILENCE_REQUESTS:
            return
        if not response.is_stream_consumed:
            response.read()

        msg = f"Request: {request.method} {request.url} - Status: {response.status_code}"
        resp_json = response.json()
        if resp_json:
            msg += f" - Response: {resp_json}"

        logger.error(msg)
        return True


def retry_if_http_status_error(exception):
    """Return upon httpx.HTTPStatusError"""
    if getattr(exception, "code", None) in NON_RETRYABLE_ERROR_CODES:
        return False
    return isinstance(exception, CapellaConsoleClientError)


def retry_if_httpx_status_error(exception):
    return isinstance(exception, httpx.HTTPStatusError)


def log_attempt_delay(attempts, delay):
    logger.info(f"Attempt #{attempts}, retrying in {delay} ms")
    return delay
