from typing import Any

from pydantic import BaseModel, Field, model_validator


class LoginRequest(BaseModel):
	user_id: str


class ChatRequest(BaseModel):
	message: str = Field(min_length=1, max_length=2000)


class ConfirmRequest(BaseModel):
	approved: bool


class DefenseUpdate(BaseModel):
	input_filter: bool
	guardian: bool
	hard_rules: bool
	human_confirm: bool


class PayeeRequest(BaseModel):
	name: str = Field(min_length=2, max_length=80)
	account_ref: str = Field(min_length=3, max_length=64)


class AttackRequest(BaseModel):
	attack_id: str = Field(min_length=1, max_length=80)
	config: str = Field(default="live", min_length=1, max_length=40)
	message: str | None = Field(default=None, min_length=1, max_length=2000)
	messages: list[str] = Field(default_factory=list, max_length=20)

	@model_validator(mode="after")
	def require_message(self) -> "AttackRequest":
		if not self.message and not self.messages:
			raise ValueError("Provide a message or a non-empty messages list.")
		if any(not item.strip() or len(item) > 2000 for item in self.messages):
			raise ValueError("Each attack message must contain 1 to 2000 characters.")
		return self


class ApiResponse(BaseModel):
	ok: bool = True
	data: dict[str, Any] = Field(default_factory=dict)
