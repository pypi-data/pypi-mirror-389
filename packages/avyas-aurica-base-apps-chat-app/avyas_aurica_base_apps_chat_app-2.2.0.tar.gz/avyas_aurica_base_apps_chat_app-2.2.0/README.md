# Chat App with Digital Twin Integration

A real-time chat application integrated with the Digital Twin agent system.

## Overview

The Chat App provides a conversational interface that routes messages to each user's Digital Twin running on their local execution node. The DT processes requests, uses tools autonomously, and responds with intelligent, context-aware answers.

## Persistent Storage

**All chat data is stored locally in the file system:**
- **Location**: `apps/chat-app/data/chat/`
- **Conversations**: Stored in `conversations.json`
- **Messages**: Each conversation has its own file in `messages/{conversation_id}.json`
- **Persistence**: Data survives server restarts and is available both locally and via API domain
- **Privacy**: Data stays on your node and is not committed to git

The storage system ensures:
- ✅ Data persistence across server restarts
- ✅ Fast access with in-memory caching
- ✅ Automatic synchronization between local and API domain access
- ✅ User-scoped access control (each user only sees their own conversations)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CLOUD TIER                            │
│                 (api.oneaurica.com)                      │
│                                                          │
│  User Browser → Chat UI → Chat Backend                  │
│                                                          │
│  - User authentication (JWT)                             │
│  - Chat interface & conversation management              │
│  - Message routing to execution node                     │
└─────────────────────────────────────────────────────────┘
                        ↓ HTTP/WebSocket
┌─────────────────────────────────────────────────────────┐
│                  EXECUTION NODE TIER                     │
│                    (localhost:8000)                      │
│                                                          │
│         [Digital Twin Agent]                             │
│              - User's AI Self                            │
│              - Acts with user's JWT                      │
│              - Uses tools autonomously                   │
└─────────────────────────────────────────────────────────┘
```

## Features

### ✅ Digital Twin Integration
- **Cloud-to-Local Communication**: Chat backend routes messages to user's local DT
- **Autonomous Tool Execution**: DT uses tools based on autonomy levels
- **Real-time Responses**: DT responses stream back through chat UI
- **Health Monitoring**: Check DT status and connectivity

### ✅ Conversation Management
- Create and manage multiple conversations
- Persistent conversation history
- Message timestamps and metadata
- User authentication and authorization

### ✅ Error Handling
- Graceful handling when DT is offline
- Connection timeout management
- User-friendly error messages
- Fallback behavior when DT disabled

## API Endpoints

### Conversations

**Create Conversation**
```http
POST /chat-app/api/conversations
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "title": "New Conversation"
}
```

**List Conversations**
```http
GET /chat-app/api/conversations
Authorization: Bearer {jwt_token}
```

**Get Conversation**
```http
GET /chat-app/api/conversations/{conversation_id}
Authorization: Bearer {jwt_token}
```

**Delete Conversation**
```http
DELETE /chat-app/api/conversations/{conversation_id}
Authorization: Bearer {jwt_token}
```

### Messages

**Send Message (to Digital Twin)**
```http
POST /chat-app/api/send
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "conversation_id": "uuid-optional",
  "content": "What's the weather in London?",
  "sender": "user"
}

Response:
{
  "message": {
    "id": "msg-uuid",
    "conversation_id": "conv-uuid",
    "content": "What's the weather in London?",
    "sender": "username",
    "timestamp": "2025-11-03T12:00:00Z"
  },
  "dt_response": {
    "id": "dt-msg-uuid",
    "conversation_id": "conv-uuid",
    "content": "The weather in London is currently 15°C and cloudy...",
    "sender": "digital_twin",
    "timestamp": "2025-11-03T12:00:01Z",
    "metadata": {
      "dt_active": true,
      "tools_used": ["get_current_weather"],
      "autonomous": true,
      "confidence": 0.95
    }
  },
  "conversation_id": "conv-uuid",
  "dt_status": {
    "active": true,
    "confidence": 0.95,
    "tools_used": ["get_current_weather"]
  }
}
```

**Get Messages**
```http
GET /chat-app/api/conversations/{conversation_id}/messages
Authorization: Bearer {jwt_token}
```

### Digital Twin Status

**Get DT Status**
```http
GET /chat-app/api/dt/status
Authorization: Bearer {jwt_token}

Response:
{
  "dt_enabled": true,
  "reachable": true,
  "health": {
    "status": "healthy",
    "dt_active": true
  },
  "capabilities": {
    "tools": ["get_current_weather", "get_user_profile", ...],
    "execution_node": {
      "accessible": true
    }
  },
  "state": {
    "user_id": "user123",
    "dt_active": true
  }
}
```

## Configuration

### Environment Variables

```bash
# Digital Twin Configuration
DIGITAL_TWIN_ENABLED=true              # Enable/disable DT integration
EXECUTION_NODE_URL=http://localhost:8000  # URL of user's execution node

