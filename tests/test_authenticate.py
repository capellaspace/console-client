import base64
from unittest.mock import MagicMock

import pytest
from pytest_httpx import HTTPXMock

from capella_console_client.config import CONSOLE_API_URL
from capella_console_client import CapellaConsoleClient
from capella_console_client.exceptions import AuthenticationError
import capella_console_client.session
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
        url=f"{CONSOLE_API_URL}/token", method="POST", status_code=400, json={"error": {"code": "not allowed"}}
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
    assert client._sesh._refresh_token == post_mock_responses("/token")["refreshToken"]


def test_token_auth(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=f"{CONSOLE_API_URL}/user", json=get_mock_responses("/user"))

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
    "email,pw,token,prompt_count_email,prompt_count_pw",
    [
        (None, None, None, 1, 1),
        ("", "", "", 1, 1),
        (None, "MOCK_PW", None, 1, 0),
        ("MOCK_EMAIL", None, None, 0, 1),
    ],
)
def test_authenticate_missing_data_prompts(
    email,
    pw,
    token,
    prompt_count_email,
    prompt_count_pw,
    auth_httpx_mock: HTTPXMock,
    monkeypatch,
):
    email_mock = MagicMock()
    pw_mock = MagicMock()
    monkeypatch.setattr("builtins.input", email_mock)
    monkeypatch.setattr(capella_console_client.session, "getpass", pw_mock)

    CapellaConsoleClient(email=email, password=pw, token=token)
    assert email_mock.call_count == prompt_count_email
    assert pw_mock.call_count == prompt_count_pw


def test_authenticate_missing_data_prompts_empty(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda x: "")
    monkeypatch.setattr(capella_console_client.session, "getpass", lambda x: "")

    with pytest.raises(ValueError):
        CapellaConsoleClient()


def test_whoami(auth_httpx_mock):
    client = CapellaConsoleClient(email="MOCK_EMAIL", password="MOCK_PW")
    whoami = client.whoami()
    assert whoami == get_mock_responses("/user")


def test_chatty_client(auth_httpx_mock):
    # chatty client
    CapellaConsoleClient(email="MOCK_EMAIL", password="MOCK_PW", verbose=True)
