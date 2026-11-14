from fastapi import APIRouter, Depends, HTTPException

from .. import db
from ..auth import issue_token
from ..config import GEMINI_API_KEY, GEMINI_MODEL, NESSIE_ACCOUNT_MAP, NESSIE_API_KEY, NESSIE_MODE, NESSIE_PAYEE_MAP
from ..dependencies import current_user
from ..models import LoginRequest
from ..nessie.executor import get_account_snapshot


router = APIRouter()


@router.get("/health")
def health() -> dict[str, object]:
	provider = "gemini" if GEMINI_API_KEY else "local"
	return {
		"status": "ok",
		"mode": NESSIE_MODE,
		"ai": {
			"provider": provider,
			"model": GEMINI_MODEL if GEMINI_API_KEY else None,
			"components": {"agent": provider, "guardian": provider, "explainer": provider},
		},
		"nessie": {
			"mode": NESSIE_MODE,
			"configured": NESSIE_MODE == "mock" or bool(NESSIE_API_KEY and NESSIE_ACCOUNT_MAP and NESSIE_PAYEE_MAP),
			"attack_mode_available": NESSIE_MODE == "mock",
			"mapped_users": len(NESSIE_ACCOUNT_MAP),
			"mapped_payees": len(NESSIE_PAYEE_MAP),
		},
	}


@router.get("/users")
def users() -> dict[str, object]:
	return {"users": db.list_users()}


@router.post("/login")
def login(request: LoginRequest) -> dict[str, object]:
	user = db.get_user(request.user_id)
	if user is None:
		raise HTTPException(status_code=404, detail="Unknown demo user.")
	try:
		account = get_account_snapshot(request.user_id)
	except (RuntimeError, ValueError) as error:
		raise HTTPException(status_code=502, detail=str(error)) from error
	return {
		"user": {"id": user["id"], "name": user["name"]},
		"account": account,
		"access_token": issue_token(request.user_id),
	}


@router.get("/account")
def account(user_id: str = Depends(current_user)) -> dict[str, object]:
	try:
		account_snapshot = get_account_snapshot(user_id)
	except (RuntimeError, ValueError) as error:
		raise HTTPException(status_code=502, detail=str(error)) from error
	return {
		"account": account_snapshot,
		"transactions": db.get_transactions(user_id),
		"payees": db.get_payees(user_id),
	}


@router.post("/reset")
def reset(user_id: str = Depends(current_user)) -> dict[str, object]:
	if NESSIE_MODE != "mock":
		raise HTTPException(status_code=409, detail="Reset is mock-only; a local reset cannot reverse a Nessie transfer.")
	return {"account": db.reset_demo(user_id), "message": "Sandbox account restored."}