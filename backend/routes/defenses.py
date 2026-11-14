from fastapi import APIRouter, Depends, HTTPException

from .. import db
from ..config import NESSIE_MODE, POLICY
from ..dependencies import current_user
from ..models import DefenseUpdate


router = APIRouter()


@router.get("/defenses")
def defenses(user_id: str = Depends(current_user)) -> dict[str, object]:
	locked = ["hard_rules", "human_confirm"] if NESSIE_MODE == "nessie" else []
	return {"defenses": db.get_defenses(user_id), "policy": POLICY, "locked": locked}


@router.post("/defenses")
def update_defenses(request: DefenseUpdate, user_id: str = Depends(current_user)) -> dict[str, object]:
	try:
		return {"defenses": db.set_defenses(user_id, request.model_dump())}
	except ValueError as error:
		raise HTTPException(status_code=409, detail=str(error)) from error