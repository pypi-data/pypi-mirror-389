"""
DT Conversation Client

Client for chat-app to interact with Digital Twin's conversation management.
Chat-app uses this to fetch and display conversations stored in DT's Drive.

Note: All requests to api.oneaurica.com are forwarded to the user's local 
execution node, where Drive storage is accessible.

The chat-app can be accessed at:
- Local: http://localhost:8000/chat-app/
- Production: https://api.oneaurica.com/chat-app/

Both support DT/role switching for multi-identity management.
"""

import httpx
from typing import Optional, List, Dict, Any
import os


class DTConversationClient:
    """
    Client for accessing Digital Twin conversation API.
    
    Chat-app uses this to retrieve conversations for rendering.
    All storage is handled by the Digital Twin app.
    """
    
    def __init__(self, auth_token: str, base_url: Optional[str] = None):
        """
        Initialize DT conversation client.
        
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
        
        self.api_base = f"{self.base_url}/digital-twin/api/conversations"
        
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    async def create_conversation(
        self,
        other_dt_id: str,
        title: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Create a new conversation with another DT.
        
        Args:
            other_dt_id: The other DT's identifier
            title: Optional conversation title
            metadata: Optional metadata
            
        Returns:
            Conversation object or None on error
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/create",
                    json={
                        "other_dt_id": other_dt_id,
                        "title": title,
                        "metadata": metadata or {}
                    },
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                result = response.json()
                return result.get("conversation")
        except Exception as e:
            print(f"⚠️ Error creating conversation via DT: {e}")
            return None
    
    async def list_conversations(
        self,
        other_dt_id: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        List conversations for the current DT.
        
        Args:
            other_dt_id: Optional filter by other participant
            limit: Optional limit on number of conversations
            
        Returns:
            List of conversation summaries
        """
        try:
            params = {}
            if other_dt_id:
                params["other_dt_id"] = other_dt_id
            if limit:
                params["limit"] = limit
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base}/list",
                    params=params,
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                result = response.json()
                return result.get("conversations", [])
        except Exception as e:
            print(f"⚠️ Error listing conversations via DT: {e}")
            return []
    
    async def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """
        Get a specific conversation's metadata.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Conversation metadata or None
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base}/{conversation_id}",
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                result = response.json()
                return result.get("conversation")
        except Exception as e:
            print(f"⚠️ Error getting conversation via DT: {e}")
            return None
    
    async def get_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
        before_timestamp: Optional[str] = None
    ) -> List[Dict]:
        """
        Get messages from a conversation.
        
        Args:
            conversation_id: Conversation identifier
            limit: Optional limit on number of messages
            before_timestamp: Optional timestamp to get messages before
            
        Returns:
            List of messages
        """
        try:
            params = {}
            if limit:
                params["limit"] = limit
            if before_timestamp:
                params["before_timestamp"] = before_timestamp
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base}/{conversation_id}/messages",
                    params=params,
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                result = response.json()
                return result.get("messages", [])
        except Exception as e:
            print(f"⚠️ Error getting messages via DT: {e}")
            return []
    
    async def add_message(
        self,
        conversation_id: str,
        content: str,
        message_type: str = "text",
        metadata: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Add a message to a conversation (used for user messages).
        
        Args:
            conversation_id: Conversation identifier
            content: Message content
            message_type: Type of message
            metadata: Optional metadata
            
        Returns:
            Message object or None on error
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/message",
                    json={
                        "conversation_id": conversation_id,
                        "content": content,
                        "message_type": message_type,
                        "metadata": metadata or {}
                    },
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                result = response.json()
                return result.get("message")
        except Exception as e:
            print(f"⚠️ Error adding message via DT: {e}")
            return None
    
    async def mark_messages_read(
        self,
        conversation_id: str,
        message_ids: List[str]
    ) -> bool:
        """
        Mark messages as read.
        
        Args:
            conversation_id: Conversation identifier
            message_ids: List of message IDs to mark as read
            
        Returns:
            True if successful
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/mark-read",
                    json={
                        "conversation_id": conversation_id,
                        "message_ids": message_ids
                    },
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                result = response.json()
                return result.get("success", False)
        except Exception as e:
            print(f"⚠️ Error marking messages as read via DT: {e}")
            return False
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            True if successful
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.api_base}/{conversation_id}",
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                result = response.json()
                return result.get("success", False)
        except Exception as e:
            print(f"⚠️ Error deleting conversation via DT: {e}")
            return False
    
    async def get_stats(self) -> Dict:
        """
        Get conversation statistics.
        
        Returns:
            Statistics dictionary
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base}/stats",
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                result = response.json()
                return result.get("stats", {})
        except Exception as e:
            print(f"⚠️ Error getting conversation stats via DT: {e}")
            return {}
