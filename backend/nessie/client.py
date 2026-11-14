import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from ..config import NESSIE_API_KEY, NESSIE_BASE_URL


ALLOWED_HOSTS = {"api.reimaginebanking.com"}


class NessieTransferUncertain(RuntimeError):
	pass


class NessieClient:
    def __init__(self) -> None:
        parsed = urllib.parse.urlparse(NESSIE_BASE_URL)
        if parsed.scheme not in {"http", "https"} or parsed.hostname not in ALLOWED_HOSTS:
            raise ValueError("Live mode only supports the official api.reimaginebanking.com host.")
        if not NESSIE_API_KEY:
            raise ValueError("NESSIE_API_KEY is required when NESSIE_MODE=nessie.")
        self.base_url = NESSIE_BASE_URL.rstrip("/")

    def _request(self, path: str, method: str = "GET", body: dict[str, Any] | None = None) -> dict[str, Any]:
        query = urllib.parse.urlencode({"key": NESSIE_API_KEY})
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(
            f"{self.base_url}{path}?{query}",
            data=data,
            headers={"Content-Type": "application/json"},
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=12) as response:
                raw = response.read()
            result = json.loads(raw) if raw else {}
        except urllib.error.HTTPError as error:
            if method == "POST" and error.code >= 500:
                raise NessieTransferUncertain(
                    "Nessie could not confirm the transfer result. Check the Nessie transaction history before retrying."
                ) from error
            raise RuntimeError(f"Nessie API rejected the request ({error.code}).") from error
        except (urllib.error.URLError, TimeoutError) as error:
            if method == "POST":
                raise NessieTransferUncertain(
                    "Nessie could not confirm the transfer result. Check the Nessie transaction history before retrying."
                ) from error
            raise RuntimeError("Nessie API could not be reached.") from error
        except json.JSONDecodeError as error:
            if method == "POST":
                raise NessieTransferUncertain(
                    "Nessie returned an unreadable transfer result. Check the Nessie transaction history before retrying."
                ) from error
            raise RuntimeError("Nessie API could not be reached or returned invalid JSON.") from error
        if not isinstance(result, dict):
            if method == "POST":
                raise NessieTransferUncertain(
                    "Nessie returned an unexpected transfer result. Check the Nessie transaction history before retrying."
                )
            raise RuntimeError("Nessie API returned an unexpected response.")
        return result

    def get_balance(self, account_id: str) -> float:
        escaped_id = urllib.parse.quote(account_id, safe="")
        account = self._request(f"/accounts/{escaped_id}")
        try:
            return float(account["balance"])
        except (KeyError, TypeError, ValueError) as error:
            raise RuntimeError("Nessie account response did not contain a valid balance.") from error

    def create_transfer(self, source_account_id: str, payee_account_id: str, amount: float, memo: str) -> dict[str, Any]:
        escaped_id = urllib.parse.quote(source_account_id, safe="")
        return self._request(
            f"/accounts/{escaped_id}/transfers",
            method="POST",
            body={
                "medium": "balance",
                "payee_id": payee_account_id,
                "amount": round(amount, 2),
                "description": memo[:120],
            },
        )