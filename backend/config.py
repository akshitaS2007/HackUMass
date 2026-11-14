import json
import os
import secrets
from pathlib import Path


def _load_id_map(name: str) -> dict[str, str]:
	try:
		value = json.loads(os.getenv(name, "{}"))
	except json.JSONDecodeError as error:
		raise RuntimeError(f"{name} must be a JSON object of IDs.") from error
	if not isinstance(value, dict) or any(
		not isinstance(key, str) or not key.strip() or not isinstance(item, str) or not item.strip()
		for key, item in value.items()
	):
		raise RuntimeError(f"{name} must be a JSON object of non-empty string IDs.")
	return value


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(BASE_DIR / "demo.db")))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
NESSIE_API_KEY = os.getenv("NESSIE_API_KEY", "")
NESSIE_MODE = os.getenv("NESSIE_MODE", "mock").lower()
NESSIE_BASE_URL = os.getenv("NESSIE_BASE_URL", "http://api.reimaginebanking.com")
NESSIE_ACCOUNT_MAP = _load_id_map("NESSIE_ACCOUNT_MAP")
NESSIE_PAYEE_MAP = _load_id_map("NESSIE_PAYEE_MAP")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
SESSION_SECRET = os.getenv("SESSION_SECRET", secrets.token_urlsafe(32))

POLICY = {
	"max_transfer": 200.0,
	"daily_limit": 500.0,
	"new_payee_requires_approval": True,
	"transfers_above_confirm": 100.0,
	"max_actions_per_minute": 5,
}

if NESSIE_MODE not in {"mock", "nessie"}:
	raise RuntimeError("NESSIE_MODE must be 'mock' or 'nessie'.")
