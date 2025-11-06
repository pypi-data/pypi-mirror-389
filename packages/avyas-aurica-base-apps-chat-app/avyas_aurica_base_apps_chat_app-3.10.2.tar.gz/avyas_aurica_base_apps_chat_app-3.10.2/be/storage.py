"""
Chat Storage Manager - Persistent storage using centralized data directory.

This module provides persistent storage for chat data using the centralized data/ directory.
All data is stored in data/chat-app/ (sibling to apps/) managed by Drive.
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ChatStorage:
    """Manages persistent storage for chat conversations and messages."""
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize chat storage.
        
        Args:
            storage_dir: Optional custom storage directory. 
                        Defaults to data/chat-app/chat/ (centralized storage)
        """
        if storage_dir is None:
            # Use centralized data directory (sibling to apps/)
            code_root = Path(__file__).parent.parent.parent.parent  # /code directory
            storage_dir = code_root / "data" / "chat-app" / "chat"
        
        self.storage_dir = Path(storage_dir)
        self.conversations_file = self.storage_dir / "conversations.json"
        self.messages_dir = self.storage_dir / "messages"
        
        # Create directories if they don't exist
        self._initialize_storage()
        
        # In-memory cache for faster access
        self._conversations_cache: Dict = {}
        self._messages_cache: Dict = {}
        self._cache_loaded = False
    
    def _initialize_storage(self):
        """Create storage directories if they don't exist."""
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            self.messages_dir.mkdir(parents=True, exist_ok=True)
            
            # Create empty conversations file if it doesn't exist
            if not self.conversations_file.exists():
                self._save_json(self.conversations_file, {})
                logger.info(f"✅ Created conversations storage at {self.conversations_file}")
            
            logger.info(f"✅ Chat storage initialized at {self.storage_dir}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize chat storage: {e}")
            raise
    
    def _load_json(self, file_path: Path) -> Dict:
        """Load JSON data from file."""
        try:
            if not file_path.exists():
                return {}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ Error loading {file_path}: {e}")
            return {}
    
    def _save_json(self, file_path: Path, data: Dict):
        """Save JSON data to file."""
        try:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ Error saving {file_path}: {e}")
            raise
    
    def load_all_data(self):
        """Load all conversations and messages from storage into memory cache."""
        if self._cache_loaded:
            return
        
        logger.info("📂 Loading chat data from centralized storage...")
        
        # Load conversations
        self._conversations_cache = self._load_json(self.conversations_file)
        logger.info(f"   Loaded {len(self._conversations_cache)} conversations")
        
        # Load messages for each conversation
        for conv_id in self._conversations_cache.keys():
            messages_file = self.messages_dir / f"{conv_id}.json"
            loaded_data = self._load_json(messages_file)
            # Ensure messages are stored as list, not dict
            self._messages_cache[conv_id] = loaded_data if isinstance(loaded_data, list) else []
        
        self._cache_loaded = True
        logger.info("✅ Chat data loaded successfully")
    
    def get_conversations(self, user_id: Optional[str] = None, dt_id: Optional[str] = None) -> Dict:
        """
        Get all conversations, optionally filtered by user and/or DT.
        
        Args:
            user_id: Optional user ID to filter by owner
            dt_id: Optional DT ID to filter by associated digital twin
            
        Returns:
            Dictionary of conversations
        """
        self.load_all_data()
        
        conversations = self._conversations_cache
        
        # Filter by user_id if provided
        if user_id:
            conversations = {
                conv_id: conv_data
                for conv_id, conv_data in conversations.items()
                if conv_data.get("owner") == user_id
            }
        
        # Filter by dt_id if provided
        if dt_id:
            conversations = {
                conv_id: conv_data
                for conv_id, conv_data in conversations.items()
                if conv_data.get("dt_id") == dt_id
            }
        
        return dict(conversations)
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Get a specific conversation."""
        self.load_all_data()
        return self._conversations_cache.get(conversation_id)
    
    def save_conversation(self, conversation_id: str, conversation_data: Dict):
        """Save or update a conversation."""
        self.load_all_data()
        
        # Update cache
        self._conversations_cache[conversation_id] = conversation_data
        
        # Save to storage
        self._save_json(self.conversations_file, self._conversations_cache)
        logger.info(f"💾 Saved conversation: {conversation_id}")
    
    def delete_conversation(self, conversation_id: str):
        """Delete a conversation and its messages."""
        self.load_all_data()
        
        # Remove from cache
        if conversation_id in self._conversations_cache:
            del self._conversations_cache[conversation_id]
        
        if conversation_id in self._messages_cache:
            del self._messages_cache[conversation_id]
        
        # Delete from storage
        self._save_json(self.conversations_file, self._conversations_cache)
        
        messages_file = self.messages_dir / f"{conversation_id}.json"
        if messages_file.exists():
            messages_file.unlink()
        
        logger.info(f"🗑️  Deleted conversation: {conversation_id}")
    
    def get_messages(self, conversation_id: str) -> List[Dict]:
        """Get all messages for a conversation."""
        self.load_all_data()
        
        if conversation_id not in self._messages_cache:
            messages_file = self.messages_dir / f"{conversation_id}.json"
            loaded_data = self._load_json(messages_file)
            # Ensure it's a list, not a dict (in case file is empty or malformed)
            self._messages_cache[conversation_id] = loaded_data if isinstance(loaded_data, list) else []
        
        messages = self._messages_cache.get(conversation_id, [])
        # Double-check it's a list
        return messages if isinstance(messages, list) else []
    
    def add_message(self, conversation_id: str, message: Dict):
        """Add a message to a conversation."""
        self.load_all_data()
        
        # Ensure conversation exists in messages cache
        if conversation_id not in self._messages_cache:
            self._messages_cache[conversation_id] = []
        
        # Ensure it's a list (in case it was loaded as dict)
        if not isinstance(self._messages_cache[conversation_id], list):
            logger.warning(f"⚠️  Messages cache for {conversation_id} was not a list, resetting to empty list")
            self._messages_cache[conversation_id] = []
        
        # Add message to cache
        self._messages_cache[conversation_id].append(message)
        
        # Save to storage
        messages_file = self.messages_dir / f"{conversation_id}.json"
        self._save_json(messages_file, self._messages_cache[conversation_id])
        
        # Update conversation's updated_at timestamp
        if conversation_id in self._conversations_cache:
            self._conversations_cache[conversation_id]["updated_at"] = datetime.utcnow().isoformat()
            self._save_json(self.conversations_file, self._conversations_cache)
    
    def clear_messages(self, conversation_id: str):
        """Clear all messages for a conversation."""
        self.load_all_data()
    
    def clear_messages(self, conversation_id: str):
        """Clear all messages from a conversation."""
        self.load_all_data()
        
        # Clear cache
        self._messages_cache[conversation_id] = []
        
        # Save to storage
        messages_file = self.messages_dir / f"{conversation_id}.json"
        self._save_json(messages_file, [])
        
        logger.info(f"🗑️  Cleared messages for conversation: {conversation_id}")
    
    def get_stats(self) -> Dict:
        """Get storage statistics."""
        self.load_all_data()
        
        total_messages = sum(len(messages) for messages in self._messages_cache.values())
        
        # Calculate storage size
        storage_size_bytes = 0
        try:
            # Count conversations file
            if self.conversations_file.exists():
                storage_size_bytes += self.conversations_file.stat().st_size
            
            # Count message files
            for msg_file in self.messages_dir.glob("*.json"):
                storage_size_bytes += msg_file.stat().st_size
        except Exception as e:
            logger.warning(f"Could not calculate storage size: {e}")
        
        storage_size_mb = round(storage_size_bytes / (1024 * 1024), 2)
        
        return {
            "total_conversations": len(self._conversations_cache),
            "total_messages": total_messages,
            "storage_size_mb": storage_size_mb,
            "storage_dir": str(self.storage_dir),
            "storage_backend": "Centralized data/ directory",
            "storage_path": str(self.storage_dir)
        }


# Global storage instance
_storage: Optional[ChatStorage] = None


def get_storage() -> ChatStorage:
    """Get the global chat storage instance."""
    global _storage
    if _storage is None:
        _storage = ChatStorage()
    return _storage


def initialize_storage(storage_dir: Optional[Path] = None):
    """Initialize the global storage instance with custom directory."""
    global _storage
    _storage = ChatStorage(storage_dir)
    return _storage
