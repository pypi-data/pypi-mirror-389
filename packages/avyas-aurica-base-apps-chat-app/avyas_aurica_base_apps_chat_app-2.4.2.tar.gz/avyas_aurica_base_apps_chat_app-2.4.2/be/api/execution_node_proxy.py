"""
Execution Node Proxy API

Universal proxy that allows ANY remote app to access the local execution node.
All apps can use this to communicate with the user's local machine via P2P.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any

# Import auth
try:
    from src.aurica_auth import protected, get_current_user
except ImportError:
    def protected(func):
        return func
    def get_current_user(request):
        return type('User', (), {"username": "unknown", "user_id": "unknown"})()

# Import Universal Connector
try:
    # Old connector - deprecated, not needed with transparent proxy
    # from src.execution_node_connector import ExecutionNodeConnector
    ExecutionNodeConnector = None
    print("ℹ️  ExecutionNodeConnector deprecated - using transparent proxy")
except ImportError:
    ExecutionNodeConnector = None
    print("ℹ️  ExecutionNodeConnector not available - using transparent proxy")

router = APIRouter()


class ProxyRequest(BaseModel):
    """Request to proxy to execution node"""
    app_name: str
    endpoint: str
    method: str = "GET"
    data: Optional[Dict] = None
    params: Optional[Dict] = None


@router.post("/call")
@protected
async def proxy_to_execution_node(request: Request, req: ProxyRequest):
    """
    Universal proxy to call any API on the user's execution node.
    
    This allows ANY remote app to access the local execution node via P2P.
    
    Example:
        POST /chat-app/api/execution_node/call
        {
            "app_name": "chat-app",
            "endpoint": "/api/conversations/123/messages",
            "method": "GET"
        }
    """
    if not ExecutionNodeConnector:
        raise HTTPException(
            status_code=503,
            detail="Execution node connector not available"
        )
    
    user = get_current_user(request)
    auth_token = request.headers.get("authorization", "").replace("Bearer ", "")
    
    # Create connector
    connector = ExecutionNodeConnector(
        user_id=user.user_id,
        auth_token=auth_token,
        discovery_url=str(request.base_url).rstrip('/')
    )
    
    # Connect to execution node
    connected = await connector.connect()
    
    if not connected:
        raise HTTPException(
            status_code=503,
            detail="Execution node not available"
        )
    
    # Make the proxied call
    result = await connector.call(
        app_name=req.app_name,
        endpoint=req.endpoint,
        method=req.method,
        data=req.data,
        params=req.params
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=502,
            detail=f"Execution node call failed: {result.get('message')}"
        )
    
    return result.get("data")


@router.get("/status")
@protected
async def get_execution_node_status(request: Request):
    """
    Get status of user's execution node connection.
    """
    if not ExecutionNodeConnector:
        return {
            "available": False,
            "error": "Connector not available"
        }
    
    user = get_current_user(request)
    auth_token = request.headers.get("authorization", "").replace("Bearer ", "")
    
    connector = ExecutionNodeConnector(
        user_id=user.user_id,
        auth_token=auth_token,
        discovery_url=str(request.base_url).rstrip('/')
    )
    
    connected = await connector.connect()
    
    return {
        "available": connected,
        "status": connector.get_status()
    }


@router.get("/conversations/{conversation_id}/messages")
@protected
async def get_messages_from_execution_node(
    conversation_id: str,
    request: Request
):
    """
    Get messages from execution node (example of direct access).
    
    This shows how to directly access data from the local execution node
    without going through the cloud storage.
    """
    if not ExecutionNodeConnector:
        raise HTTPException(
            status_code=503,
            detail="Execution node connector not available"
        )
    
    user = get_current_user(request)
    auth_token = request.headers.get("authorization", "").replace("Bearer ", "")
    
    connector = ExecutionNodeConnector(
        user_id=user.user_id,
        auth_token=auth_token,
        discovery_url=str(request.base_url).rstrip('/')
    )
    
    connected = await connector.connect()
    
    if not connected:
        raise HTTPException(
            status_code=503,
            detail="Execution node not available - please start your local server"
        )
    
    # Get messages directly from execution node
    result = await connector.get_chat_history(conversation_id)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=502,
            detail=f"Failed to get messages: {result.get('message')}"
        )
    
    return result.get("data")
