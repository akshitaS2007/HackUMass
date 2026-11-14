AGENT_TOOLS = [{
	"functionDeclarations": [
		{"name": "get_balance", "description": "Read the current user's available demo balance.", "parameters": {"type": "OBJECT", "properties": {}}},
		{"name": "list_transactions", "description": "Read recent transactions for the current user.", "parameters": {"type": "OBJECT", "properties": {"limit": {"type": "INTEGER", "description": "Maximum number of recent transactions, from 1 to 12."}}}},
		{"name": "list_payees", "description": "List saved payees for the current user.", "parameters": {"type": "OBJECT", "properties": {}}},
		{"name": "transfer", "description": "Propose a transfer to one of the user's saved payees. This does not execute the transfer.", "parameters": {"type": "OBJECT", "properties": {"payee_id": {"type": "STRING"}, "amount": {"type": "NUMBER"}, "memo": {"type": "STRING"}}, "required": ["payee_id", "amount"]}},
		{"name": "add_payee", "description": "Propose adding a payee using details explicitly supplied by the user. This always requires a user confirmation.", "parameters": {"type": "OBJECT", "properties": {"name": {"type": "STRING"}, "account_ref": {"type": "STRING"}}, "required": ["name", "account_ref"]}},
	]
}]