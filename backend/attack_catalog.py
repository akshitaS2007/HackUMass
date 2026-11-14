import json
from pathlib import Path
from typing import Any


ATTACKS_PATH = Path(__file__).resolve().parents[1] / "redteam" / "attacks.json"
ATTACK_CONFIGURATIONS = {
	"no_defenses": {"input_filter": False, "guardian": False, "hard_rules": False, "human_confirm": False},
	"input_filter": {"input_filter": True, "guardian": False, "hard_rules": False, "human_confirm": False},
	"guardian": {"input_filter": True, "guardian": True, "hard_rules": False, "human_confirm": False},
	"hard_rules": {"input_filter": True, "guardian": True, "hard_rules": True, "human_confirm": False},
	"all_defenses": {"input_filter": True, "guardian": True, "hard_rules": True, "human_confirm": True},
}

try:
	with ATTACKS_PATH.open(encoding="utf-8") as attacks_file:
		attack_items: Any = json.load(attacks_file)
except (OSError, json.JSONDecodeError) as error:
	raise RuntimeError(f"Unable to load the benchmark attack catalog at {ATTACKS_PATH}.") from error

if not isinstance(attack_items, list):
	raise RuntimeError("The benchmark attack catalog must be a JSON list.")

ATTACK_CASES: dict[str, dict[str, Any]] = {}
for item in attack_items:
	if (
		not isinstance(item, dict)
		or not isinstance(item.get("id"), str)
		or not isinstance(item.get("category"), str)
		or not isinstance(item.get("messages"), list)
		or not item["messages"]
		or any(not isinstance(message, str) for message in item["messages"])
	):
		raise RuntimeError("Every benchmark case must define an ID, category, and non-empty list of messages.")
	if item["id"] in ATTACK_CASES:
		raise RuntimeError(f"Duplicate benchmark attack ID: {item['id']}.")
	ATTACK_CASES[item["id"]] = {"category": item["category"], "messages": item["messages"]}
