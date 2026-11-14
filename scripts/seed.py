from backend import db


def main() -> None:
	db.init_db()
	users = db.list_users()
	print(f"Sandbox ready: {len(users)} demo users")
	for user in users:
		account = db.get_account(user["id"]) or {}
		print(f"  {user['name']}: {account.get('label')} · ${account.get('balance', 0):,.2f}")
	print("Transfers remain local unless Nessie sandbox mode is explicitly configured.")


if __name__ == "__main__":
	main()
