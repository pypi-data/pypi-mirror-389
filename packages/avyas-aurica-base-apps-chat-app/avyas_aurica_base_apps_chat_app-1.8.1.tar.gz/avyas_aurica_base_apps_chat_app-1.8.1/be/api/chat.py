"""
Chat API endpoints for managing conversations.
Timestamp: 2025-11-02 20:15
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import os

# Import Aurica Auth SDK
try:
    from src.aurica_auth import protected, get_current_user, public
except ImportError:
    # Fallback if running in different context
    print("⚠️  Warning: Could not import aurica_auth SDK")
    def protected(func):
        return func
    def get_current_user(request, required=True):
        return type('User', (), {"username": "unknown", "user_id": "unknown"})()
    def public(func):
        return func

# Import Universal Execution Node Connector
try:
    # Old connector - deprecated with transparent proxy architecture
    # from src.execution_node_connector import ExecutionNodeConnector
    ExecutionNodeConnector = None
    print("ℹ️  ExecutionNodeConnector deprecated - using transparent proxy")
except ImportError as e:
    print(f"ℹ️  ExecutionNodeConnector not available - using transparent proxy: {e}")
    ExecutionNodeConnector = None

# Import storage
import sys
from pathlib import Path
chat_be_dir = Path(__file__).parent.parent
if str(chat_be_dir) not in sys.path:
    sys.path.insert(0, str(chat_be_dir))

from storage import get_storage

router = APIRouter()

# Configuration
# TEMPORARY: Hardcoded to True for testing - check .env file
DIGITAL_TWIN_ENABLED = True  # os.getenv("DIGITAL_TWIN_ENABLED", "false").lower() == "true"

# Debug: Print DT status at module load
print(f"🤖 Chat App: DIGITAL_TWIN_ENABLED = {DIGITAL_TWIN_ENABLED}")
print(f"   Environment value: {os.getenv('DIGITAL_TWIN_ENABLED', 'NOT SET')}")


class Message(BaseModel):
    """Message model."""
    id: str
    conversation_id: str
    content: str
    sender: str
    timestamp: str
    

class Conversation(BaseModel):
    """Conversation model."""
    id: str
    title: str
    created_at: str
    updated_at: str


class SendMessageRequest(BaseModel):
    """Request model for sending a message."""
    conversation_id: Optional[str] = None
    content: str
    sender: str = "user"


class CreateConversationRequest(BaseModel):
    """Request model for creating a conversation."""
    title: str = "New Conversation"


@router.post("/conversations")
@protected
async def create_conversation(request: Request, req: CreateConversationRequest):
    """Create a new conversation."""
    user = get_current_user(request)
    storage = get_storage()
    
    conversation_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    conversation = {
        "id": conversation_id,
        "title": req.title,
        "created_at": now,
        "updated_at": now,
        "owner": user.user_id  # Track conversation owner
    }
    
    # Save to persistent storage
    storage.save_conversation(conversation_id, conversation)
    
    print(f"💬 User {user.username} created conversation: {conversation_id}")
    
    return conversation


@router.get("/conversations")
@protected
async def list_conversations(request: Request):
    """List all conversations for the authenticated user."""
    user = get_current_user(request)
    storage = get_storage()
    
    print(f"💬 User {user.username} listing conversations")
    
    # Simple detection: If IS_EXECUTION_NODE is true, we're the execution node itself
    # Execution nodes don't need to connect to themselves via P2P
    is_execution_node = os.getenv("IS_EXECUTION_NODE", "false").lower() == "true"
    print(f"🔍 IS_EXECUTION_NODE env: {os.getenv('IS_EXECUTION_NODE', 'NOT SET')}, parsed: {is_execution_node}")
    
    # Try to get conversations from local execution node first (P2P)
    # Skip this if we ARE the execution node to avoid self-connection loops
    if DIGITAL_TWIN_ENABLED and ExecutionNodeConnector and not is_execution_node:
        auth_token = request.headers.get("authorization", "").replace("Bearer ", "")
        
        try:
            connector = ExecutionNodeConnector(
                user_id=user.user_id,
                auth_token=auth_token,
                discovery_url=str(request.base_url).rstrip('/')
            )
            
            connected = await connector.connect()
            
            if connected:
                # Get conversations from local execution node
                result = await connector.call(
                    app_name="chat-app",
                    endpoint="/api/chat/conversations",
                    method="GET"
                )
                
                if result.get("success"):
                    print(f"✅ Retrieved conversations from local execution node via P2P")
                    data = result.get("data", {})
                    return {
                        "conversations": data.get("conversations", []),
                        "source": "local_execution_node"
                    }
        except Exception as e:
            print(f"⚠️ Could not connect to execution node: {e}")
    
    # Use local storage (either we are the execution node, or fallback from cloud)
    if is_execution_node:
        print(f"📦 Using local storage (running on execution node)")
    else:
        print(f"📦 Using cloud storage (execution node not available)")
    user_conversations = storage.get_conversations(user_id=user.user_id)
    
    return {
        "conversations": list(user_conversations.values()),
        "source": "cloud_storage"
    }


@router.get("/conversations/{conversation_id}")
@protected
async def get_conversation(conversation_id: str, request: Request):
    """Get a specific conversation."""
    user = get_current_user(request)
    storage = get_storage()
    
    conversation = storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Check ownership
    if conversation.get("owner") != user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    print(f"💬 User {user.username} viewing conversation: {conversation_id}")
    
    return conversation


@router.delete("/conversations/{conversation_id}")
@protected
async def delete_conversation(conversation_id: str, request: Request):
    """Delete a conversation."""
    user = get_current_user(request)
    storage = get_storage()
    
    conversation = storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Check ownership
    if conversation.get("owner") != user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    storage.delete_conversation(conversation_id)
    
    return {"message": "Conversation deleted successfully"}


@router.post("/send")
@protected
async def send_message(request: Request, req: SendMessageRequest):
    """Send a message in a conversation - routes to local execution node."""
    user = get_current_user(request)
    auth_token = request.headers.get("authorization", "").replace("Bearer ", "")
    
    # Check if we're running as the execution node
    is_execution_node = os.getenv("IS_EXECUTION_NODE", "false").lower() == "true"
    
    # Always try to route to local execution node first (unless we ARE the execution node)
    if DIGITAL_TWIN_ENABLED and ExecutionNodeConnector and not is_execution_node:
        try:
            connector = ExecutionNodeConnector(
                user_id=user.user_id,
                auth_token=auth_token,
                discovery_url=str(request.base_url).rstrip('/')
            )
            
            connected = await connector.connect()
            
            if connected:
                print(f"✅ Routing message to local execution node via P2P")
                
                # Forward the entire request to local execution node
                result = await connector.call(
                    app_name="chat-app",
                    endpoint="/api/chat/send",
                    method="POST",
                    data={
                        "conversation_id": req.conversation_id,
                        "content": req.content,
                        "sender": req.sender
                    }
                )
                
                if result.get("success"):
                    response_data = result.get("data", {})
                    response_data["source"] = "local_execution_node"
                    return response_data
                else:
                    print(f"⚠️ Local execution node returned error: {result.get('message')}")
        
        except Exception as e:
            print(f"⚠️ Could not route to execution node: {e}")
    
    # Fallback to cloud storage if execution node not available
    print(f"📦 Using cloud storage (execution node not available)")
    storage = get_storage()
    conversation_id = req.conversation_id
    
    # Create new conversation if none specified
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        conversation = {
            "id": conversation_id,
            "title": "New Conversation",
            "created_at": now,
            "updated_at": now,
            "owner": user.user_id
        }
        storage.save_conversation(conversation_id, conversation)
    
    # Check if conversation exists
    conversation = storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Check ownership
    if conversation.get("owner") != user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Create message
    message_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    # Determine sender - use req.sender if provided, otherwise use username
    sender = req.sender if req.sender in ['user', 'digital_twin', 'assistant', 'system'] else user.username
    
    message = {
        "id": message_id,
        "conversation_id": conversation_id,
        "content": req.content,
        "sender": sender,
        "timestamp": now
    }
    
    # Save message to persistent storage
    storage.add_message(conversation_id, message)
    
    print(f"💬 User {user.username} sent message (sender: {sender}) in conversation: {conversation_id} (cloud storage fallback)")
    
    # If this is a digital_twin or assistant message, just save it and return
    if sender in ['digital_twin', 'assistant']:
        return {
            "message": message,
            "conversation_id": conversation_id,
            "source": "cloud_storage"
        }
    
    # For user messages, return success (streaming will handle the response)
    return {
        "message": message,
        "conversation_id": conversation_id,
        "source": "cloud_storage"
    }


@router.get("/conversations/{conversation_id}/messages")
@protected
async def get_messages(conversation_id: str, request: Request):
    """Get all messages in a conversation."""
    user = get_current_user(request)
    storage = get_storage()
    
    print(f"💬 User {user.username} viewing messages in conversation: {conversation_id}")
    
    # Check if we're running as the execution node
    is_execution_node = os.getenv("IS_EXECUTION_NODE", "false").lower() == "true"
    
    # Try to get messages from local execution node first (P2P)
    if DIGITAL_TWIN_ENABLED and ExecutionNodeConnector and not is_execution_node:
        auth_token = request.headers.get("authorization", "").replace("Bearer ", "")
        
        try:
            connector = ExecutionNodeConnector(
                user_id=user.user_id,
                auth_token=auth_token,
                discovery_url=str(request.base_url).rstrip('/')
            )
            
            connected = await connector.connect()
            
            if connected:
                # Get messages from local execution node
                result = await connector.call(
                    app_name="chat-app",
                    endpoint=f"/api/chat/conversations/{conversation_id}/messages",
                    method="GET"
                )
                
                if result.get("success"):
                    print(f"✅ Retrieved messages from local execution node via P2P")
                    data = result.get("data", {})
                    return {
                        "conversation_id": conversation_id,
                        "messages": data.get("messages", []),
                        "source": "local_execution_node"
                    }
        except Exception as e:
            print(f"⚠️ Could not connect to execution node: {e}")
    
    # Fallback to cloud storage if execution node not available
    print(f"📦 Using cloud storage (execution node not available)")
    
    conversation = storage.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Check ownership
    if conversation.get("owner") != user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    messages = storage.get_messages(conversation_id)
    
    return {
        "conversation_id": conversation_id,
        "messages": messages,
        "source": "cloud_storage"
    }


@router.get("/dt/status")
@protected
async def get_dt_status(request: Request):
    """
    Get Digital Twin status and capabilities via P2P connection.
    """
    user = get_current_user(request)
    
    if not DIGITAL_TWIN_ENABLED or not ExecutionNodeConnector:
        return {
            "dt_enabled": False,
            "message": "Digital Twin integration is not enabled"
        }
    
    auth_token = request.headers.get("authorization", "").replace("Bearer ", "")
    
    # Use P2P connector
    connector = ExecutionNodeConnector(
        user_id=user.user_id,
        auth_token=auth_token,
        discovery_url=str(request.base_url).rstrip('/')
    )
    
    # Check connection
    connected = await connector.connect()
    
    if not connected:
        return {
            "dt_enabled": True,
            "reachable": False,
            "error": "not_connected",
            "message": "Execution node not available"
        }
    
    # Get capabilities from execution node
    capabilities_result = await connector.call(
        app_name="digital-twin",
        endpoint="/api/capabilities/",
        method="GET"
    )
    
    # Get state from execution node
    state_result = await connector.call(
        app_name="digital-twin",
        endpoint="/api/state/",
        method="GET"
    )
    
    return {
        "dt_enabled": True,
        "reachable": True,
        "connection": "p2p",
        "execution_node_url": connector.execution_node_url,
        "capabilities": capabilities_result.get("data", {}) if capabilities_result.get("success") else {},
        "state": state_result.get("data", {}) if state_result.get("success") else {}
    }
