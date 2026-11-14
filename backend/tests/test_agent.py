import json
import unittest
from unittest.mock import MagicMock, patch

from backend.agent.agent import propose


class GeminiAgentTests(unittest.TestCase):
	def setUp(self) -> None:
		self.account = {"balance": 2150.0}
		self.payees = [{"id": "alex-electric", "name": "Northstar Electric", "approved": True}]

	def call_agent(self, payee_id: str) -> tuple[dict, MagicMock]:
		payload = {
			"candidates": [{
				"content": {
					"parts": [{
						"functionCall": {
							"name": "transfer",
							"args": {"payee_id": payee_id, "amount": 80, "memo": "Electric bill"},
						},
					}],
				},
			}],
		}
		response = MagicMock()
		response.__enter__.return_value.read.return_value = json.dumps(payload).encode()
		with (
			patch("backend.agent.agent.GEMINI_API_KEY", "test-key"),
			patch("backend.agent.agent.urllib.request.urlopen", return_value=response) as urlopen,
		):
			result = propose("Pay my electric bill $80", self.account, self.payees, [])
		return result, urlopen

	def test_function_call_is_validated_and_returned_as_a_proposal(self) -> None:
		result, urlopen = self.call_agent("alex-electric")
		self.assertEqual(result["action"], {
			"type": "transfer",
			"payee_id": "alex-electric",
			"amount": 80.0,
			"memo": "Electric bill",
		})
		request_body = json.loads(urlopen.call_args.args[0].data)
		self.assertEqual(request_body["toolConfig"]["functionCallingConfig"]["mode"], "AUTO")
		self.assertIn("transfer", [tool["name"] for tool in request_body["tools"][0]["functionDeclarations"]])

	def test_function_call_cannot_name_another_users_payee(self) -> None:
		result, _ = self.call_agent("someone-elses-payee")
		self.assertIsNone(result["action"])
		self.assertIn("couldn't securely validate", result["reply"])


if __name__ == "__main__":
	unittest.main()
