#!/usr/bin/env python

import base64

import pytest
from pytest_httpx import HTTPXMock

from capella_console_client.config import CONSOLE_API_URL
from capella_console_client import CapellaConsoleClient
from capella_console_client.exceptions import (
    AuthenticationError,
)
from .test_data import (
    post_mock_responses,
    get_mock_responses,
)


def test_basic_auth(auth_httpx_mock: HTTPXMock):
    email = "MOCK_EMAIL"
    pw = "MOCK_PW"

    client = CapellaConsoleClient(email=email, password=pw)
    _shared_basic_auth_asserts(auth_httpx_mock, client, email, pw)


def test_failed_basic_auth(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/token",
        status_code=400,
        json={
            "error": {
                "message": "Incorrect username or password.",
                "code": "GENERAL_API_ERROR",
            }
        },
    )
    with pytest.raises(AuthenticationError):
        CapellaConsoleClient(email="MOCK_INVALID_EMAIL", password="MOCK_INVALID_PW")


def test_basic_auth_takes_precedence(auth_httpx_mock: HTTPXMock):
    email = "MOCK_EMAIL"
    pw = "MOCK_PW"
    token = "MOCK_TOKEN"

    client = CapellaConsoleClient(email=email, password=pw, token=token)
    _shared_basic_auth_asserts(auth_httpx_mock, client, email, pw)


def _shared_basic_auth_asserts(auth_httpx_mock, client, email, pw):
    requests = auth_httpx_mock.get_requests()
    assert requests[0].url == f"{CONSOLE_API_URL}/token"
    assert requests[0].method == "POST"

    basic_token = base64.b64encode(f"{email}:{pw}".encode()).decode("utf-8")
    assert requests[0].headers["authorization"] == f"Basic {basic_token}"
    assert requests[1].url == f"{CONSOLE_API_URL}/user"
    assert requests[1].method == "GET"

    assert "Authorization" in client._sesh.headers
    mock_access_token = post_mock_responses("/token")["accessToken"]
    assert client._sesh.headers["Authorization"] == f"Bearer {mock_access_token}"


def test_token_auth(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/user", json=get_mock_responses("/user")
    )

    token = "MOCK_TOKEN"

    client = CapellaConsoleClient(token=token)
    requests = httpx_mock.get_requests()

    assert requests[0].url == f"{CONSOLE_API_URL}/user"
    assert requests[0].method == "GET"

    assert "Authorization" in client._sesh.headers
    mock_access_token = post_mock_responses("/token")["accessToken"]
    assert client._sesh.headers["Authorization"] == f"Bearer {mock_access_token}"


def test_token_auth_no_check(httpx_mock: HTTPXMock):
    token = "MOCK_TOKEN"
    client = CapellaConsoleClient(token=token, no_token_check=True)
    requests = httpx_mock.get_requests()

    assert "Authorization" in client._sesh.headers
    assert client._sesh.headers["Authorization"] == f"Bearer {token}"
    assert len(requests) == 0


@pytest.mark.parametrize(
    "email,pw,token",
    [
        (None, None, None),
        ("", "", ""),
        (None, "MOCK_PW", None),
        ("MOCK_EMAIL", None, None),
    ],
)
def test_authenticate_missing_data(email, pw, token):
    with pytest.raises(ValueError):
        CapellaConsoleClient(email=email, password=pw, token=token)


def test_whoami(auth_httpx_mock):
    client = CapellaConsoleClient(email="MOCK_EMAIL", password="MOCK_PW")
    whoami = client.whoami()

    assert whoami == get_mock_responses("/user")


def test_chatty_client(auth_httpx_mock):
    # chatty client
    CapellaConsoleClient(email="MOCK_EMAIL", password="MOCK_PW", verbose=True)
