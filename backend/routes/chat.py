from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import current_user
from ..models import ChatRequest
from ..pipeline import process_chat


router = APIRouter()


@router.post("/chat")
def chat(request: ChatRequest, user_id: str = Depends(current_user)) -> dict[str, object]:
	try:
		return process_chat(user_id, request.message)
	except ValueError as error:
		raise HTTPException(status_code=400, detail=str(error)) from error