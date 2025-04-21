import os
from enum import Enum
import warnings
from getpass import getpass

from typing import Optional

from capella_console_client.enumerations import AuthHeaderPrefix
import httpx

from capella_console_client.config import DEFAULT_TIMEOUT, CONSOLE_API_URL, CAPELLA_API_KEY_ENV
from capella_console_client.hooks import log_on_4xx_5xx, translate_error_to_exception
from capella_console_client.logconf import logger
from capella_console_client.exceptions import (
    CapellaConsoleClientError,
    AuthenticationError,
)
from capella_console_client.version import __version__


class AuthMethod(Enum):
    API_KEY = 1  # API key
    TOKEN = 2  # JWT token


AUTHORIZATION_HEADER_NAME = "Authorization"


class AuthMethodDeprecationWarning(DeprecationWarning):
    pass


class CapellaConsoleSession(httpx.Client):
    def __init__(self, *args, **kwargs):
        verbose = kwargs.pop("verbose", False)
        search_url = kwargs.pop("search_url", None)
        event_hooks = [translate_error_to_exception]
        if verbose:
            event_hooks.insert(0, log_on_4xx_5xx)

        deprecation_warning_action = "once" if verbose else "ignore"
        warnings.simplefilter(action=deprecation_warning_action, category=AuthMethodDeprecationWarning)

        super(CapellaConsoleSession, self).__init__(
            *args,
            event_hooks={"response": event_hooks},
            timeout=DEFAULT_TIMEOUT,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "User-Agent": f"capella-console-client/{__version__}",
            },
            **kwargs,
        )
        self.customer_id = None
        self.organization_id = None

        self.search_url = search_url if search_url is not None else f"{self.base_url}/catalog/search"

    def authenticate(
        self,
        api_key: Optional[str] = None,
        token: Optional[str] = None,
        no_token_check: bool = False,
    ) -> None:
        try:
            if not bool(token) and not bool(api_key):
                api_key = self._api_key_from_env_or_prompt()

            auth_method = _get_auth_method(token, api_key)

            if auth_method == AuthMethod.API_KEY:
                self._set_api_key_auth_header(api_key)
            if auth_method == AuthMethod.TOKEN:
                self._set_bearer_auth_header(token)

            if not no_token_check:
                self._cache_user_info()

        except (httpx.HTTPStatusError, CapellaConsoleClientError):
            message = {
                AuthMethod.TOKEN: "provided token invalid",
                AuthMethod.API_KEY: "provided API key invalid",
            }[auth_method]

            raise AuthenticationError(
                f"Unable to authenticate with {self.base_url} ({auth_method}) - {message}"
            ) from None

        suffix = f"({self.base_url})" if self.base_url != CONSOLE_API_URL else ""
        if auth_method in (AuthMethod.API_KEY, AuthMethod.TOKEN) and no_token_check:
            logger.info(f"successfully authenticated {suffix}")
        else:
            logger.info(f"successfully authenticated as {self.email} {suffix}")

    def _api_key_from_env_or_prompt(self):
        """prompt for api.capellaspace.com API key"""
        if CAPELLA_API_KEY_ENV in os.environ:
            return os.environ[CAPELLA_API_KEY_ENV]

        api_key = getpass(
            f"your api_key on {self.base_url} (can also be set by environment variable {CAPELLA_API_KEY_ENV}):"
        ).strip()
        return api_key

    def _set_bearer_auth_header(self, token: Optional[str]):
        assert isinstance(token, str)
        token = token.strip()
        if not token.lower().startswith(AuthHeaderPrefix.TOKEN.value.lower()):
            token = f"{AuthHeaderPrefix.TOKEN.value} {token}"

        self.headers[AUTHORIZATION_HEADER_NAME] = token

    def _cache_user_info(self):
        """cache customer_id and organization_id - serves as test for successful auth"""
        resp = self.get("/user")
        resp.raise_for_status()

        con = resp.json()
        self.customer_id = con["id"]
        self.organization_id = con["organizationId"]
        self.email = con["email"]

    def _set_api_key_auth_header(self, api_key: Optional[str]):
        assert isinstance(api_key, str)
        api_key = api_key.strip()
        if not api_key.lower().startswith(AuthHeaderPrefix.API_KEY.value.lower()):
            api_key = f"{AuthHeaderPrefix.API_KEY.value} {api_key}"

        self.headers[AUTHORIZATION_HEADER_NAME] = api_key


def _get_auth_method(token: Optional[str], api_key: Optional[str]) -> AuthMethod:
    token_provided = bool(token)
    api_key_provided = bool(api_key)

    if not any((api_key_provided, token_provided)):
        raise ValueError("please provide either api_key or token")

    auth_method = AuthMethod.API_KEY
    if token_provided:
        auth_method = AuthMethod.TOKEN
    return auth_method
