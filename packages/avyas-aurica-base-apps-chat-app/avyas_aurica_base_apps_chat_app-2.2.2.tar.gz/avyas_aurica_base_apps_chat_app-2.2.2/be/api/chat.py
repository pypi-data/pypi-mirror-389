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

# Import rendering blocks
from rendering_blocks import get_rendering_registry, RenderBlock, RenderType
import json
import re

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
    render_blocks: Optional[List[dict]] = None  # Rendering metadata
    metadata: Optional[dict] = None


def parse_message_for_rendering(content: str, sender: str = "assistant") -> dict:
    """
    Parse message content and extract rendering blocks.
    
    Returns a dict with:
    - render_blocks: List of rendering block specifications
    - metadata: Additional metadata about the message
    """
    registry = get_rendering_registry()
    blocks = []
    metadata = {}
    
    # Pattern 1: Extract JSON blocks from markdown code fences (strip whitespace)
    json_blocks_raw = re.findall(r'```json\s*(.*?)\s*```', content, re.DOTALL)
    json_blocks = [block.strip() for block in json_blocks_raw]  # Strip each block
    
    if json_blocks:
        # Has structured data - split into parts
        parts = re.split(r'```json\s*.*?\s*```', content, flags=re.DOTALL)
        
        for i, part in enumerate(parts):
            part = part.strip()
            if part:
                # Check for execution status patterns
                if "Executing" in part or "Calling" in part:
                    blocks.append({
                        "type": RenderType.EXECUTION_STATUS.value,
                        "data": {"content": part, "status": "executing"},
                        "metadata": {"animated": True}
                    })
                elif "✅" in part:
                    # Extract function name if present
                    func_match = re.search(r'✅\s*(\w+):', part)
                    func_name = func_match.group(1) if func_match else None
                    
                    blocks.append({
                        "type": RenderType.SUCCESS.value,
                        "data": {"content": part},
                        "metadata": {"icon": "✅", "function_name": func_name}
                    })
                else:
                    blocks.append({
                        "type": RenderType.MARKDOWN.value,
                        "data": {"content": part},
                        "metadata": {}
                    })
            
            # Add JSON block if exists
            if i < len(json_blocks):
                try:
                    print(f"🔍 Attempting to parse JSON block {i}")
                    # Get the raw content
                    json_content = json_blocks[i]
                    
                    # Debug: show actual representation
                    print(f"   Content length: {len(json_content)}, starts with: {repr(json_content[:50])}")
                    
                    # Handle escaped newlines (e.g., \\n as string literals)
                    # This can happen if content is double-encoded
                    if '\\n' in json_content[:10]:
                        print(f"   ⚠️  Found escaped newlines, decoding...")
                        # Decode escaped sequences
                        json_content = json_content.encode().decode('unicode_escape')
                        print(f"   After decode: {repr(json_content[:50])}")
                    
                    # Now strip whitespace
                    json_content = json_content.strip()
                    
                    json_data = json.loads(json_content)
                    print(f"   📊 Parsed JSON data successfully!")
                    
                    # Check if it has user_id and username for profile detection
                    if isinstance(json_data, dict):
                        print(f"   Keys: {list(json_data.keys())}")
                        if "user_id" in json_data and "username" in json_data:
                            print(f"   ✅ Detected as PROFILE DATA")
                    
                    render_block = registry.create_render_block(json_data)
                    print(f"   🎨 Created render block type: {render_block.type}")
                    blocks.append(render_block.dict())
                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON decode error: {e}")
                    print(f"   Failed content (first 100 chars): {repr(json_blocks[i][:100])}")
                    # If not valid JSON, treat as code
                    blocks.append({
                        "type": RenderType.CODE.value,
                        "data": {"content": json_blocks[i], "language": "json"},
                        "metadata": {}
                    })
                except Exception as e:
                    print(f"   ❌ Unexpected error: {e}")
                    import traceback
                    traceback.print_exc()
                    # Fallback to code block
                    blocks.append({
                        "type": RenderType.CODE.value,
                        "data": {"content": json_blocks[i], "language": "json"},
                        "metadata": {}
                    })
        
        metadata["has_structured_data"] = True
        metadata["json_block_count"] = len(json_blocks)
    
    else:
        # No JSON blocks - check if content itself is JSON
        try:
            data = json.loads(content)
            render_block = registry.create_render_block(data)
            blocks.append(render_block.dict())
            metadata["is_pure_json"] = True
        except json.JSONDecodeError:
            # Regular text/markdown
            blocks.append({
                "type": RenderType.MARKDOWN.value,
                "data": {"content": content},
                "metadata": {}
            })
    
    return {
        "render_blocks": blocks,
        "metadata": metadata
    }
    

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
    
    # Add rendering blocks to assistant messages
    enhanced_messages = []
    for msg in messages:
        if msg.get("sender") in ["assistant", "digital_twin"]:
            print(f"🎨 Parsing message for rendering: {msg.get('id')}")
            print(f"   Sender: {msg.get('sender')}")
            print(f"   Content preview: {msg.get('content', '')[:100]}...")
            
            # Parse content for rendering
            rendering_info = parse_message_for_rendering(msg.get("content", ""), msg.get("sender"))
            msg["render_blocks"] = rendering_info["render_blocks"]
            msg["render_metadata"] = rendering_info["metadata"]
            
            print(f"   ✅ Created {len(rendering_info['render_blocks'])} render blocks")
        enhanced_messages.append(msg)
    
    return {
        "conversation_id": conversation_id,
        "messages": enhanced_messages,
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
