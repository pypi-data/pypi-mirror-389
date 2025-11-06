import requests
from typing import Dict, Any
from requests.exceptions import RequestException
from isuvalidation.config import Config
from isuvalidation.utils import extract_hidden_lt, extract_hidden_execution, build_login_error

app_config = Config()


def check_credentials(username: str, password: str) -> Dict[str, Any]:
    """Validate provided credentials against the configured login endpoint."""
    if not username or not password:
        return build_login_error("missing_credentials")

    payload = {
        "username": username,
        "password": password,
        "_eventId": "submit",
        "submit": "LOGIN",
    }

    try:
        with requests.Session() as session:
            response = session.get(app_config.FENIX_LOGIN_URL)
            lt = extract_hidden_lt(response.text)
            execution = extract_hidden_execution(response.text)

            if lt is None:
                return build_login_error("lt_token_not_found")
            if execution is None:
                return build_login_error("execution_token_not_found")

            payload.update({"lt": lt, "execution": execution})
            login_response = session.post(app_config.FENIX_LOGIN_URL, data=payload)
    except RequestException as exc:
        return build_login_error("network_error", f"({exc})")

    if login_response.status_code != app_config.SUCCESS_LOGIN_STATUS:
        return build_login_error(
            "invalid_status_code",
            f"(received {login_response.status_code})"
        )

    headers = {key.lower(): value for key, value in login_response.headers.items()}
    pragma = headers.get("pragma", "").lower()
    cache_control = headers.get("cache-control", "").lower()
    expires = headers.get("expires", "").lower()

    if (
        pragma == "no-cache"
        or cache_control.startswith("no-cache")
        or expires == "thu, 01 jan 1970 00:00:00 gmt".lower()
    ):
        return build_login_error("invalid_credentials")

    return {"success": True}
