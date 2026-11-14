from typing import Any


def confirmation_required(hard_decision: str, human_confirm_enabled: bool) -> bool:
	return human_confirm_enabled and hard_decision == "confirm"


def confirmation_summary(action: dict[str, Any], payee: dict[str, Any]) -> str:
	return f"Send ${float(action['amount']):.2f} to {payee['name']}?"
