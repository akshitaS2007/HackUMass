import argparse
import json
import statistics
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ATTACKS_PATH = ROOT / "redteam" / "attacks.json"
LOOPBACK_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
CONFIGURATIONS = [
    ("no_defenses", {"input_filter": False, "guardian": False, "hard_rules": False, "human_confirm": False}),
    ("input_filter", {"input_filter": True, "guardian": False, "hard_rules": False, "human_confirm": False}),
    ("guardian", {"input_filter": True, "guardian": True, "hard_rules": False, "human_confirm": False}),
    ("hard_rules", {"input_filter": True, "guardian": True, "hard_rules": True, "human_confirm": False}),
    ("all_defenses", {"input_filter": True, "guardian": True, "hard_rules": True, "human_confirm": True}),
]


def request_json(base_url: str, path: str, method: str = "GET", body: dict | None = None, token: str = "") -> dict:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(f"{base_url.rstrip('/')}{path}", data=data, headers=headers, method=method)
    try:
        with LOOPBACK_OPENER.open(request, timeout=30) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")
        raise RuntimeError(f"{method} {path} failed ({error.code}): {detail}") from error


def loopback_base_url(value: str) -> str:
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        raise SystemExit("The harness only runs against http://localhost, 127.0.0.1, or ::1.")
    return value.rstrip("/")


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure guarded transfers against the local demo sandbox only.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--user-id", default="alex", choices=("alex", "jordan"))
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--limit", type=int, default=0, help="Run only the first N attacks (useful for a quick smoke test).")
    parser.add_argument("--output", type=Path, default=ROOT / "redteam" / "results" / "latest.json")
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be at least one")
    base_url = loopback_base_url(args.base_url)
    health = request_json(base_url, "/health")
    if health.get("mode") != "mock":
        raise SystemExit("The automated harness requires NESSIE_MODE=mock; remote transfer mode is not permitted.")
    users = request_json(base_url, "/users").get("users", [])
    if args.user_id not in {user["id"] for user in users}:
        raise SystemExit(f"Demo user {args.user_id!r} is not available on this server.")
    login = request_json(base_url, "/login", "POST", {"user_id": args.user_id})
    token = login["access_token"]
    request_json(base_url, "/scoreboard/reset", "POST", {}, token)
    attacks = json.loads(ATTACKS_PATH.read_text())
    if args.limit:
        attacks = attacks[:args.limit]

    observations = []
    total_runs = len(attacks) * args.repeats * len(CONFIGURATIONS)
    run_number = 0
    for config_name, config in CONFIGURATIONS:
        print(f"\n[{config_name}] {len(attacks)} attacks x {args.repeats} repeats")
        for attack in attacks:
            for repeat in range(1, args.repeats + 1):
                run_number += 1
                request_json(base_url, "/reset", "POST", {}, token)
                request_json(base_url, "/defenses", "POST", config, token)
                result = request_json(
                    base_url,
                    "/attack",
                    "POST",
                    {
                        "attack_id": attack["id"],
                        "config": config_name,
                        "messages": attack["messages"],
                    },
                    token,
                )
                outcome = result["attack_result"]
                observations.append({
                    "config": config_name,
                    "attack_id": attack["id"],
                    "category": attack["category"],
                    "repeat": repeat,
                    "success": outcome["success"],
                    "money_lost": outcome["money_lost"],
                    "data_leaked": outcome["data_leaked"],
                })
                print(f"  {run_number:>3}/{total_runs} {attack['id']:<14} success={str(outcome['success']):<5} lost=${outcome['money_lost']:.2f}")

    grouped = defaultdict(list)
    grouped_categories = defaultdict(list)
    for observation in observations:
        grouped[observation["config"]].append(observation)
        grouped_categories[(observation["config"], observation["category"])].append(observation)
    summary = []
    for config_name, config in CONFIGURATIONS:
        runs = grouped[config_name]
        per_attack = defaultdict(list)
        for run in runs:
            per_attack[run["attack_id"]].append(run)
        success_counts = [sum(run["success"] for run in trials) for trials in per_attack.values()]
        losses = [statistics.mean(run["money_lost"] for run in trials) for trials in per_attack.values()]
        summary.append({
            "config": config_name,
            "attacks": len(per_attack),
            "repeats": args.repeats,
            "success_rate_percent": round(100 * sum(success_counts) / max(1, len(success_counts) * args.repeats), 2),
            "mean_successful_repeats_per_attack": round(statistics.mean(success_counts), 2) if success_counts else 0,
            "mean_money_lost_per_attack": round(statistics.mean(losses), 2) if losses else 0,
            "total_data_leaks": sum(run["data_leaked"] for run in runs),
        })

    category_summary = []
    for (config_name, category), runs in sorted(grouped_categories.items()):
        category_summary.append({
            "config": config_name,
            "category": category,
            "attacks": len({run["attack_id"] for run in runs}),
            "attempts": len(runs),
            "success_rate_percent": round(100 * sum(run["success"] for run in runs) / len(runs), 2),
            "money_lost": round(sum(run["money_lost"] for run in runs), 2),
            "data_leaks": sum(run["data_leaked"] for run in runs),
        })

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "local-sandbox",
        "user_id": args.user_id,
        "source_attacks": str(ATTACKS_PATH.relative_to(ROOT)),
        "summary": summary,
        "category_summary": category_summary,
        "observations": observations,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(f"\nSaved observed results to {args.output}")
    print("\nSummary")
    for row in summary:
        print(f"  {row['config']:<14} {row['success_rate_percent']:>6.2f}% success  mean loss/attack ${row['mean_money_lost_per_attack']:.2f}")
    print("\nCategory outcomes")
    for row in category_summary:
        print(f"  {row['config']:<14} {row['category']:<24} {row['success_rate_percent']:>6.2f}% success  lost ${row['money_lost']:.2f}")


if __name__ == "__main__":
    main()