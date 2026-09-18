from fastapi import Header, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models

def get_current_user(
    x_client_id: str = Header(..., alias="X-Client-Id"),
    db: Session = Depends(get_db),
) -> models.User:
    if not x_client_id or len(x_client_id) < 8:
        raise HTTPException(status_code=400, detail="A valid X-Client-Id header is required")
    user = db.query(models.User).filter(models.User.id == x_client_id).first()
    if not user:
        user = models.User(id=x_client_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
