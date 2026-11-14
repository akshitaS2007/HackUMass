from fastapi import Header, HTTPException

from . import db
from .auth import verify_token


def current_user(authorization: str = Header(default="")) -> str:
	token = authorization.removeprefix("Bearer ") if authorization.startswith("Bearer ") else ""
	user_id = verify_token(token) if token else None
	if not user_id or db.get_user(user_id) is None:
		raise HTTPException(status_code=401, detail="Choose a demo user first.")
	return user_id