# For development (execution node on localhost)
# For production (each user has their own execution node URL)
```

### app.json
```json
{
  "name": "chat-app",
  "version": "1.0.14",
  "requires": ["authentication"],
  "public_routes": [],
  "description": "Real-time chat application with Digital Twin integration"
}
```

## Usage

### For Development

**Terminal 1 - Start Execution Node (Local DT)**
```bash
cd aurica-base-be
export DIGITAL_TWIN_ENABLED=true
export OPENAI_API_KEY=sk-...
uvicorn src.main:app --port 8000 --reload
```

**Terminal 2 - Start Chat App (Cloud simulation)**
```bash
cd aurica-base-be
export DIGITAL_TWIN_ENABLED=true
export EXECUTION_NODE_URL=http://localhost:8000
uvicorn src.main:app --port 8001 --reload
```

**Browser**
```
Open: http://localhost:8001/chat-app/static/
```

### Testing

**Test DT Integration**
```bash
cd apps/chat-app
python test_dt_integration.py
```

**Manual Testing with curl**
```bash
# 1. Get auth token (login first)
AUTH_TOKEN="your-jwt-token"

# 2. Check DT status
curl http://localhost:8000/chat-app/api/dt/status \
  -H "Authorization: Bearer $AUTH_TOKEN"

# 3. Send a message
curl -X POST http://localhost:8000/chat-app/api/send \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Hello, who are you?",
    "sender": "user"
  }'
```

## Message Flow

1. **User sends message** via chat UI
2. **Chat backend** receives message and saves it
3. **Chat backend routes** to user's Digital Twin (execution node)
4. **Digital Twin processes** the message:
   - Analyzes user intent
   - Decides if tools are needed
   - Executes tools autonomously (if allowed)
   - Generates response
5. **DT response** sent back to chat backend
6. **Chat backend saves** DT response as new message
7. **User sees response** in chat UI

## Digital Twin Metadata

Messages from the Digital Twin include rich metadata:

```json
{
  "sender": "digital_twin",
  "content": "Response text...",
  "metadata": {
    "dt_active": true,              // DT successfully processed
    "thought_process": "...",       // DT's reasoning (optional)
    "tools_used": ["tool1", "tool2"], // Tools executed
    "autonomous": true,             // Acted autonomously
    "confidence": 0.95              // DT's confidence score
  }
}
```

## Error Handling

### DT Offline
```json
{
  "sender": "system",
  "content": "⚠️ Your Digital Twin (execution node) is not reachable...",
  "metadata": {
    "dt_active": false,
    "error": "connection_failed",
    "suggestion": "Start your execution node with: uvicorn..."
  }
}
```

### DT Timeout
```json
{
  "sender": "system",
  "content": "⏱️ Your Digital Twin is taking too long to respond...",
  "metadata": {
    "dt_active": false,
    "error": "timeout"
  }
}
```

## Implementation Details

### Digital Twin Client (`be/dt_client.py`)
- Handles HTTP communication to execution node
- Manages timeouts and retries
- Provides error messages
- Health checking

### Chat API (`be/api/chat.py`)
- Routes messages to DT
- Saves user and DT messages
- Tracks conversation history
- Provides DT status endpoint

## Future Enhancements

- [ ] WebSocket support for real-time streaming
- [ ] DT response streaming (Server-Sent Events)
- [ ] Multi-user conversation support
- [ ] Voice interface integration
- [ ] DT action history viewer
- [ ] Standing permissions UI
- [ ] Conversation export/import
- [ ] Search across conversations

## Troubleshooting

**Problem: DT not reachable**
- Ensure execution node is running: `uvicorn src.main:app --port 8000`
- Check `EXECUTION_NODE_URL` environment variable
- Verify firewall/network settings

**Problem: No DT response**
- Check DT health: `GET /digital-twin/api/health`
- Verify `DIGITAL_TWIN_ENABLED=true`
- Check execution node logs for errors

**Problem: Tools not executing**
- Verify tools are discovered: `GET /digital-twin/api/capabilities`
- Check tool autonomy levels in app.json
- Review DT logs for tool execution errors

## Related Documentation

- [Digital Twin Implementation Plan](../../LLM_AGENT_IMPLEMENTATION_PLAN.md)
- [Digital Twin App](../digital-twin/README.md)
- [Weather App (Tool Example)](../weather-app/README.md)
- [Authentication SDK](../auth-app/SDK_USAGE.md)

## Version History

- **v1.0.14** - Digital Twin integration added
- **v1.0.0** - Initial chat application

---

**Last Updated:** November 3, 2025
**Status:** ✅ Digital Twin Integration Complete
