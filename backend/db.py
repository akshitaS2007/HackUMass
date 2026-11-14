import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

from .config import DATABASE_PATH, NESSIE_MODE


DEMO_USERS = [
	("alex", "Alex Morgan", "CUST-1001", "ACCT-1001", 2150.00),
	("jordan", "Jordan Lee", "CUST-1002", "ACCT-1002", 1980.00),
]
PAYEE_SEEDS = [
	("Northstar Electric", "PAYEE-ELECTRIC", 1),
	("Sam Rivera", "PAYEE-SAM", 1),
	("Harbor Apartments", "PAYEE-RENT", 1),
	("Quick Cash LLC", "ATTACKER-001", 0),
	("Northstar Electric", "PAYEE-ELECTRIC-2", 1),
	("Taylor Kim", "PAYEE-TAYLOR", 1),
	("Cedar Grove Housing", "PAYEE-RENT-2", 1),
]


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
	DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
	connection = sqlite3.connect(DATABASE_PATH, timeout=10)
	connection.row_factory = sqlite3.Row
	connection.execute("PRAGMA foreign_keys = ON")
	try:
		yield connection
		connection.commit()
	except Exception:
		connection.rollback()
		raise
	finally:
		connection.close()


def init_db() -> None:
	with connect() as db:
		db.executescript(
			"""
			CREATE TABLE IF NOT EXISTS users (
				id TEXT PRIMARY KEY, name TEXT NOT NULL, customer_id TEXT NOT NULL,
				account_id TEXT NOT NULL UNIQUE
			);
			CREATE TABLE IF NOT EXISTS accounts (
				id TEXT PRIMARY KEY, user_id TEXT, label TEXT NOT NULL,
				balance REAL NOT NULL DEFAULT 0, is_attacker INTEGER NOT NULL DEFAULT 0
			);
			CREATE TABLE IF NOT EXISTS payees (
				id TEXT PRIMARY KEY, user_id TEXT NOT NULL, name TEXT NOT NULL,
				account_ref TEXT NOT NULL, added_at TEXT NOT NULL,
				approved INTEGER NOT NULL DEFAULT 1
			);
			CREATE TABLE IF NOT EXISTS transactions (
				id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
				description TEXT NOT NULL, amount REAL NOT NULL, kind TEXT NOT NULL,
				created_at TEXT NOT NULL
			);
			CREATE TABLE IF NOT EXISTS events (
				id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL,
				user_id TEXT NOT NULL, layer TEXT NOT NULL, event_type TEXT NOT NULL,
				input_summary TEXT NOT NULL, decision TEXT NOT NULL, reason TEXT NOT NULL
			);
			CREATE TABLE IF NOT EXISTS pending_actions (
				id TEXT PRIMARY KEY, user_id TEXT NOT NULL, action_json TEXT NOT NULL,
				status TEXT NOT NULL DEFAULT 'pending', created_at TEXT NOT NULL
			);
			CREATE TABLE IF NOT EXISTS defense_settings (
				user_id TEXT PRIMARY KEY, input_filter INTEGER NOT NULL DEFAULT 1,
				guardian INTEGER NOT NULL DEFAULT 1, hard_rules INTEGER NOT NULL DEFAULT 1,
				human_confirm INTEGER NOT NULL DEFAULT 1
			);
			CREATE TABLE IF NOT EXISTS attack_runs (
				id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
				config TEXT NOT NULL, attack_id TEXT NOT NULL, success INTEGER NOT NULL,
				money_lost REAL NOT NULL, data_leaked INTEGER NOT NULL DEFAULT 0,
				category TEXT NOT NULL DEFAULT 'live',
				created_at TEXT NOT NULL
			);
			"""
		)
		attack_run_columns = {row["name"] for row in db.execute("PRAGMA table_info(attack_runs)")}
		if "category" not in attack_run_columns:
			db.execute("ALTER TABLE attack_runs ADD COLUMN category TEXT NOT NULL DEFAULT 'live'")
		if db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
			now = datetime.now(timezone.utc).isoformat()
			for user_id, name, customer_id, account_id, balance in DEMO_USERS:
				db.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (user_id, name, customer_id, account_id))
				db.execute("INSERT INTO accounts VALUES (?, ?, ?, ?, 0)", (account_id, user_id, "Everyday checking", balance))
				db.execute("INSERT INTO defense_settings (user_id) VALUES (?)", (user_id,))
				for payee_name, account_ref, approved in PAYEE_SEEDS:
					if user_id == "alex" and account_ref.endswith("-2") or user_id == "jordan" and account_ref in {"PAYEE-ELECTRIC", "PAYEE-SAM", "PAYEE-RENT"}:
						continue
					payee_id = f"{user_id}-{account_ref.lower()}"
					db.execute(
						"INSERT INTO payees VALUES (?, ?, ?, ?, ?, ?)",
						(payee_id, user_id, payee_name, account_ref, now, approved),
					)
				merchants = ["Market Street Grocer", "Metro Transit", "Juniper Coffee", "City Books", "Fresh Basket"]
				for index in range(32):
					amount = round(8 + ((index * 17) % 83) + (index % 3) * 0.49, 2)
					when = (datetime.now(timezone.utc) - timedelta(days=index + 1)).isoformat()
					db.execute(
						"INSERT INTO transactions (user_id, description, amount, kind, created_at) VALUES (?, ?, ?, 'purchase', ?)",
						(user_id, merchants[index % len(merchants)], -amount, when),
					)
			db.execute("INSERT OR IGNORE INTO accounts VALUES ('ATTACKER-001', NULL, 'Sandbox destination', 0, 1)")


