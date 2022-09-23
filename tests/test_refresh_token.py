import pytest
import httpx

from pytest_httpx import HTTPXMock

from .test_data import post_mock_responses

from capella_console_client.config import CONSOLE_API_URL
from capella_console_client.exceptions import (
    AuthenticationError,
    INVALID_TOKEN_ERROR_CODE,
    CapellaConsoleClientError,
    DEFAULT_ERROR_CODE,
    NoRefreshTokenError,
)
from capella_console_client import CapellaConsoleClient


def test_refresh_token(refresh_token_client):
    token_refr_mock_response = post_mock_responses("/token/refresh")

    assert refresh_token_client._sesh.headers["Authorization"] == "Bearer MOCK_TOKEN"
    assert refresh_token_client._sesh._refresh_token == "MOCK_REFRESH_TOKEN"
    refresh_token_client._sesh.perform_token_refresh()
    assert refresh_token_client._sesh.headers["Authorization"] == f"Bearer {token_refr_mock_response['accessToken']}"
    assert refresh_token_client._sesh._refresh_token == token_refr_mock_response["refreshToken"]


def test_auto_refresh_no_capture_exc_type(refresh_token_client, auth_httpx_mock: HTTPXMock):
    def raise_general_error(request):
        raise CapellaConsoleClientError(code=DEFAULT_ERROR_CODE)

    auth_httpx_mock.add_callback(raise_general_error)

    with pytest.raises(CapellaConsoleClientError):
        refresh_token_client._sesh.get("/this-route-does-not-exist")


def test_auto_refresh_no_capture_error_code(refresh_token_client, auth_httpx_mock: HTTPXMock):
    def raise_auth_error(request):
        raise AuthenticationError(code="some_other_error_code")

    auth_httpx_mock.add_callback(raise_auth_error)

    with pytest.raises(AuthenticationError):
        refresh_token_client._sesh.get("/this-route-does-not-exist")


def test_auto_refresh(refresh_token_client, auth_httpx_mock: HTTPXMock):
    def raise_invalid_token(request):
        raise AuthenticationError(code=INVALID_TOKEN_ERROR_CODE)

    auth_httpx_mock.add_callback(raise_invalid_token)

    assert refresh_token_client._sesh.headers["Authorization"] == "Bearer MOCK_TOKEN"
    assert refresh_token_client._sesh._refresh_token == "MOCK_REFRESH_TOKEN"

    with pytest.raises(AuthenticationError):
        refresh_token_client._sesh.get("/this-route-does-not-exist")

    requests = auth_httpx_mock.get_requests()
    assert len(requests) == 5

    urls = [r.url for r in requests]

    EXPECTED_URLS = [
        httpx.URL(f"{CONSOLE_API_URL}/token"),
        httpx.URL(f"{CONSOLE_API_URL}/user"),
        httpx.URL(f"{CONSOLE_API_URL}/this-route-does-not-exist"),
        httpx.URL(f"{CONSOLE_API_URL}/token/refresh"),
        httpx.URL(f"{CONSOLE_API_URL}/this-route-does-not-exist"),
    ]
    assert urls == EXPECTED_URLS

    assert requests[-1].headers["Authorization"] == f"Bearer {post_mock_responses('/token/refresh')['accessToken']}"


def test_no_refresh_token_provided():
    token = "MOCK_TOKEN"
    client = CapellaConsoleClient(token=token, no_token_check=True)

    with pytest.raises(NoRefreshTokenError):
        client._sesh.perform_token_refresh()
