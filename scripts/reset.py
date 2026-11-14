import argparse

from backend import db


def main() -> None:
	parser = argparse.ArgumentParser(description="Restore one or all local demo accounts.")
	parser.add_argument("--user", choices=("alex", "jordan"), help="Reset only this user; defaults to both demo users.")
	args = parser.parse_args()
	db.init_db()
	user_ids = [args.user] if args.user else [user["id"] for user in db.list_users()]
	for user_id in user_ids:
		account = db.reset_demo(user_id)
		print(f"Reset {user_id}: ${account['balance']:,.2f}")


if __name__ == "__main__":
	main()
