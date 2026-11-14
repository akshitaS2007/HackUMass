from typing import Any

from . import db
from .agent.agent import propose
from .agent.explainer import explain_decision
from .config import NESSIE_MODE
from .defenses import confirmation_required, evaluate, inspect_message, review, sanitize
from .nessie.client import NessieTransferUncertain
from .nessie.executor import execute_transfer


def process_chat(user_id: str, message: str) -> dict[str, Any]:
	user = db.get_user(user_id)
	account = db.get_account(user_id)
	if user is None or account is None:
		raise ValueError("Unknown demo user.")
	defenses = db.get_defenses(user_id)
	trace: list[dict[str, str]] = []

	def safe_reply(text: str) -> str:
		safe = sanitize(text)
		altered = safe != text
		db.record_event(
			user_id,
			"output_guard",
			"scan",
			"Assistant response",
			"filtered" if altered else "passed",
			"Sensitive account-like references were masked." if altered else "No account-like references exposed.",
		)
		return safe

	def stage(layer: str, decision: str, reason: str, source: str | None = None) -> None:
		trace_step = {"layer": layer, "decision": decision, "reason": reason}
		audit_reason = reason
		if source:
			trace_step["source"] = source
			audit_reason = f"{reason} (source: {source})"
		trace.append(trace_step)
		db.record_event(user_id, layer, "review", message[:100], decision, audit_reason)

	def explain_block(layer: str, reason: str) -> str:
		explanation, source = explain_decision(layer, "deny", reason)
		db.record_event(user_id, "explainer", "explain", layer, source, "Prepared a plain-language explanation of the policy decision.")
		return safe_reply(explanation)

	if defenses["input_filter"]:
		reason = inspect_message(message)
		if reason:
			stage("input_filter", "blocked", reason)
			return {"reply": safe_reply("I couldn't process that request because it resembles an instruction override."), "pipeline": trace, "account": db.get_account(user_id)}
	stage("input_filter", "passed", "No known override pattern found." if defenses["input_filter"] else "Layer disabled.")

	payees = db.get_payees(user_id)
	proposal = propose(message, account, payees, db.get_transactions(user_id))
	action = proposal.get("action")
	if not action:
		stage("agent", "no_action", "The agent answered without proposing a financial action.", proposal.get("source"))
		return {"reply": safe_reply(proposal.get("reply", "How can I help?")), "pipeline": trace, "account": db.get_account(user_id)}
	stage("agent", "proposed", f"Proposed {action.get('type')} for ${float(action.get('amount', 0)):.2f}.", proposal.get("source"))

	if action.get("type") == "add_payee":
		if NESSIE_MODE == "nessie":
			reason = "Adding payees is disabled in Nessie mode. Configure and verify the destination mapping first."
			stage("executor", "denied", reason)
			return {"reply": safe_reply(reason), "pipeline": trace, "account": db.get_account(user_id)}
		name = str(action.get("name", "")).strip()
		account_ref = str(action.get("account_ref", "")).strip()
		if not name or not 3 <= len(account_ref) <= 64:
			stage("executor", "denied", "The proposed payee details could not be validated.")
			return {"reply": safe_reply("I couldn't validate those payee details, so nothing was added."), "pipeline": trace, "account": db.get_account(user_id)}
		pending_id = db.create_pending(user_id, {"type": "add_payee", "name": name[:80], "account_ref": account_ref})
		reason = "Adding a destination always requires a separate user confirmation."
		stage("human_confirm", "required", reason)
		return {
			"reply": safe_reply(f"{proposal.get('reply', 'Payee prepared')} This destination is waiting for your confirmation."),
			"pending_action": {"id": pending_id, "type": "add_payee", "name": name[:80], "account_ref": account_ref, "reason": reason},
			"pipeline": trace,
			"account": db.get_account(user_id),
		}

	payee = db.get_payee(user_id, str(action.get("payee_id", "")))
	if action.get("type") != "transfer" or payee is None:
		stage("executor", "denied", "The proposal does not identify a payee owned by this session.")
		return {"reply": safe_reply("I couldn't verify that saved destination, so nothing was sent."), "pipeline": trace, "account": db.get_account(user_id)}

	if defenses["guardian"]:
		risk_context = db.get_risk_context(user_id, payee["id"])
		guardian_result = review({
			"action": {"type": "transfer", "amount": action["amount"]},
			"payee": {"name": payee["name"], "approved": bool(payee["approved"]), "age_days": risk_context["age_days"]},
			"user_context": {
				"balance": account["balance"],
				"daily_spent_so_far": db.get_daily_spent(user_id),
				"avg_transfer": risk_context["avg_transfer"],
			},
		})
		decision = guardian_result["decision"]
		stage("guardian", decision, guardian_result["reason"], guardian_result.get("source"))
		if decision == "deny":
			return {"reply": explain_block("guardian", "The independent risk review stopped this transfer. " + guardian_result['reason']), "pipeline": trace, "account": db.get_account(user_id)}
		guardian_escalated = decision == "escalate"
		if guardian_escalated:
			action["review_reason"] = guardian_result["reason"]
	else:
		guardian_escalated = False
		stage("guardian", "skipped", "Layer disabled.")

	if defenses["hard_rules"]:
		hard_result = evaluate(action, account, payee, db.get_daily_spent(user_id), db.count_recent_actions(user_id))
		stage("hard_rules", hard_result["decision"], hard_result["reason"])
		if hard_result["decision"] == "deny":
			return {"reply": explain_block("hard_rules", "The transfer was stopped by a fixed account rule. " + hard_result["reason"]), "pipeline": trace, "account": db.get_account(user_id)}
	else:
		hard_result = {"decision": "approve", "reason": "Layer disabled."}
		stage("hard_rules", "skipped", "Layer disabled.")

	confirmation_required_by_policy = hard_result["decision"] == "confirm" or guardian_escalated
	if confirmation_required_by_policy and not defenses["human_confirm"]:
		reason = "This action requires human confirmation, but that layer is disabled; the transfer was stopped."
		stage("human_confirm", "blocked", reason)
		return {"reply": explain_block("human_confirm", reason), "pipeline": trace, "account": db.get_account(user_id)}
	needs_confirmation = (
		NESSIE_MODE == "nessie"
		or confirmation_required(hard_result["decision"], defenses["human_confirm"])
		or guardian_escalated
	)
	if needs_confirmation:
		pending_id = db.create_pending(user_id, action)
		confirmation_reason = hard_result["reason"]
		if NESSIE_MODE == "nessie":
			confirmation_reason = "Nessie sandbox transfers always require explicit approval. " + confirmation_reason
		stage("human_confirm", "required", confirmation_reason)
		return {
			"reply": safe_reply(f"{proposal.get('reply', 'Transfer prepared')} This transfer is waiting for your confirmation."),
			"pending_action": {"id": pending_id, "payee": payee["name"], "amount": float(action["amount"]), "reason": confirmation_reason},
			"pipeline": trace,
			"account": db.get_account(user_id),
		}
	stage("human_confirm", "skipped", "No confirmation is required or the layer is disabled.")

	try:
		result = execute_transfer(user_id, payee["id"], float(action["amount"]), str(action.get("memo", "")))
	except ValueError as error:
		stage("executor", "denied", str(error))
		return {"reply": explain_block("executor", "Nothing was sent. " + str(error)), "pipeline": trace, "account": db.get_account(user_id)}
	except RuntimeError as error:
		stage("executor", "failed", str(error))
		return {"reply": safe_reply(f"I couldn't complete the Nessie request. {error}"), "pipeline": trace, "account": db.get_account(user_id)}
	stage("executor", "executed", f"Sandbox transfer of ${result['amount']:.2f} to {result['payee']} completed.")
	return {"reply": safe_reply(f"Transfer complete: ${result['amount']:.2f} to {result['payee']}."), "transfer": result, "pipeline": trace, "account": db.get_account(user_id)}


