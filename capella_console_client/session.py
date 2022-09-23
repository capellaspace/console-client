import base64
from enum import Enum
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
    BASIC = 1  # email/ password
    TOKEN = 2  # JWT token


class CapellaConsoleSession(httpx.Client):
    def __init__(self, *args, **kwargs):
        verbose = kwargs.pop("verbose", False)
        search_url = kwargs.pop("search_url", None)
        event_hooks = [translate_error_to_exception]
        if verbose:
            event_hooks.insert(0, log_on_4xx_5xx)

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
        no_token_check: bool = False,
    ) -> None:
        try:
            basic_auth_provided = bool(email) and bool(password)
            if not basic_auth_provided and not bool(token):
                email, password = self._prompt_user_creds(email, password)  # type: ignore

            auth_method = self._get_auth_method(email, password, token)
            if auth_method == AuthMethod.BASIC:
                self._basic_auth(email, password)  # type: ignore
            elif auth_method == AuthMethod.TOKEN:
                self._token_auth_check(token, no_token_check)  # type: ignore
        except httpx.HTTPStatusError:
            message = {
                AuthMethod.BASIC: "please check your credentials",
                AuthMethod.TOKEN: "provided token invalid",
            }[auth_method]

            raise AuthenticationError(
                f"Unable to authenticate with {self.base_url} ({auth_method}) - {message}"
            ) from None

        suffix = f"({self.base_url})" if self.base_url != CONSOLE_API_URL else ""
        if auth_method == AuthMethod.TOKEN and no_token_check:
            logger.info(f"successfully authenticated {suffix}")
        else:
            logger.info(f"successfully authenticated as {self.email} {suffix}")

    def _prompt_user_creds(self, email: str, password: str) -> Tuple[str, str]:
        """user credentials on console.capellaspace.com"""
        if not email:
            email = input("user on console.capellaspace.com (user@email.com): ").strip()
        if not password:
            password = getpass("password: ").strip()
        return (email, password)

    def _get_auth_method(self, email: Optional[str], password: Optional[str], token: Optional[str]) -> AuthMethod:
        basic_auth_provided = bool(email) and bool(password)
        has_token = bool(token)

        if not has_token and not basic_auth_provided:
            raise ValueError("please provide either email and password or token")

        if has_token and basic_auth_provided:
            logger.info("both token and email/ password provided ... using email/ password for authentication")

        auth_method = AuthMethod.BASIC
        if not basic_auth_provided:
            auth_method = AuthMethod.TOKEN
        return auth_method

    def _basic_auth(self, email: str, password: str):
        """
        authenticate with Console API

        returns jwt access token
        """
        basic_token = base64.b64encode(f"{email}:{password}".encode()).decode("utf-8")
        resp = self.post("/token", headers={"Authorization": f"Basic {basic_token}"})
        resp.raise_for_status()
        response_body = resp.json()

        self._set_auth_header(response_body["accessToken"])
        self._refresh_token = response_body["refreshToken"]
        self._cache_user_info()

    def _set_auth_header(self, token: str):
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

    def _token_auth_check(self, token: str, no_token_check: bool):
        self._set_auth_header(token)
        if not no_token_check:
            self._cache_user_info()

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
            ret = super().send(*fct_args, **kwargs)
        return ret

    def perform_token_refresh(self):
        if not self._refresh_token:
            raise NoRefreshTokenError("No refresh token found") from None

        resp = self.post("/token/refresh", json={"refreshToken": self._refresh_token})
        con = resp.json()
        self._set_auth_header(con["accessToken"])
        if con["refreshToken"] != self._refresh_token:
            self._refresh_token = con["refreshToken"]
        logger.info("successfully refreshed access token")
