"""
Messages API endpoints for chat functionality.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List
from datetime import datetime

# Import the new universal authentication helper
try:
    from src.aurica_auth import protected, get_current_user, public_route
except ImportError:
    # Fallback if running in different context
    print("⚠️  Warning: Could not import universal_auth, authentication may not work")
    def auth_required(func):
        return func
    def get_current_user(request, required=True):
        return {"username": "unknown", "user_id": "unknown"}
    def public_route(func):
        return func

router = APIRouter()

# Simple in-memory message history
message_history: List[dict] = []


class ChatMessage(BaseModel):
    """Chat message model."""
    content: str
    sender: str = "user"


@router.get("/")
@protected
async def get_all_messages(request: Request):
    """Get all messages from history."""
    user = get_current_user(request)
    print(f"💬 User {user.username} viewing message history")
    
    return {"messages": message_history}


@router.post("/")
@protected
async def post_message(request: Request, message: ChatMessage):
    """Post a new message to the chat."""
    user = get_current_user(request)
    
    new_message = {
        "id": len(message_history) + 1,
        "content": message.content,
        "sender": user.username,  # Use authenticated user's username
        "timestamp": datetime.utcnow().isoformat()
    }
    
    message_history.append(new_message)
    
    print(f"💬 User {user.username} posted message #{new_message['id']}")
    
    return {
        "status": "success",
        "message": new_message
    }


@router.delete("/")
@protected
async def clear_messages(request: Request):
    """Clear all messages from history."""
    user = get_current_user(request)
    print(f"🗑️  User {user.username} clearing chat history")
    
    global message_history
    message_history = []
    return {"status": "success", "message": "Chat history cleared"}


@router.get("/count")
@public_route
async def get_message_count():
    """Get the total number of messages."""
    return {
        "count": len(message_history),
        "user_messages": len([m for m in message_history if m["sender"] == "user"]),
        "assistant_messages": len([m for m in message_history if m["sender"] == "assistant"])
    }
