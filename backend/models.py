from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SessionCreate(BaseModel):
    session_name: str
    description: Optional[str] = ""
    max_participants: int = 3  # judge + human + ai
    duration_minutes: Optional[int] = 30

class SessionJoin(BaseModel):
    session_id: Optional[str] = None
    join_code: Optional[str] = None

class UserData(BaseModel):
    uid: str
    email: str
    name: str
    role: str  # "judge", "human", "ai"

class ParticipantData(BaseModel):
    user_id: str
    name: str
    email: str
    role: str
    joined_at: datetime

class SessionResponse(BaseModel):
    session_id: str
    session_name: str
    description: Optional[str]
    creator_id: str
    creator_name: str
    status: str  # "waiting", "active", "completed"
    participants: List[dict]
    created_at: datetime
    join_code: Optional[str] = None
    max_participants: int
    duration_minutes: Optional[int]

class MessageData(BaseModel):
    type: str = "chat"
    content: str