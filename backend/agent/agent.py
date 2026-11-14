import json
import re
import urllib.error
import urllib.request
from typing import Any

from ..config import GEMINI_API_KEY, GEMINI_MODEL
from .prompts import AGENT_INSTRUCTION


AGENT_TOOLS = [{
	"functionDeclarations": [
		{"name": "get_balance", "description": "Read the current user's available demo balance.", "parameters": {"type": "OBJECT", "properties": {}}},
		{"name": "list_transactions", "description": "Read recent transactions for the current user.", "parameters": {"type": "OBJECT", "properties": {"limit": {"type": "INTEGER", "description": "Maximum number of recent transactions, from 1 to 12."}}}},
		{"name": "list_payees", "description": "List saved payees for the current user.", "parameters": {"type": "OBJECT", "properties": {}}},
		{"name": "transfer", "description": "Propose a transfer to one of the user's saved payees. This does not execute the transfer.", "parameters": {"type": "OBJECT", "properties": {"payee_id": {"type": "STRING"}, "amount": {"type": "NUMBER"}, "memo": {"type": "STRING"}}, "required": ["payee_id", "amount"]}},
		{"name": "add_payee", "description": "Propose adding a payee using details explicitly supplied by the user. This always requires a user confirmation.", "parameters": {"type": "OBJECT", "properties": {"name": {"type": "STRING"}, "account_ref": {"type": "STRING"}}, "required": ["name", "account_ref"]}},
	]
}]


def _local_response(message: str, account: dict[str, Any], payees: list[dict[str, Any]], transactions: list[dict[str, Any]]) -> dict[str, Any]:
	normalized = message.lower().strip()
	if "add payee" in normalized or "save payee" in normalized:
		match = re.search(
			r"(?:add|save)\s+payee\s+(.+?)\s+(?:with\s+)?(?:account|reference|id)\s*[:#]?\s*([A-Za-z0-9-]{3,64})\s*[.!]?\s*$",
			message,
			re.IGNORECASE,
		)
		if match:
			return {
				"reply": f"I can add {match.group(1).strip()} as an unverified payee after you confirm.",
				"action": {"type": "add_payee", "name": match.group(1).strip()[:80], "account_ref": match.group(2)},
			}
		return {"reply": "Please provide the payee name and account reference so I can prepare it for your approval.", "action": None}
	if any(word in normalized for word in ("balance", "how much", "available")):
		return {"reply": f"Your available balance is ${account['balance']:.2f}.", "action": None}
	if "transaction" in normalized or "recent" in normalized:
		recent = ", ".join(row["description"] for row in transactions[:3]) or "no recent activity"
		return {"reply": f"Recent activity includes {recent}.", "action": None}

	amount_match = re.search(r"\$\s?(\d+(?:\.\d{1,2})?)", message)
	if amount_match is None:
		amount_match = re.search(r"(?:send|transfer|pay)\s+(\d+(?:\.\d{1,2})?)\b", normalized)
	if not any(word in normalized for word in ("send", "transfer", "pay")):
		return {"reply": "I can check your balance, review recent activity, or prepare a transfer to a saved payee.", "action": None}
	if amount_match is None:
		return {"reply": "What amount should I prepare?", "action": None}
	amount = float(amount_match.group(1))
	recipient = normalized
	for marker in (" to ", " for "):
		if marker in recipient:
			recipient = recipient.split(marker, 1)[1]
			break
	recipient = re.sub(r"\$?\d+(?:\.\d{1,2})?", "", recipient).strip(" .,!?$")
	recipient = re.sub(r"^(?:my|the)\s+", "", recipient)
	candidates = [payee for payee in payees if recipient and payee["name"].lower() in recipient]
	if not candidates and recipient:
		candidates = [payee for payee in payees if recipient in payee["name"].lower()]
	if not candidates and "electric" in recipient:
		candidates = [payee for payee in payees if "electric" in payee["name"].lower()]
	if not candidates and any(word in recipient for word in ("rent", "landlord", "apartment")):
		candidates = [payee for payee in payees if any(word in payee["name"].lower() for word in ("rent", "housing", "apartment"))]
	if not candidates:
		names = ", ".join(payee["name"] for payee in payees[:4])
		return {"reply": f"I couldn't match that to a saved payee. Available payees include {names}.", "action": None}
	payee = candidates[0]
	return {
		"reply": f"I'll check whether ${amount:.2f} to {payee['name']} is allowed.",
		"action": {"type": "transfer", "payee_id": payee["id"], "amount": amount, "memo": "Requested in chat"},
	}


