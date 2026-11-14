from typing import Any

from .. import db
from ..config import NESSIE_ACCOUNT_MAP, NESSIE_MODE, NESSIE_PAYEE_MAP
from .client import NessieClient, NessieTransferUncertain
from .mock_executor import execute_transfer as execute_mock_transfer


def get_account_snapshot(user_id: str) -> dict[str, Any]:
    if NESSIE_MODE == "mock":
        return db.get_account(user_id) or {}
    source_account_id = NESSIE_ACCOUNT_MAP.get(user_id)
    if not source_account_id:
        raise ValueError("A Nessie source-account mapping is required for this demo user.")
    balance = NessieClient().get_balance(source_account_id)
    return db.sync_account_balance(user_id, balance)


def execute_transfer(user_id: str, payee_id: str, amount: float, memo: str) -> dict[str, Any]:
    if NESSIE_MODE == "mock":
        return execute_mock_transfer(user_id, payee_id, amount, memo)

    source_account_id = NESSIE_ACCOUNT_MAP.get(user_id)
    payee_account_id = NESSIE_PAYEE_MAP.get(payee_id)
    if not source_account_id or not payee_account_id:
        raise ValueError("Live Nessie account mappings are incomplete; nothing was sent.")
    client = NessieClient()
    remote_balance = client.get_balance(source_account_id)
    if amount > remote_balance:
        raise ValueError("The Nessie account does not have enough available balance.")
    db.sync_account_balance(user_id, remote_balance)
    receipt = client.create_transfer(source_account_id, payee_account_id, amount, memo)
    if not receipt.get("_id") and not receipt.get("id"):
        raise NessieTransferUncertain(
            "Nessie did not return a transfer receipt. Check the Nessie transaction history before retrying."
        )
    mirrored = db.perform_transfer(user_id, payee_id, amount, memo)
    mirrored["executor"] = "nessie"
    mirrored["external_transfer_id"] = str(receipt.get("_id", receipt.get("id", "")))[:100]
    return mirrored