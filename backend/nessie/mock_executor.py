from typing import Any

from .. import db


def execute_transfer(user_id: str, payee_id: str, amount: float, memo: str) -> dict[str, Any]:
    return db.perform_transfer(user_id, payee_id, amount, memo)