def propose(message: str, account: dict[str, Any], payees: list[dict[str, Any]], transactions: list[dict[str, Any]]) -> dict[str, Any]:
	if not GEMINI_API_KEY:
		return {**_local_response(message, account, payees, transactions), "source": "local"}
	context = {
		"message": message,
		"account": {"balance": account["balance"]},
		"saved_payees": [{"id": payee["id"], "name": payee["name"], "approved": bool(payee["approved"])} for payee in payees],
		"recent_transactions": transactions[:12],
	}
	body = json.dumps({
		"systemInstruction": {"parts": [{"text": AGENT_INSTRUCTION}]},
		"contents": [{"role": "user", "parts": [{"text": json.dumps(context)}]}],
		"tools": AGENT_TOOLS,
		"toolConfig": {"functionCallingConfig": {"mode": "AUTO"}},
	}).encode()
	url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
	request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
	try:
		with urllib.request.urlopen(request, timeout=10) as response:
			payload = json.loads(response.read())
		parts = payload["candidates"][0]["content"]["parts"]
		function_call = next((part["functionCall"] for part in parts if "functionCall" in part), None)
		if function_call is None:
			reply = next((part["text"] for part in parts if isinstance(part.get("text"), str)), None)
			if reply is None:
				raise ValueError("Invalid agent response schema")
			return {"reply": reply[:1000], "action": None, "source": "gemini"}

		name = function_call.get("name")
		args = function_call.get("args")
		if not isinstance(args, dict):
			raise ValueError("Invalid agent tool arguments")
		if name == "get_balance":
			return {"reply": f"Your available balance is ${account['balance']:.2f}.", "action": None, "source": "gemini"}
		if name == "list_transactions":
			limit = int(args.get("limit", 5))
			if not 1 <= limit <= 12:
				raise ValueError("Invalid transaction list limit")
			recent = ", ".join(row["description"] for row in transactions[:limit]) or "no recent activity"
			return {"reply": f"Recent activity includes {recent}.", "action": None, "source": "gemini"}
		if name == "list_payees":
			names = ", ".join(payee["name"] for payee in payees) or "no saved payees"
			return {"reply": f"Your saved payees are {names}.", "action": None, "source": "gemini"}
		if name == "add_payee":
			payee_name = str(args.get("name", "")).strip()
			account_ref = str(args.get("account_ref", "")).strip()
			if not payee_name or not 3 <= len(account_ref) <= 64:
				raise ValueError("Agent proposed an invalid payee")
			return {
				"reply": f"I can add {payee_name[:80]} as an unverified payee after you confirm.",
				"action": {"type": "add_payee", "name": payee_name[:80], "account_ref": account_ref},
				"source": "gemini",
			}
		if name == "transfer":
			valid_ids = {payee["id"] for payee in payees}
			payee_id = args.get("payee_id")
			amount = float(args.get("amount", 0))
			if payee_id not in valid_ids or not 0 < amount <= 100000:
				raise ValueError("Agent proposed an unsupported action")
			return {
				"reply": f"I'll check whether ${amount:.2f} to {next(payee['name'] for payee in payees if payee['id'] == payee_id)} is allowed.",
				"action": {"type": "transfer", "payee_id": payee_id, "amount": amount, "memo": str(args.get("memo", "Requested in chat"))[:120]},
				"source": "gemini",
			}
		raise ValueError("Agent proposed an unknown tool")
	except (KeyError, ValueError, TypeError, OSError, urllib.error.URLError, StopIteration):
		return {"reply": "I couldn't securely validate that request. Please try again with a saved payee and amount.", "action": None, "source": "fallback"}
