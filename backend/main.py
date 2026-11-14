from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import db
from .attack_catalog import ATTACK_CONFIGURATIONS
from .config import ALLOWED_ORIGINS, NESSIE_MODE
from .dependencies import current_user
from .models import AttackRequest, DefenseUpdate
from .routes.admin import account, health, login, reset as _reset, router as admin_router, users
from .routes.attack import attack as _attack, router as attack_router
from .routes.chat import chat, router as chat_router
from .routes.confirm import confirm, router as confirm_router
from .routes.defenses import defenses as _defenses, router as defenses_router, update_defenses as _update_defenses
from .routes.events import events, router as events_router
from .routes.scoreboard import reset_scoreboard, router as scoreboard_router, scoreboard


app = FastAPI(title="Break the Bank", version="1.0.0")
app.add_middleware(
	CORSMiddleware,
	allow_origins=ALLOWED_ORIGINS,
	allow_credentials=True,
	allow_methods=["GET", "POST", "OPTIONS"],
	allow_headers=["Content-Type", "Authorization"],
)

for router in (
	admin_router,
	attack_router,
	chat_router,
	confirm_router,
	defenses_router,
	events_router,
	scoreboard_router,
):
	app.include_router(router)

db.init_db()


def attack(request: AttackRequest, user_id: str) -> dict[str, object]:
	if NESSIE_MODE != "mock":
		raise HTTPException(status_code=409, detail="Attack Mode is restricted to the reversible mock sandbox.")
	return _attack(request, user_id)


def reset(user_id: str) -> dict[str, object]:
	if NESSIE_MODE != "mock":
		raise HTTPException(status_code=409, detail="Reset is mock-only; a local reset cannot reverse a Nessie transfer.")
	return _reset(user_id)


def defenses(user_id: str) -> dict[str, object]:
	result = _defenses(user_id)
	if NESSIE_MODE == "nessie":
		result["locked"] = ["hard_rules", "human_confirm"]
	return result


def update_defenses(request: DefenseUpdate, user_id: str) -> dict[str, object]:
	if NESSIE_MODE == "nessie" and (not request.hard_rules or not request.human_confirm):
		raise HTTPException(status_code=409, detail="Hard rules and human confirmation cannot be disabled in Nessie mode.")
	return _update_defenses(request, user_id)
