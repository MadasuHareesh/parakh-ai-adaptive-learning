from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user
from ..models import User
from ..schemas import LoginRequest
from ..security import verify_password, create_access_token, login_throttle

router = APIRouter(tags=["Authentication"])


@router.post("/login")
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    email = data.email.strip().lower()
    throttle_key = f"{email}:{request.client.host if request.client else 'unknown'}"

    if login_throttle.blocked(throttle_key):
        raise HTTPException(status_code=429, detail="Too many failed attempts. Try again later.")

    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(data.password, user.password_hash):
        login_throttle.record_failure(throttle_key)
        raise HTTPException(status_code=401, detail="Invalid email or password")

    login_throttle.clear(throttle_key)
    token = create_access_token(user.id, user.role)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role},
    }


@router.get("/me")
def me(user=Depends(get_current_user)):
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}
