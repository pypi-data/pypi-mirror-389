import re
from typing import Optional, Dict, Any
from isuvalidation.config import Config
app_config = Config()

def extract_hidden_lt(text):
    pattern = r'<input type="hidden" name="lt" value="(.*?)" />'
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    else:
        return None
    
def extract_hidden_execution(text):
    pattern = r'<input type="hidden" name="execution" value="(.*?)" />'
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    else:
        return None

def build_login_error(code_key: str, extra_detail: Optional[str] = None) -> Dict[str, Any]:
    error_info = app_config.error_codes.get(code_key, {})
    code = error_info.get("code", code_key)
    message = error_info.get("message", "Login error occurred.")
    if extra_detail:
        message = f"{message} {extra_detail}"
    return {
        "success": False,
        "code": code,
        "message": message
    }
