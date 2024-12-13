import base64
from enum import Enum
import warnings
from getpass import getpass

from typing import Optional, Tuple

import httpx

from capella_console_client.config import DEFAULT_TIMEOUT, CONSOLE_API_URL
from capella_console_client.hooks import log_on_4xx_5xx, translate_error_to_exception
from capella_console_client.logconf import logger
from capella_console_client.exceptions import (
    CapellaConsoleClientError,
    AuthenticationError,
    INVALID_TOKEN_ERROR_CODE,
    NoRefreshTokenError,
)
from capella_console_client.version import __version__


class AuthMethod(Enum):
    BASIC = 1  # email/ password - TO BE DEPRECATED
    TOKEN = 2  # JWT token
    API_KEY = 3  # API key


class AuthMethodDeprecationWarning(DeprecationWarning):
    pass


BASIC_AUTH_DEPRECATION_MSG = "BASIC auth (email, password) is going to be deprecated in 2025"


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
        self._refresh_token = None

    def authenticate(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
        api_key: Optional[str] = None,
        no_token_check: bool = False,
    ) -> None:
        try:
            basic_auth_provided = bool(email) and bool(password)
            if not basic_auth_provided and not bool(token) and not bool(api_key):
                email, password = self._prompt_user_creds(email, password)

            auth_method = _get_auth_method(email, password, token, api_key)

            if auth_method == AuthMethod.BASIC:
                self._basic_auth(email, password)
                return
            if auth_method == AuthMethod.API_KEY:
                self._set_api_key_auth_header(api_key)
            if auth_method == AuthMethod.TOKEN:
                self._set_bearer_auth_header(token)

            if not no_token_check:
                self._cache_user_info()

        except (httpx.HTTPStatusError, CapellaConsoleClientError):
            message = {
                AuthMethod.BASIC: "please check your credentials",
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

    def _prompt_user_creds(self, email: Optional[str], password: Optional[str]) -> Tuple[str, str]:
        """user credentials on console"""
        warnings.warn(
            message=BASIC_AUTH_DEPRECATION_MSG,
            category=AuthMethodDeprecationWarning,
            stacklevel=2,
        )
        if not email:
            email = input(f"user on {self.base_url} (user@email.com): ").strip()
        if not password:
            password = getpass("password: ").strip()
        return (email, password)

    def _basic_auth(self, email: Optional[str], password: Optional[str]):
        """
        authenticate with Console API

        returns jwt access token
        """
        warnings.warn(
            message=BASIC_AUTH_DEPRECATION_MSG,
            category=AuthMethodDeprecationWarning,
            stacklevel=2,
        )
        assert isinstance(email, str)
        assert isinstance(password, str)

        basic_token = base64.b64encode(f"{email}:{password}".encode()).decode("utf-8")
        resp = self.post("/token", headers={"Authorization": f"Basic {basic_token}"})
        resp.raise_for_status()
        response_body = resp.json()

        self._set_bearer_auth_header(response_body["accessToken"])
        self._refresh_token = response_body["refreshToken"]
        self._cache_user_info()

    def _set_bearer_auth_header(self, token: Optional[str]):
        assert isinstance(token, str)
        token = token.strip()
        if not token.startswith("Bearer"):
            token = f"Bearer {token}"

        self.headers["Authorization"] = token

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
        if not api_key.startswith("Apikey"):
            api_key = f"Apikey {api_key}"

        self.headers["Authorization"] = api_key

    def send(self, *fct_args, **kwargs):
        """wrap httpx.Client.send for auto token_refresh"""
        try:
            ret = super().send(*fct_args, **kwargs)
        except AuthenticationError as e:
            # safeguard in case AuthenticationError get's improperly re-used
            if e.code != INVALID_TOKEN_ERROR_CODE:
                raise e

            self.perform_token_refresh()

            # retry request
            orig_request = fct_args[0]
            orig_request.headers["authorization"] = self.headers["authorization"]
            logger.info(f"retrying {fct_args[0]}")
            ret = super().send(*fct_args, **kwargs)
        return ret

    def perform_token_refresh(self):
        if not self._refresh_token:
            raise NoRefreshTokenError("No refresh token found") from None

        resp = self.post("/token/refresh", json={"refreshToken": self._refresh_token})
        con = resp.json()
        self._set_bearer_auth_header(con["accessToken"])
        if con["refreshToken"] != self._refresh_token:
            self._refresh_token = con["refreshToken"]
        logger.info("successfully refreshed access token")


def _get_auth_method(
    email: Optional[str], password: Optional[str], token: Optional[str], api_key: Optional[str]
) -> AuthMethod:
    basic_auth_provided = bool(email) and bool(password)
    token_provided = bool(token)
    api_key_provided = bool(api_key)

    if not any((api_key_provided, token_provided, basic_auth_provided)):
        raise ValueError("please provide either api_key, token or email and password")

    if token_provided and basic_auth_provided:
        logger.info("both token and email/ password provided ... using email/ password for authentication")

    auth_method = AuthMethod.API_KEY
    if basic_auth_provided:
        auth_method = AuthMethod.BASIC
    elif token_provided:
        auth_method = AuthMethod.TOKEN
    return auth_method
