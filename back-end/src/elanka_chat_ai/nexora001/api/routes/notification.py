from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel
from nexora001.api.dependencies import get_storage, get_current_user
from nexora001.storage.mongodb import MongoDBStorage

router = APIRouter()

class NotificationOut(BaseModel):
    id: str
    message: str
    type: str
    read: bool
    created_at: str

@router.get("/", response_model=List[NotificationOut])
async def get_my_notifications(
    storage: MongoDBStorage = Depends(get_storage),
    current_user: dict = Depends(get_current_user)
):
    raw = storage.get_user_notifications(current_user["_id"])
    return [
        NotificationOut(
            id=str(n["_id"]),
            message=n["message"],
            type=n.get("type", "info"),
            read=n.get("read", False),
            created_at=n["created_at"].isoformat()
        ) for n in raw
    ]

@router.put("/{note_id}/read")
async def mark_read(
    note_id: str,
    storage: MongoDBStorage = Depends(get_storage),
    current_user: dict = Depends(get_current_user)
):
    storage.mark_notification_read(note_id, current_user["_id"])
    return {"status": "ok"}