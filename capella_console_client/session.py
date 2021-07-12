import base64

import httpx

from capella_console_client.config import DEFAULT_TIMEOUT
from capella_console_client.hooks import log_on_4xx_5xx, translate_error_to_exception


class CapellaConsoleSession(httpx.Client):
    def __init__(self, *args, **kwargs):
        verbose = kwargs.pop("verbose")
        event_hooks = [translate_error_to_exception]
        if verbose:
            event_hooks.insert(0, log_on_4xx_5xx)

        super(CapellaConsoleSession, self).__init__(
            *args,
            event_hooks={"response": event_hooks},
            timeout=DEFAULT_TIMEOUT,
            headers={"Content-Type": "application/json; charset=utf-8",},
            **kwargs,
        )
        self.customer_id = None
        self.organization_id = None

    def basic_auth(self, email: str, password: str):
        """
        authenticate with Console API

        returns jwt access token
        """
        basic_token = base64.b64encode(f"{email}:{password}".encode()).decode("utf-8")
        headers = {"Authorization": f"Basic {basic_token}"}

        with self as session:
            resp = session.post("/token", headers=headers)
        resp.raise_for_status()
        token = resp.json()["accessToken"]
        self._set_auth_header(token)
        self._cache_user_info()

    def _set_auth_header(self, token: str):
        token = token.strip()
        if not token.startswith("Bearer"):
            token = f"Bearer {token}"

        self.headers["Authorization"] = token

    def _cache_user_info(self):
        """cache customer_id and organization_id - serves as test for successful auth"""
        with self as session:
            resp = session.get("/user")
        resp.raise_for_status()

        con = resp.json()
        self.customer_id = con["id"]
        self.organization_id = con["organizationId"]
        self.email = con["email"]

    def token_auth_check(self, token: str, no_token_check: bool):
        self._set_auth_header(token)
        if not no_token_check:
            self._cache_user_info()