def transfer_after_confirmation(user_id: str, pending_id: str, approved: bool) -> dict[str, Any]:
	pending = db.get_pending(user_id, pending_id)
	if pending is None or pending["status"] != "pending":
		raise ValueError("This confirmation has expired or does not belong to this session.")
	if not db.claim_pending(user_id, pending_id):
		raise ValueError("This confirmation has expired or is already being processed.")
	action = pending["action"]
	if action.get("type") == "add_payee":
		if NESSIE_MODE == "nessie":
			db.mark_pending(user_id, pending_id, "denied")
			raise ValueError("Adding payees is disabled in Nessie mode. Configure and verify the destination mapping first.")
		if not approved:
			db.mark_pending(user_id, pending_id, "cancelled")
			db.record_event(user_id, "human_confirm", "cancelled", "Add payee", "cancelled", "The user cancelled adding this payee.")
			return {"approved": False, "reply": "Payee addition cancelled."}
		payee_id = db.create_payee(user_id, str(action["name"]), str(action["account_ref"]), approved=False)
		db.mark_pending(user_id, pending_id, "approved")
		db.record_event(user_id, "human_confirm", "approved", "Add payee", "approved", "The user approved adding an untrusted destination.")
		return {"approved": True, "reply": "Payee added. Transfers to this destination will still require approval.", "payee": {"id": payee_id, "name": action["name"], "approved": False}}
	payee = db.get_payee(user_id, action.get("payee_id", ""))
	if not approved:
		db.mark_pending(user_id, pending_id, "cancelled")
		db.record_event(user_id, "human_confirm", "cancelled", "Pending transfer", "cancelled", "The user cancelled the action.")
		return {"approved": False, "reply": "Transfer cancelled.", "account": db.get_account(user_id)}
	if payee is None:
		db.mark_pending(user_id, pending_id, "denied")
		raise ValueError("The saved destination could not be verified.")
	account = db.get_account(user_id) or {}
	if db.get_defenses(user_id)["hard_rules"]:
		result = evaluate(action, account, payee, db.get_daily_spent(user_id), db.count_recent_actions(user_id))
		if result["decision"] == "deny":
			db.mark_pending(user_id, pending_id, "denied")
			raise ValueError(result["reason"])
	try:
		transfer = execute_transfer(user_id, payee["id"], float(action["amount"]), str(action.get("memo", "")))
	except NessieTransferUncertain as error:
		db.mark_pending(user_id, pending_id, "uncertain")
		db.record_event(user_id, "executor", "uncertain", "Confirmed transfer", "uncertain", str(error))
		raise
	except RuntimeError as error:
		db.mark_pending(user_id, pending_id, "failed")
		db.record_event(user_id, "executor", "failed", "Confirmed transfer", "failed", str(error))
		raise
	except ValueError:
		db.mark_pending(user_id, pending_id, "denied")
		raise
	db.mark_pending(user_id, pending_id, "approved")
	db.record_event(user_id, "human_confirm", "approved", "Pending transfer", "approved", "The user confirmed the transfer.")
	db.record_event(user_id, "executor", "executed", "Confirmed transfer", "executed", f"Sandbox transfer of ${transfer['amount']:.2f} to {transfer['payee']}.")
	return {"approved": True, "reply": "Transfer sent.", "transfer": transfer, "account": db.get_account(user_id)}
