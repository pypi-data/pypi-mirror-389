"""
Digital Twin Client - Connects cloud chat to local execution node DT.

This client handles communication between the cloud tier (api.oneaurica.com)
and the user's local execution node where their Digital Twin runs.
"""
import httpx
import os
from typing import Dict, List, Optional
from datetime import datetime


class DigitalTwinClient:
    """Client for communicating with user's Digital Twin on execution node."""
    
    def __init__(self, execution_node_url: str = None, timeout: float = 30.0):
        """
        Initialize DT client.
        
        Args:
            execution_node_url: URL of user's execution node (defaults to localhost for dev)
            timeout: Request timeout in seconds
        """
        self.execution_node_url = execution_node_url or os.getenv(
            "EXECUTION_NODE_URL", 
            "http://localhost:8000"
        )
        self.timeout = timeout
        self.dt_endpoint = f"{self.execution_node_url}/digital-twin/api"
    
    async def check_health(self) -> Dict:
        """
        Check if Digital Twin is reachable and healthy.
        
        Returns:
            dict: Health status or error info
        """
        try:
            async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
                # Health check doesn't require authentication
                response = await client.get(f"{self.dt_endpoint}/health/")
                
                # Check if response was successful (200-299)
                if 200 <= response.status_code < 300:
                    return {
                        "reachable": True,
                        "status": response.json()
                    }
                else:
                    # Non-2xx response
                    return {
                        "reachable": False,
                        "error": f"http_status_{response.status_code}",
                        "message": f"❌ Digital Twin health check returned status {response.status_code}"
                    }
        except httpx.ConnectError:
            return {
                "reachable": False,
                "error": "connection_failed",
                "message": "⚠️ Your Digital Twin (execution node) is not reachable. Please ensure it's running."
            }
        except httpx.TimeoutException:
            return {
                "reachable": False,
                "error": "timeout",
                "message": "⏱️ Your Digital Twin health check timed out."
            }
        except httpx.HTTPStatusError as e:
            return {
                "reachable": False,
                "error": str(e),
                "message": f"❌ Digital Twin health check failed: {str(e)}"
            }
    
    async def think(
        self,
        user_input: str,
        conversation_id: str,
        history: List[Dict],
        user_id: str,
        auth_token: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Send user input to Digital Twin for reasoning and response.
        
        This is the main interaction point - the DT "thinks" about the request
        and decides what to do (respond, use tools, ask for confirmation, etc.).
        
        Args:
            user_input: User's message/query
            conversation_id: Current conversation ID
            history: Conversation history (list of message dicts)
            user_id: User's ID
            auth_token: User's JWT token (DT acts with this authority)
            context: Optional additional context
            
        Returns:
            dict: DT's response with thought process, actions, etc.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.post(
                    f"{self.dt_endpoint}/think/",
                    json={
                        "input": user_input,
                        "context": {
                            "conversation_id": conversation_id,
                            "user_id": user_id,
                            "user_intent": "chat",
                            **(context or {})
                        },
                        "history": history
                    },
                    headers={
                        "Authorization": f"Bearer {auth_token}",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                # Add metadata about DT interaction
                result["dt_active"] = True
                result["timestamp"] = datetime.utcnow().isoformat()
                
                return result
                
        except httpx.ConnectError:
            return {
                "dt_active": False,
                "error": "connection_failed",
                "response": "⚠️ Your Digital Twin (execution node) is not reachable. Please ensure your execution node is running and accessible.",
                "thought_process": "Connection to execution node failed",
                "suggestion": "Start your execution node with: uvicorn src.main:app --port 8000"
            }
        except httpx.TimeoutException:
            return {
                "dt_active": False,
                "error": "timeout",
                "response": "⏱️ Your Digital Twin is taking too long to respond. It may be processing a complex task or experiencing issues.",
                "thought_process": "Request to Digital Twin timed out",
                "suggestion": "Try again or check execution node logs"
            }
        except httpx.HTTPStatusError as e:
            return {
                "dt_active": False,
                "error": "http_error",
                "response": f"❌ Your Digital Twin encountered an error: {e.response.status_code}",
                "thought_process": f"HTTP error from Digital Twin: {str(e)}",
                "details": e.response.text if hasattr(e.response, 'text') else str(e)
            }
        except Exception as e:
            print(f"❌ Digital Twin client error: {e}")
            return {
                "dt_active": False,
                "error": "unknown",
                "response": "❌ Failed to communicate with your Digital Twin. Please try again.",
                "thought_process": f"Unexpected error: {str(e)}"
            }
    
    async def get_capabilities(self, auth_token: str) -> Dict:
        """
        Get Digital Twin's current capabilities.
        
        Args:
            auth_token: User's JWT token
            
        Returns:
            dict: DT capabilities or error
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.dt_endpoint}/capabilities",
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {
                "error": str(e),
                "capabilities": {}
            }
    
    async def get_state(self, auth_token: str) -> Dict:
        """
        Get Digital Twin's current state.
        
        Args:
            auth_token: User's JWT token
            
        Returns:
            dict: DT state or error
        """
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(
                    f"{self.dt_endpoint}/state/",
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {
                "error": str(e),
                "state": {}
            }


def get_execution_node_url(user_id: str) -> str:
    """
    Get the execution node URL for a specific user.
    
    In production, this would:
    - Look up user's registered execution node
    - Use discovery service to find active node
    - Support multiple nodes per user
    
    For development, returns localhost.
    
    Args:
        user_id: User's ID
        
    Returns:
        str: Execution node URL
    """
    # TODO: Implement user-specific execution node discovery
    # For now, use environment variable or default to localhost
    return os.getenv("EXECUTION_NODE_URL", "http://localhost:8000")


def create_dt_client(user_id: str) -> DigitalTwinClient:
    """
    Create a Digital Twin client for a specific user.
    
    Args:
        user_id: User's ID
        
    Returns:
        DigitalTwinClient: Configured client instance
    """
    execution_node_url = get_execution_node_url(user_id)
    return DigitalTwinClient(execution_node_url=execution_node_url)
