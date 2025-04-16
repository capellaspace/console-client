import os
from unittest.mock import MagicMock

import pytest
from pytest_httpx import HTTPXMock

from capella_console_client.config import CONSOLE_API_URL, CAPELLA_API_KEY_ENV
from capella_console_client import CapellaConsoleClient
from capella_console_client.exceptions import AuthenticationError
from capella_console_client.enumerations import AuthHeaderPrefix
import capella_console_client.session
from .test_data import (
    post_mock_responses,
    get_mock_responses,
)


def test_basic_auth_not_supported():
    email = "MOCK_EMAIL"
    pw = "MOCK_PW"

    with pytest.raises(TypeError):
        CapellaConsoleClient(email=email, password=pw)


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


def test_api_key_auth(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=f"{CONSOLE_API_URL}/user", json=get_mock_responses("/user"))
    api_key = "MOCK_API_KEY"

    client = CapellaConsoleClient(api_key=api_key)
    requests = httpx_mock.get_requests()

    assert requests[0].url == f"{CONSOLE_API_URL}/user"
    assert requests[0].method == "GET"

    assert "Authorization" in client._sesh.headers
    assert client._sesh.headers["Authorization"] == f"{AuthHeaderPrefix.API_KEY.value} {api_key}"


def test_api_key_auth_no_check(httpx_mock: HTTPXMock):
    api_key = "MOCK_API_KEY"
    client = CapellaConsoleClient(api_key=api_key, no_token_check=True)
    requests = httpx_mock.get_requests()

    assert "Authorization" in client._sesh.headers
    assert client._sesh.headers["Authorization"] == f"{AuthHeaderPrefix.API_KEY.value} {api_key}"
    assert len(requests) == 0


def test_failed_api_key_auth(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=f"{CONSOLE_API_URL}/user", status_code=401, json={"message": "Unauthorized"})
    with pytest.raises(AuthenticationError):
        CapellaConsoleClient(api_key="MOCK_INVALID_API_KEY")


@pytest.mark.parametrize(
    "api_key,token,prompt_count_api_key",
    [
        (None, None, 1),
        ("", "", 1),
    ],
)
def test_authenticate_missing_data_prompts(
    api_key,
    token,
    prompt_count_api_key,
    auth_httpx_mock: HTTPXMock,
    monkeypatch,
):
    api_key_mock = MagicMock(return_value="MOCK_API_KEY")
    monkeypatch.setattr(capella_console_client.session, "getpass", api_key_mock)

    CapellaConsoleClient(api_key=api_key, token=token)
    assert api_key_mock.call_count == prompt_count_api_key


def test_authenticate_missing_data_prompts_empty(monkeypatch):
    monkeypatch.setattr(capella_console_client.session, "getpass", lambda x: "")

    with pytest.raises(ValueError):
        CapellaConsoleClient()


def test_api_key_env_set_no_prompt(auth_httpx_mock: HTTPXMock, monkeypatch):
    env_api_key = "ENV_API_KEY"
    monkeypatch.setenv(CAPELLA_API_KEY_ENV, env_api_key)

    api_key_prompt_mock = MagicMock()
    monkeypatch.setattr(capella_console_client.session, "getpass", api_key_prompt_mock)

    client = CapellaConsoleClient()

    api_key_prompt_mock.assert_not_called()
    assert client._sesh.headers["Authorization"] == f"{AuthHeaderPrefix.API_KEY.value} {env_api_key}"


def test_whoami(auth_httpx_mock):
    client = CapellaConsoleClient(api_key="MOCK_API_KEY")
    whoami = client.whoami()
    assert whoami == get_mock_responses("/user")


def test_chatty_client(auth_httpx_mock):
    client = CapellaConsoleClient(api_key="MOCK_API_KEY", verbose=True)
    assert client.verbose == True
