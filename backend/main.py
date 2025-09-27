from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from services.session import Session
from services.connections import ConnectionManager
from models import SessionCreate, SessionJoin, SessionResponse, MessageData
from firebase_auth import verify_firebase_token
import database
import json
import httpx
import asyncio
import os
import uuid
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Turing Test Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await database.init_database()

manager = ConnectionManager()
sessions = {}

AI_SERVICE_URL = "http://localhost:3001/api/ai/join"

async def get_current_user(authorization: str = Header(None)):
    """Get current user from Firebase token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    token = authorization.split("Bearer ")[1]
    user_data = verify_firebase_token(token)
    
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user_data

async def trigger_ai_join(session_id: str):
    """Automatically trigger AI to join the session"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                AI_SERVICE_URL,
                json={
                    "session_id": session_id,
                    "websocket_url": f"ws://localhost:8000/ws/{session_id}"
                },
                timeout=10.0
            )
            if response.status_code == 200:
                print(f"AI service notified for session {session_id}")
            else:
                print(f"Failed to notify AI service: {response.status_code}")
    except Exception as e:
        print(f"Error triggering AI join: {e}")

@app.get("/")
async def root():
    return {"message": "Turing Test Backend API", "version": "1.0.0"}

@app.post("/api/sessions/create", response_model=SessionResponse)
async def create_session(session_data: SessionCreate, current_user: dict = Depends(get_current_user)):
    """Create a new Turing test session"""
    
    session_id = str(uuid.uuid4())[:8]  # Short session ID
    join_code = str(uuid.uuid4())[:6].upper()  # 6-character join code
    
    # Create session document
    session_doc = {
        "session_id": session_id,
        "session_name": session_data.session_name,
        "description": session_data.description,
        "creator_id": current_user["uid"],
        "creator_name": current_user["name"],
        "creator_email": current_user["email"],
        "status": "waiting",
        "participants": [
            {
                "user_id": current_user["uid"],
                "name": current_user["name"],
                "email": current_user["email"],
                "role": "judge",
                "joined_at": datetime.utcnow().isoformat()
            }
        ],
        "join_code": join_code,
        "max_participants": session_data.max_participants,
        "duration_minutes": session_data.duration_minutes,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    # Save to database
    await database.create_session(session_doc)
    
    # Create session in memory
    sessions[session_id] = Session(session_id, current_user["uid"])
    sessions[session_id].add_participant("judge", current_user["uid"])
    
    return SessionResponse(
        session_id=session_id,
        session_name=session_data.session_name,
        description=session_data.description,
        creator_id=current_user["uid"],
        creator_name=current_user["name"],
        status="waiting",
        participants=[{
            "user_id": current_user["uid"],
            "name": current_user["name"],
            "email": current_user["email"],
            "role": "judge"
        }],
        created_at=session_doc["created_at"],
        join_code=join_code,
        max_participants=session_data.max_participants,
        duration_minutes=session_data.duration_minutes
    )

@app.post("/api/sessions/join")
async def join_session(join_data: SessionJoin, current_user: dict = Depends(get_current_user)):
    """Join an existing session"""
    
    # Find session by ID or join code
    query = {}
    if join_data.session_id:
        query["session_id"] = join_data.session_id
    elif join_data.join_code:
        query["join_code"] = join_data.join_code
    else:
        raise HTTPException(status_code=400, detail="Either session_id or join_code is required")
    
    # Find session by ID or join code
    session_doc = await database.find_session(
        session_id=join_data.session_id,
        join_code=join_data.join_code
    )
    
    if not session_doc:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session_doc["status"] != "waiting":
        raise HTTPException(status_code=400, detail="Session is not accepting new participants")
    
    # Check if user is already in session
    existing_participant = next(
        (p for p in session_doc["participants"] if p["user_id"] == current_user["uid"]), 
        None
    )
    
    if existing_participant:
        return {
            "message": "Already in session", 
            "session_id": session_doc["session_id"],
            "role": existing_participant["role"]
        }
    
    # Check if session is full
    if len(session_doc["participants"]) >= session_doc["max_participants"]:
        raise HTTPException(status_code=400, detail="Session is full")
    
    # Determine role (first non-judge becomes human)
    role = "human"  # Default for joining participants
    
    # Add participant to session
    new_participant = {
        "user_id": current_user["uid"],
        "name": current_user["name"],
        "email": current_user["email"],
        "role": role,
        "joined_at": datetime.utcnow().isoformat()
    }
    
    # Add participant to database
    await database.add_participant_to_session(session_doc["session_id"], new_participant)
    
    # Update in-memory session
    session_id = session_doc["session_id"]
    if session_id not in sessions:
        sessions[session_id] = Session(session_id, session_doc["creator_id"])
    
    sessions[session_id].add_participant(role, current_user["uid"])
    
    # Trigger AI to join if this is the first human
    if role == "human":
        asyncio.create_task(trigger_ai_join(session_id))
    
    return {
        "message": "Joined session successfully",
        "session_id": session_id,
        "role": role,
        "session_name": session_doc["session_name"]
    }

@app.get("/api/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """Get session details"""
    
    session_doc = await database.get_session(session_id)
    
    if not session_doc:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check if user is participant
    is_participant = any(p["user_id"] == current_user["uid"] for p in session_doc["participants"])
    
    if not is_participant:
        raise HTTPException(status_code=403, detail="Not a participant in this session")
    
    return SessionResponse(
        session_id=session_doc["session_id"],
        session_name=session_doc["session_name"],
        description=session_doc.get("description", ""),
        creator_id=session_doc["creator_id"],
        creator_name=session_doc["creator_name"],
        status=session_doc["status"],
        participants=session_doc["participants"],
        created_at=datetime.fromisoformat(session_doc["created_at"]),
        join_code=session_doc.get("join_code"),
        max_participants=session_doc["max_participants"],
        duration_minutes=session_doc.get("duration_minutes")
    )

@app.get("/api/sessions")
async def list_user_sessions(current_user: dict = Depends(get_current_user)):
    """List all sessions for current user"""
    
    # Get user sessions from database
    sessions_list = await database.get_user_sessions(current_user["uid"], 50)
    
    return {"sessions": sessions_list}

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a session (only creator can delete)"""
    
    session_doc = await database.get_session(session_id)
    
    if not session_doc:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session_doc["creator_id"] != current_user["uid"]:
        raise HTTPException(status_code=403, detail="Only session creator can delete")
    
    # Remove from database
    await database.delete_session(session_id)
    
    # Remove from memory
    if session_id in sessions:
        del sessions[session_id]
    
    return {"message": "Session deleted successfully"}

# Legacy endpoint for compatibility
@app.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """Get information about a session (legacy endpoint)"""
    if session_id in sessions:
        session = sessions[session_id]
        return {
            "session_id": session.session_id,
            "state": session.state,
            "judge_id": session.judge_id,
            "human_id": session.human_id,
            "ai_id": session.ai_id
        }
    return {"error": "Session not found"}

@app.websocket("/ws/{session_id}/{user_id}/{role}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, user_id: str, role: str):
    await manager.connect(user_id, websocket)

    if session_id not in sessions:
        sessions[session_id] = Session(session_id, judge_id=None)

    session = sessions[session_id]
    
    session.add_participant(role, user_id)
    
    if role == "human" and not session.ai_id:
        asyncio.create_task(trigger_ai_join(session_id))
    
    await manager.notify_user_joined(session.get_all_participants(), user_id, role)
    
    session_state = json.dumps({
        "type": "session_state",
        "session_id": session_id,
        "state": session.state,
        "your_role": role,
        "participants": {
            "judge": session.judge_id,
            "human": session.human_id,
            "ai": session.ai_id
        }
    })
    await manager.send_to_user(user_id, session_state)

    try:
        while True:
            data = await websocket.receive_text()
            await session.route_message(user_id, data, manager)
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        leave_notification = json.dumps({
            "type": "user_left",
            "user_id": user_id,
            "role": role
        })
        for participant_id in session.get_all_participants():
            if participant_id != user_id:
                await manager.send_to_user(participant_id, leave_notification)
if __name__=='__main__':
    import uvicorn
    uvicorn.run(app,host="0.0.0.0",port=8000)