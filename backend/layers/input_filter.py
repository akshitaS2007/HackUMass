import re


INJECTION_PATTERNS = (
	r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|rules)",
	r"system\s+prompt",
	r"you\s+are\s+now",
	r"admin\s+override",
	r"developer\s+mode",
	r"bypass\s+(the\s+)?(security|approval|rules)",
	r"disable\s+(all\s+)?(safety|security|defenses)",
)


def inspect_message(message: str) -> str | None:
	normalized = " ".join(message.lower().split())
	if any(re.search(pattern, normalized) for pattern in INJECTION_PATTERNS):
		return "The message contains an instruction override pattern."
	return None
