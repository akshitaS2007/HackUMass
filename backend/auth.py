import base64
import hashlib
import hmac
import json
import time

from .config import SESSION_SECRET


def issue_token(user_id: str) -> str:
    payload = json.dumps({"sub": user_id, "exp": int(time.time()) + 60 * 60 * 12}, separators=(",", ":")).encode()
    encoded = base64.urlsafe_b64encode(payload).decode().rstrip("=")
    signature = hmac.new(SESSION_SECRET.encode(), encoded.encode(), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


def verify_token(token: str) -> str | None:
    try:
        encoded, supplied_signature = token.split(".", 1)
        expected = hmac.new(SESSION_SECRET.encode(), encoded.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(supplied_signature, expected):
            return None
        payload = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
        if not isinstance(payload.get("sub"), str) or int(payload.get("exp", 0)) <= int(time.time()):
            return None
        return payload["sub"]
    except (ValueError, TypeError, json.JSONDecodeError):
        return None