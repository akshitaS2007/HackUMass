from fastapi import APIRouter, Depends

from .. import db
from ..dependencies import current_user


router = APIRouter()


@router.get("/events")
def events(user_id: str = Depends(current_user)) -> dict[str, object]:
	return {"events": db.list_events(user_id)}