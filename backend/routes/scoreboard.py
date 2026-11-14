from fastapi import APIRouter, Depends

from .. import db
from ..dependencies import current_user


router = APIRouter()


@router.get("/scoreboard")
def scoreboard(user_id: str = Depends(current_user)) -> dict[str, object]:
	return {"results": db.get_scoreboard(user_id), "categories": db.get_scoreboard_categories(user_id)}


@router.post("/scoreboard/reset")
def reset_scoreboard(user_id: str = Depends(current_user)) -> dict[str, str]:
	db.clear_scoreboard(user_id)
	return {"message": "Previous attack measurements cleared for this demo user."}