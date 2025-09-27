#!/usr/bin/env python3
"""
Simple test script to verify the database module works correctly
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database

async def test_database():
    """Test the database module functionality"""
    print("Testing database module...")
    
    # Initialize database
    await database.init_database()
    print("✓ Database initialized")
    
    # Test session creation
    session_doc = {
        "session_id": "test-session-123",
        "join_code": "ABC123",
        "creator_id": "test-user-id",
        "creator_name": "Test User",
        "status": "waiting",
        "participants": [
            {
                "user_id": "test-user-id",
                "name": "Test User",
                "role": "judge",
                "joined_at": datetime.utcnow().isoformat()
            }
        ],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    await database.create_session(session_doc)
    print("✓ Session created successfully")
    
    # Test session retrieval
    retrieved_session = await database.get_session("test-session-123")
    if retrieved_session:
        print("✓ Session retrieved successfully")
        print(f"  Session ID: {retrieved_session['session_id']}")
        print(f"  Join Code: {retrieved_session['join_code']}")
        print(f"  Participants: {len(retrieved_session['participants'])}")
    else:
        print("✗ Failed to retrieve session")
        return
    
    # Test finding session by join code
    found_session = await database.find_session(join_code="ABC123")
    if found_session:
        print("✓ Session found by join code")
    else:
        print("✗ Failed to find session by join code")
        return
    
    # Test adding participant
    new_participant = {
        "user_id": "test-human-id",
        "name": "Test Human",
        "role": "human",
        "joined_at": datetime.utcnow().isoformat()
    }
    
    await database.add_participant_to_session("test-session-123", new_participant)
    print("✓ Participant added successfully")
    
    # Verify participant was added
    updated_session = await database.get_session("test-session-123")
    if len(updated_session["participants"]) == 2:
        print("✓ Participant count updated correctly")
    else:
        print("✗ Participant count not updated")
        return
    
    # Test user sessions query
    user_sessions = await database.get_user_sessions("test-user-id", 10)
    if len(user_sessions) >= 1:
        print("✓ User sessions retrieved successfully")
    else:
        print("✗ Failed to retrieve user sessions")
        return
    
    # Test session deletion
    await database.delete_session("test-session-123")
    print("✓ Session deleted successfully")
    
    # Verify deletion
    deleted_session = await database.get_session("test-session-123")
    if not deleted_session:
        print("✓ Session deletion verified")
    else:
        print("✗ Session still exists after deletion")
        return
    
    print("\n🎉 All database tests passed!")

if __name__ == "__main__":
    asyncio.run(test_database())