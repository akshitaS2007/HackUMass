from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import current_user
from ..models import ConfirmRequest
from ..pipeline import transfer_after_confirmation


router = APIRouter()


@router.post("/confirm/{action_id}")
def confirm(
	action_id: str,
	request: ConfirmRequest,
	user_id: str = Depends(current_user),
) -> dict[str, object]:
	try:
		return transfer_after_confirmation(user_id, action_id, request.approved)
	except ValueError as error:
		raise HTTPException(status_code=400, detail=str(error)) from error
	except RuntimeError as error:
		raise HTTPException(status_code=502, detail=str(error)) from error