def _dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
	return dict(row) if row else None


def list_users() -> list[dict[str, Any]]:
	with connect() as db:
		return [dict(row) for row in db.execute("SELECT id, name FROM users ORDER BY name")]


def get_user(user_id: str) -> dict[str, Any] | None:
	with connect() as db:
		return _dict(db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())


def get_account(user_id: str) -> dict[str, Any] | None:
	with connect() as db:
		return _dict(db.execute("SELECT id, label, balance FROM accounts WHERE user_id = ?", (user_id,)).fetchone())


def get_payees(user_id: str, include_unapproved: bool = True) -> list[dict[str, Any]]:
	query = "SELECT id, name, account_ref, added_at, approved FROM payees WHERE user_id = ?"
	if not include_unapproved:
		query += " AND approved = 1"
	with connect() as db:
		return [dict(row) for row in db.execute(query + " ORDER BY name", (user_id,))]


def get_payee(user_id: str, payee_id: str) -> dict[str, Any] | None:
	with connect() as db:
		return _dict(db.execute("SELECT * FROM payees WHERE user_id = ? AND id = ?", (user_id, payee_id)).fetchone())


def get_transactions(user_id: str, limit: int = 12) -> list[dict[str, Any]]:
	with connect() as db:
		rows = db.execute(
			"SELECT id, description, amount, kind, created_at FROM transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
			(user_id, limit),
		)
		return [dict(row) for row in rows]


def get_risk_context(user_id: str, payee_id: str) -> dict[str, int | float]:
	cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
	with connect() as db:
		average = db.execute(
			"SELECT AVG(ABS(amount)) FROM transactions WHERE user_id = ? AND kind IN ('purchase', 'transfer') AND created_at >= ?",
			(user_id, cutoff),
		).fetchone()[0]
		payee = db.execute(
			"SELECT added_at FROM payees WHERE user_id = ? AND id = ?",
			(user_id, payee_id),
		).fetchone()
	if payee is None:
		raise ValueError("The saved payee could not be verified.")
	added_at = datetime.fromisoformat(payee["added_at"])
	if added_at.tzinfo is None:
		added_at = added_at.replace(tzinfo=timezone.utc)
	age_days = max(0, (datetime.now(timezone.utc) - added_at).days)
	return {"avg_transfer": float(average or 0), "age_days": age_days}


def sync_account_balance(user_id: str, balance: float) -> dict[str, Any]:
	if balance < 0:
		raise ValueError("Account balance cannot be negative.")
	with connect() as db:
		db.execute("UPDATE accounts SET balance = ? WHERE user_id = ?", (round(balance, 2), user_id))
	return get_account(user_id) or {}


def get_daily_spent(user_id: str) -> float:
	start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
	with connect() as db:
		row = db.execute(
			"SELECT COALESCE(SUM(-amount), 0) FROM transactions WHERE user_id = ? AND kind = 'transfer' AND created_at >= ?",
			(user_id, start),
		).fetchone()
		return float(row[0])


