import json
import unittest
from unittest.mock import MagicMock, patch

from backend.agent.explainer import explain_decision


class RiskExplainerTests(unittest.TestCase):
	def test_local_mode_uses_the_recorded_policy_reason(self) -> None:
		with patch("backend.agent.explainer.GEMINI_API_KEY", ""):
			result = explain_decision("hard_rules", "deny", "The transfer exceeds the fixed cap.")
		self.assertEqual(result, ("The transfer exceeds the fixed cap.", "local"))

	def test_invalid_gemini_output_falls_back_to_the_policy_reason(self) -> None:
		response = MagicMock()
		response.__enter__.return_value.read.return_value = json.dumps({
			"candidates": [{"content": {"parts": [{"text": "first line\nsecond line"}]}}],
		}).encode()
		with (
			patch("backend.agent.explainer.GEMINI_API_KEY", "test-key"),
			patch("backend.agent.explainer.urllib.request.urlopen", return_value=response),
		):
			result = explain_decision("hard_rules", "deny", "The transfer exceeds the fixed cap.")
		self.assertEqual(result, ("The transfer exceeds the fixed cap.", "fallback"))


if __name__ == "__main__":
	unittest.main()
