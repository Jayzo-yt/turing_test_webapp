"""
Database module for Turing Test backend
Handles session storage and retrieval operations
"""

import os
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Choose database implementation based on environment
DB_TYPE = os.getenv("DB_TYPE", "memory")  # "memory" or "mongodb"

class BaseDatabase:
    """Base database interface"""
    
    async def create_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        raise NotImplementedError
    
    async def delete_session(self, session_id: str) -> bool:
        raise NotImplementedError
    
    async def find_session_by_join_code(self, join_code: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError
    
    async def get_user_sessions(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        raise NotImplementedError
    
    async def add_participant_to_session(self, session_id: str, participant: Dict[str, Any]) -> bool:
        raise NotImplementedError


class MemoryDatabase(BaseDatabase):
    """In-memory database implementation"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    async def create_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        session_id = session_data["session_id"]
        self.sessions[session_id] = session_data.copy()
        return self.sessions[session_id]
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.sessions.get(session_id)
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        if session_id in self.sessions:
            self.sessions[session_id].update(updates)
            self.sessions[session_id]["updated_at"] = datetime.utcnow().isoformat()
            return True
        return False
    
    async def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    async def find_session_by_join_code(self, join_code: str) -> Optional[Dict[str, Any]]:
        for session in self.sessions.values():
            if session.get("join_code") == join_code:
                return session
        return None
    
    async def get_user_sessions(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        user_sessions = []
        for session in self.sessions.values():
            # Check if user is participant
            is_participant = any(
                p["user_id"] == user_id for p in session.get("participants", [])
            )
            if is_participant:
                user_sessions.append(session)
        
        # Sort by created_at descending
        user_sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return user_sessions[:limit]
    
    async def add_participant_to_session(self, session_id: str, participant: Dict[str, Any]) -> bool:
        if session_id in self.sessions:
            self.sessions[session_id]["participants"].append(participant)
            self.sessions[session_id]["updated_at"] = datetime.utcnow().isoformat()
            return True
        return False


class MongoDatabase(BaseDatabase):
    """MongoDB database implementation"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.sessions_collection = None
    
    async def initialize(self):
        """Initialize MongoDB connection"""
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            
            mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
            self.client = AsyncIOMotorClient(mongo_url)
            self.db = self.client.turing_test
            self.sessions_collection = self.db.sessions
            
            # Test connection
            await self.client.admin.command('ping')
            print("MongoDB connected successfully")
            
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            print("Falling back to in-memory storage")
            raise
    
    async def create_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        if self.sessions_collection is None:
            raise RuntimeError("Database not initialized")
        
        result = await self.sessions_collection.insert_one(session_data)
        session_data["_id"] = str(result.inserted_id)
        return session_data
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        if self.sessions_collection is None:
            raise RuntimeError("Database not initialized")
        
        session = await self.sessions_collection.find_one(
            {"session_id": session_id},
            {"_id": 0}
        )
        return session
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        if self.sessions_collection is None:
            raise RuntimeError("Database not initialized")
        
        updates["updated_at"] = datetime.utcnow().isoformat()
        result = await self.sessions_collection.update_one(
            {"session_id": session_id},
            {"$set": updates}
        )
        return result.modified_count > 0
    
    async def delete_session(self, session_id: str) -> bool:
        if self.sessions_collection is None:
            raise RuntimeError("Database not initialized")
        
        result = await self.sessions_collection.delete_one({"session_id": session_id})
        return result.deleted_count > 0
    
    async def find_session_by_join_code(self, join_code: str) -> Optional[Dict[str, Any]]:
        if self.sessions_collection is None:
            raise RuntimeError("Database not initialized")
        
        session = await self.sessions_collection.find_one(
            {"join_code": join_code},
            {"_id": 0}
        )
        return session
    
    async def get_user_sessions(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        if self.sessions_collection is None:
            raise RuntimeError("Database not initialized")
        
        cursor = self.sessions_collection.find(
            {"participants.user_id": user_id},
            {"_id": 0}
        ).sort("created_at", -1).limit(limit)
        
        sessions = await cursor.to_list(length=limit)
        return sessions
    
    async def add_participant_to_session(self, session_id: str, participant: Dict[str, Any]) -> bool:
        if self.sessions_collection is None:
            raise RuntimeError("Database not initialized")
        
        result = await self.sessions_collection.update_one(
            {"session_id": session_id},
            {
                "$push": {"participants": participant},
                "$set": {"updated_at": datetime.utcnow().isoformat()}
            }
        )
        return result.modified_count > 0


class DatabaseManager:
    """Database manager that handles different database implementations"""
    
    def __init__(self):
        self.db: BaseDatabase = None
    
    async def initialize(self):
        """Initialize the appropriate database implementation"""
        db_type = os.getenv("DB_TYPE", "memory").lower()
        
        if db_type == "mongodb":
            try:
                self.db = MongoDatabase()
                await self.db.initialize()
                print("Using MongoDB database")
            except Exception as e:
                print(f"MongoDB initialization failed: {e}")
                print("Falling back to in-memory database")
                self.db = MemoryDatabase()
        else:
            self.db = MemoryDatabase()
            print("Using in-memory database")
    
    async def create_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        return await self.db.create_session(session_data)
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.get_session(session_id)
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        return await self.db.update_session(session_id, updates)
    
    async def delete_session(self, session_id: str) -> bool:
        return await self.db.delete_session(session_id)
    
    async def find_session_by_join_code(self, join_code: str) -> Optional[Dict[str, Any]]:
        return await self.db.find_session_by_join_code(join_code)
    
    async def get_user_sessions(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        return await self.db.get_user_sessions(user_id, limit)
    
    async def add_participant_to_session(self, session_id: str, participant: Dict[str, Any]) -> bool:
        return await self.db.add_participant_to_session(session_id, participant)
    
    async def find_session(self, session_id: Optional[str] = None, join_code: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Find session by either ID or join code"""
        if session_id:
            return await self.get_session(session_id)
        elif join_code:
            return await self.find_session_by_join_code(join_code)
        return None


# Global database instance
db_manager = DatabaseManager()

# Convenience functions for easy import
async def init_database():
    """Initialize the database"""
    await db_manager.initialize()

async def create_session(session_data: Dict[str, Any]) -> Dict[str, Any]:
    return await db_manager.create_session(session_data)

async def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    return await db_manager.get_session(session_id)

async def update_session(session_id: str, updates: Dict[str, Any]) -> bool:
    return await db_manager.update_session(session_id, updates)

async def delete_session(session_id: str) -> bool:
    return await db_manager.delete_session(session_id)

async def find_session_by_join_code(join_code: str) -> Optional[Dict[str, Any]]:
    return await db_manager.find_session_by_join_code(join_code)

async def get_user_sessions(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    return await db_manager.get_user_sessions(user_id, limit)

async def add_participant_to_session(session_id: str, participant: Dict[str, Any]) -> bool:
    return await db_manager.add_participant_to_session(session_id, participant)

async def find_session(session_id: Optional[str] = None, join_code: Optional[str] = None) -> Optional[Dict[str, Any]]:
    return await db_manager.find_session(session_id, join_code)