def count_recent_actions(user_id: str) -> int:
	cutoff = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
	with connect() as db:
		return int(db.execute("SELECT COUNT(*) FROM transactions WHERE user_id = ? AND kind = 'transfer' AND created_at >= ?", (user_id, cutoff)).fetchone()[0])


def record_event(user_id: str, layer: str, event_type: str, input_summary: str, decision: str, reason: str) -> None:
	with connect() as db:
		db.execute(
			"INSERT INTO events (timestamp, user_id, layer, event_type, input_summary, decision, reason) VALUES (?, ?, ?, ?, ?, ?, ?)",
			(datetime.now(timezone.utc).isoformat(), user_id, layer, event_type, input_summary[:180], decision, reason[:300]),
		)


def list_events(user_id: str, limit: int = 100) -> list[dict[str, Any]]:
	with connect() as db:
		rows = db.execute("SELECT * FROM events WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit))
		return [dict(row) for row in rows]


def get_defenses(user_id: str) -> dict[str, bool]:
	with connect() as db:
		row = db.execute("SELECT input_filter, guardian, hard_rules, human_confirm FROM defense_settings WHERE user_id = ?", (user_id,)).fetchone()
		if row is None:
			db.execute("INSERT OR IGNORE INTO defense_settings (user_id) VALUES (?)", (user_id,))
			return {"input_filter": True, "guardian": True, "hard_rules": True, "human_confirm": True}
		values = {key: bool(row[key]) for key in row.keys()}
	if NESSIE_MODE == "nessie":
		values["hard_rules"] = True
		values["human_confirm"] = True
	return values


def set_defenses(user_id: str, values: dict[str, bool]) -> dict[str, bool]:
	if NESSIE_MODE == "nessie" and (not values["hard_rules"] or not values["human_confirm"]):
		raise ValueError("Hard rules and human confirmation cannot be disabled in Nessie mode.")
	with connect() as db:
		db.execute(
			"INSERT INTO defense_settings VALUES (?, ?, ?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET input_filter=excluded.input_filter, guardian=excluded.guardian, hard_rules=excluded.hard_rules, human_confirm=excluded.human_confirm",
			(user_id, *(int(values[key]) for key in ("input_filter", "guardian", "hard_rules", "human_confirm"))),
		)
	return get_defenses(user_id)


def create_pending(user_id: str, action: dict[str, Any]) -> str:
	import uuid

	pending_id = uuid.uuid4().hex[:12]
	with connect() as db:
		db.execute("INSERT INTO pending_actions VALUES (?, ?, ?, 'pending', ?)", (pending_id, user_id, json.dumps(action), datetime.now(timezone.utc).isoformat()))
	return pending_id


def get_pending(user_id: str, pending_id: str) -> dict[str, Any] | None:
	with connect() as db:
		row = db.execute("SELECT * FROM pending_actions WHERE user_id = ? AND id = ?", (user_id, pending_id)).fetchone()
	if row is None:
		return None
	result = dict(row)
	result["action"] = json.loads(result.pop("action_json"))
	return result


def mark_pending(user_id: str, pending_id: str, status: str) -> None:
	with connect() as db:
		db.execute(
			"UPDATE pending_actions SET status = ? WHERE user_id = ? AND id = ? AND status IN ('pending', 'processing')",
			(status, user_id, pending_id),
		)


def claim_pending(user_id: str, pending_id: str) -> bool:
	with connect() as db:
		cursor = db.execute(
			"UPDATE pending_actions SET status = 'processing' WHERE user_id = ? AND id = ? AND status = 'pending'",
			(user_id, pending_id),
		)
		return cursor.rowcount == 1


def perform_transfer(user_id: str, payee_id: str, amount: float, memo: str) -> dict[str, Any]:
	now = datetime.now(timezone.utc).isoformat()
	with connect() as db:
		db.execute("BEGIN IMMEDIATE")
		user = db.execute("SELECT account_id FROM users WHERE id = ?", (user_id,)).fetchone()
		payee = db.execute("SELECT name, account_ref, approved FROM payees WHERE user_id = ? AND id = ?", (user_id, payee_id)).fetchone()
		if user is None or payee is None:
			raise ValueError("The account or saved payee could not be verified.")
		account = db.execute("SELECT balance FROM accounts WHERE id = ? AND user_id = ?", (user["account_id"], user_id)).fetchone()
		if account is None or amount <= 0 or account["balance"] < amount:
			raise ValueError("Insufficient funds or invalid transfer amount.")
		db.execute("UPDATE accounts SET balance = balance - ? WHERE id = ? AND user_id = ?", (amount, user["account_id"], user_id))
		db.execute("UPDATE accounts SET balance = balance + ? WHERE id = ? AND is_attacker = 1", (amount, payee["account_ref"]))
		db.execute(
			"INSERT INTO transactions (user_id, description, amount, kind, created_at) VALUES (?, ?, ?, 'transfer', ?)",
			(user_id, f"Transfer to {payee['name']}: {memo}".strip(": "), -amount, now),
		)
		return {
			"amount": amount,
			"payee": payee["name"],
			"balance": account["balance"] - amount,
			"created_at": now,
			"approved_destination": bool(payee["approved"]),
			"attacker_destination": payee["account_ref"] == "ATTACKER-001",
		}


def create_payee(user_id: str, name: str, account_ref: str, approved: bool = False) -> str:
	import uuid

	payee_id = f"{user_id}-{uuid.uuid4().hex[:8]}"
	with connect() as db:
		db.execute("INSERT INTO payees VALUES (?, ?, ?, ?, ?, ?)", (payee_id, user_id, name, account_ref, datetime.now(timezone.utc).isoformat(), int(approved)))
	return payee_id


def reset_demo(user_id: str) -> dict[str, Any]:
	if NESSIE_MODE != "mock":
		raise ValueError("The local reset is available only in mock mode; it cannot reverse Nessie transfers.")
	with connect() as db:
		db.execute("BEGIN IMMEDIATE")
		account_id = db.execute("SELECT account_id FROM users WHERE id = ?", (user_id,)).fetchone()
		if account_id is None:
			raise ValueError("Unknown demo user.")
		starting_balance = next(user[4] for user in DEMO_USERS if user[0] == user_id)
		db.execute("UPDATE accounts SET balance = ? WHERE id = ?", (starting_balance, account_id[0]))
		db.execute("DELETE FROM transactions WHERE user_id = ? AND kind = 'transfer'", (user_id,))
		db.execute("UPDATE pending_actions SET status = 'expired' WHERE user_id = ? AND status = 'pending'", (user_id,))
		db.execute("UPDATE accounts SET balance = 0 WHERE is_attacker = 1")
	record_event(user_id, "system", "reset", "Demo account reset", "complete", "Sandbox balance and pending actions restored.")
	return get_account(user_id) or {}


def record_attack_run(
	user_id: str,
	config: str,
	attack_id: str,
	success: bool,
	money_lost: float,
	data_leaked: bool = False,
	category: str = "live",
) -> None:
	with connect() as db:
		db.execute(
			"INSERT INTO attack_runs (user_id, config, attack_id, success, money_lost, data_leaked, category, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
			(user_id, config, attack_id, int(success), money_lost, int(data_leaked), category, datetime.now(timezone.utc).isoformat()),
		)


def get_scoreboard(user_id: str) -> list[dict[str, Any]]:
	with connect() as db:
		rows = db.execute(
			"SELECT config, COUNT(*) AS total, SUM(success) AS successes, SUM(money_lost) AS money_lost FROM attack_runs WHERE user_id = ? GROUP BY config ORDER BY MIN(id)",
			(user_id,),
		)
		return [dict(row) for row in rows]


def get_scoreboard_categories(user_id: str) -> list[dict[str, Any]]:
	with connect() as db:
		rows = db.execute(
			"SELECT config, category, COUNT(*) AS total, SUM(success) AS successes, SUM(money_lost) AS money_lost, SUM(data_leaked) AS data_leaks FROM attack_runs WHERE user_id = ? GROUP BY config, category ORDER BY config, category",
			(user_id,),
		)
		return [dict(row) for row in rows]


def clear_scoreboard(user_id: str) -> None:
	with connect() as db:
		db.execute("DELETE FROM attack_runs WHERE user_id = ?", (user_id,))
