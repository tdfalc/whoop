from abc import ABC
from typing import Any
from datetime import datetime as dt
import requests
import json

from authlib.common.urls import extract_params
from authlib.integrations.requests_client import OAuth2Session
import pytz
import pandas as pd

TOKEN_URL = "https://api-7.whoop.com/oauth/token"
REQUEST_URL = "https://api.prod.whoop.com/developer"


def _oauth_session(token_endpoint_auth_method: str) -> OAuth2Session:
    """Workaround for authentication with username and password."""
    session = OAuth2Session(
        token_endpoint=TOKEN_URL,
        token_endpoint_auth_method=token_endpoint_auth_method,
    )

    def _auth_password_json(_client, _method, uri, headers, body):

        body = json.dumps(dict(extract_params(body)))
        headers["Content-Type"] = "application/json"

        return uri, headers, body

    session.register_client_auth_method(
        (token_endpoint_auth_method, _auth_password_json)
    )
    return session


class BaseClient(ABC):
    def __init__(self, username: str, password: str):
        """Initialize an OAuth2 session for making API requests.

        Args:
            username (str): WHOOP account email.
            password (str): WHOOP account password.
        """
        self._username = username
        self._password = password
        self.session = _oauth_session("password_json")
        self.session.fetch_token(
            url=TOKEN_URL,
            username=self._username,
            password=self._password,
            grant_type="password",
        )
        self.user_id = str(self.session.token.get("user", {}).get("id", ""))

    def _make_request(
        self, method: str, url_slug: str, **kwargs: Any
    ) -> dict[str, Any]:
        url = f"{REQUEST_URL}/{url_slug}"
        try:
            response = self.session.request(method=method, url=url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            raise requests.exceptions.HTTPError(
                f"HTTP error occurred: {http_err}"
            ) from http_err
        except requests.exceptions.RequestException as req_err:
            raise requests.exceptions.RequestException(
                f"Request error occurred: {req_err}"
            ) from req_err

    def _make_paginated_request(
        self, method: str, url_slug: str, **kwargs
    ) -> list[dict[str, Any]]:

        params = kwargs.pop("params", {})
        response_data: list[dict[str, Any]] = []

        while True:
            response = self._make_request(
                method=method,
                url_slug=url_slug,
                params=params,
                **kwargs,
            )

            response_data += response["records"]

            next_token = response.get("next_token")
            if next_token:
                params["nextToken"] = next_token
            else:
                break

        return response_data


class RecoveryClient(BaseClient):
    def __init__(self, username: str, password: str):
        super().__init__(username=username, password=password)

    def get_recovery(self, start_date: dt, end_date: dt) -> list[dict[str, Any]]:
        """Make request to Get Recovery Collection endpoint.

        For more details see: https://developer.whoop.com/api#tag/Recovery
        """

        def _format_date(date: dt):
            if date.tzinfo is None:
                raise ValueError(
                    "Timezone information is required for both start and end dates."
                )
            return date.astimezone(pytz.utc).isoformat().replace("+00:00", "Z")

        response = self._make_paginated_request(
            method="GET",
            url_slug="v1/recovery",
            params={
                "start": _format_date(start_date),
                "end": _format_date(end_date),
                "limit": 25,
            },
        )

        df = pd.DataFrame([r["score"] for r in response])
        df["date_created"] = pd.to_datetime(
            [r["created_at"] for r in response], utc=True
        )
        return df.set_index("date_created").drop("user_calibrating", axis=1)
