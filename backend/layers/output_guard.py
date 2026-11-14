import re


ACCOUNT_PATTERN = re.compile(r"\b(?:\d[ -]?){8,18}\b")
REFERENCE_PATTERN = re.compile(r"\b(?:ACCT|CUST)-\d{4,}\b", re.IGNORECASE)
PROMPT_MARKERS = (
	"you are the helpful assistant for a fictional demo checking account",
	"return json with reply",
)


def sanitize(text: str) -> str:
	safe = REFERENCE_PATTERN.sub("[account reference hidden]", text)
	safe = ACCOUNT_PATTERN.sub("[account number hidden]", safe)
	if len(safe) > 1200:
		safe = safe[:1197] + "..."
	return safe


def contains_sensitive_data(text: str) -> bool:
	lowered = text.lower()
	return bool(REFERENCE_PATTERN.search(text) or ACCOUNT_PATTERN.search(text)) or any(marker in lowered for marker in PROMPT_MARKERS)
