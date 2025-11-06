"""
DT Identities Client

Client for chat-app to interact with Digital Twin's identity management.
Supports DT/role switching in the chat interface.
"""

import httpx
from typing import Optional, List, Dict, Any
import os


class DTIdentitiesClient:
    """
    Client for accessing Digital Twin identity management API.
    
    Enables DT/role switching for users with multiple identities.
    """
    
    def __init__(self, auth_token: str, base_url: Optional[str] = None):
        """
        Initialize DT identities client.
        
        Args:
            auth_token: JWT authentication token
            base_url: Base URL for DT API (defaults to current host or local)
        """
        self.auth_token = auth_token
        
        # Determine base URL - support both local and production
        if base_url:
            self.base_url = base_url
        else:
            # Check if we're in production (oneaurica.com) or local
            api_host = os.getenv("API_HOST", "")
            if "oneaurica.com" in api_host:
                self.base_url = "https://api.oneaurica.com"
            else:
                self.base_url = os.getenv("DIGITAL_TWIN_URL", "http://localhost:8000")
        
        self.api_base = f"{self.base_url}/digital-twin/api/identities"
        
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    async def list_identities(self) -> List[Dict]:
        """
        List all DT identities/roles for the current user.
        
        Returns:
            List of identity objects
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base}/list",
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                result = response.json()
                return result.get("identities", [])
        except Exception as e:
            print(f"⚠️ Error listing identities via DT: {e}")
            return []
    
    async def get_current_identity(self) -> Optional[Dict]:
        """
        Get the current DT identity.
        
        Returns:
            Current identity object or None
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base}/current",
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                result = response.json()
                return result.get("identity")
        except Exception as e:
            print(f"⚠️ Error getting current identity via DT: {e}")
            return None
    
    async def create_identity(
        self,
        role_name: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Create a new DT identity/role.
        
        Args:
            role_name: Internal role identifier
            display_name: Display name for the identity
            description: Description of this identity
            metadata: Optional metadata
            
        Returns:
            New identity object or None on error
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/create",
                    json={
                        "role_name": role_name,
                        "display_name": display_name,
                        "description": description,
                        "metadata": metadata or {}
                    },
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                result = response.json()
                return result.get("identity")
        except Exception as e:
            print(f"⚠️ Error creating identity via DT: {e}")
            return None
    
    async def switch_identity(self, dt_id: str) -> Optional[Dict]:
        """
        Switch to a different DT identity.
        
        Args:
            dt_id: Target DT identity ID
            
        Returns:
            Switch result or None on error
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/switch",
                    params={"dt_id": dt_id},
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"⚠️ Error switching identity via DT: {e}")
            return None
