"""
Startup handler for chat-app
This module is automatically called when the app is loaded
"""
import asyncio
from pathlib import Path
import sys

# Add app directory to path for imports
chat_be_dir = Path(__file__).parent
if str(chat_be_dir) not in sys.path:
    sys.path.insert(0, str(chat_be_dir))

from storage import initialize_storage, get_storage


async def startup():
    """
    Startup routine - called when app is loaded
    Initializes persistent storage for chat conversations and messages
    """
    print("💬 Chat App: Starting up...")
    
    try:
        # Initialize storage
        storage = initialize_storage()
        
        # Load existing data
        storage.load_all_data()
        
        # Get stats
        stats = storage.get_stats()
        print(f"✅ Chat storage initialized successfully")
        print(f"   📊 Conversations: {stats['total_conversations']}")
        print(f"   📝 Messages: {stats['total_messages']}")
        print(f"   💾 Storage: {stats['storage_size_mb']} MB")
        print(f"   📂 Location: {stats['storage_dir']}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to initialize chat storage: {e}")
        import traceback
        traceback.print_exc()
        return False


async def shutdown():
    """
    Shutdown routine - called when app is unloaded
    """
    print("💬 Chat App: Shutting down...")
    
    try:
        storage = get_storage()
        stats = storage.get_stats()
        print(f"✅ Chat app shutdown complete")
        print(f"   Final stats: {stats['total_conversations']} conversations, {stats['total_messages']} messages")
    except Exception as e:
        print(f"⚠️  Error during chat app shutdown: {e}")
    
    print("✅ Chat App: Shutdown complete")
