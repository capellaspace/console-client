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
SILENCE_REQUESTS: list[RequestMeta] = []


def translate_error_to_exception(response: httpx.Response) -> None:
    if response.status_code >= 400:
        handle_error_response_and_raise(response)


def log_on_4xx_5xx(response: httpx.Response) -> bool | None:
    try:
        response.raise_for_status()
    except httpx.HTTPError:
        request = response.request
        cur = RequestMeta(request.method, request.url)
        if cur in SILENCE_REQUESTS:
            return None
        if not response.is_stream_consumed:
            response.read()

        msg = f"Request: {request.method} {request.url} - Status: {response.status_code}"
        resp_json = response.json()
        if resp_json:
            msg += f" - Response: {resp_json}"

        logger.error(msg)
        return True
    return None


def log_retry_attempt(retry_state) -> None:
    """Tenacity callback to log retry attempts"""
    attempt_number = retry_state.attempt_number
    sleep_time = retry_state.next_action.sleep
    logger.info(f"Attempt #{attempt_number}, retrying in {sleep_time * 1000:.0f} ms")
