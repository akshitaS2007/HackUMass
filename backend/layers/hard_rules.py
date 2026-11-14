from typing import Any

from ..config import POLICY


def evaluate(action: dict[str, Any], account: dict[str, Any], payee: dict[str, Any], daily_spent: float, recent_actions: int) -> dict[str, str]:
	amount = float(action.get("amount", 0))
	if amount <= 0:
		return {"decision": "deny", "reason": "Transfer amounts must be greater than zero."}
	if amount > POLICY["max_transfer"]:
		return {"decision": "deny", "reason": f"The fixed per-transfer cap is ${POLICY['max_transfer']:.0f}."}
	if amount > float(account["balance"]):
		return {"decision": "deny", "reason": "The account does not have enough available balance."}
	if daily_spent + amount > POLICY["daily_limit"]:
		return {"decision": "deny", "reason": f"This would exceed the ${POLICY['daily_limit']:.0f} daily transfer limit."}
	if recent_actions >= POLICY["max_actions_per_minute"]:
		return {"decision": "deny", "reason": "The account has reached its transfer rate limit."}
	if not bool(payee.get("approved", 0)):
		return {"decision": "confirm", "reason": "This saved destination has not been approved before."}
	if amount > POLICY["transfers_above_confirm"]:
		return {"decision": "confirm", "reason": "Transfers above $100 require a human confirmation."}
	return {"decision": "approve", "reason": "The transfer is within the fixed policy limits."}
