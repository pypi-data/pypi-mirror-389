import os
from dotenv import load_dotenv

class Config:
    load_dotenv()
    FENIX_LOGIN_URL = os.getenv('FENIX_LOGIN_URL')
    SUCCESS_LOGIN_STATUS = int(os.getenv('SUCCESS_LOGIN_STATUS', 200))

    # Centralized error codes for login-related failures to keep messages consistent.
    error_codes = {
        "missing_credentials": {
            "code": "LOGIN_001",
            "message": "Username and/or password were not provided."
        },
        "lt_token_not_found": {
            "code": "LOGIN_002",
            "message": "Unable to extract the lt token from the login page."
        },
        "execution_token_not_found": {
            "code": "LOGIN_003",
            "message": "Unable to extract the execution token from the login page."
        },
        "invalid_status_code": {
            "code": "LOGIN_004",
            "message": "Unexpected response status when submitting login form."
        },
        "invalid_credentials": {
            "code": "LOGIN_005",
            "message": "Invalid username or password."
        },
        "network_error": {
            "code": "LOGIN_006",
            "message": "Network error occurred while attempting to reach the login endpoint."
        }
    }
