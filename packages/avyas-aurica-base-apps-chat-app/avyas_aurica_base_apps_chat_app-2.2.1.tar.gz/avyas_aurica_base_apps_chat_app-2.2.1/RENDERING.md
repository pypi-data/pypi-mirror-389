# Chat App Dynamic Rendering System

This document describes the dynamic rendering system that allows the chat interface to intelligently display different types of data with appropriate UI components.

## Overview

The rendering system automatically detects data types in assistant responses and renders them with appropriate UI components:
- **Profile Cards** for user profile data
- **Tables** for arrays of structured data
- **JSON Viewers** for structured data
- **Execution Status** indicators for function calls
- **Success/Error/Warning/Info** alerts
- **Code Blocks** with syntax highlighting
- **Markdown** for formatted text

## Architecture

### Backend Components

#### 1. `rendering_blocks.py`
Defines the rendering block registry and data type detection:

```python
from rendering_blocks import get_rendering_registry, RenderBlock, RenderType

# Auto-detect render type
registry = get_rendering_registry()
render_block = registry.create_render_block(data)
```

**Available Render Types:**
- `TEXT` - Plain text
- `CODE` - Code with syntax highlighting
- `JSON` - JSON data viewer
- `PROFILE_CARD` - User profile card
- `TABLE` - Data table
- `LIST` - Bullet/numbered lists
- `FORM` - Forms (future)
- `CARD` - Generic card
- `EXECUTION_STATUS` - Function execution indicator
- `ERROR` / `SUCCESS` / `WARNING` / `INFO` - Alert messages
- `MARKDOWN` - Formatted text
- `CHART` / `IMAGE` / `FILE` / `LINK` / `TIMELINE` / `STEPS` - (future)

#### 2. `api/render.py`
API endpoints for message parsing and rendering:

**POST `/chat-app/api/render/parse`**
Parse a message and return rendering blocks:

```json
{
  "content": "Get my profile\nAssistant\n⚡ Executing...\n\n• Calling get_user_profile()\n✅ get_user_profile:\n```json\n{\n  \"user_id\": \"...\",\n  \"username\": \"avyasnew\",\n  \"email\": \"amitvyas.cse@gmail.com\"\n}\n```",
  "sender": "assistant"
}
```

Response:
```json
{
  "original_content": "...",
  "blocks": [
    {
      "type": "execution_status",
      "data": {"content": "Executing...", "status": "executing"},
      "metadata": {"animated": true}
    },
    {
      "type": "profile_card",
      "data": {"content": {...}},
      "metadata": {"username": "avyasnew", "email": "..."}
    }
  ],
  "metadata": {
    "has_structured_data": true,
    "json_block_count": 1
  }
}
```

**GET `/chat-app/api/render/templates`**
Get available rendering templates and render types.

#### 3. `api/chat.py` Integration
The chat API automatically parses messages and adds rendering metadata:

```python
def parse_message_for_rendering(content: str, sender: str = "assistant") -> dict:
    """Parse message content and extract rendering blocks."""
    # Returns: {"render_blocks": [...], "metadata": {...}}
```

Messages returned from `/conversations/{id}/messages` now include:
```json
{
  "id": "...",
  "content": "...",
  "sender": "assistant",
  "render_blocks": [...],
  "render_metadata": {...}
}
```

### Frontend Components

#### 1. `message-renderer.js`
JavaScript class that handles dynamic rendering:

```javascript
const renderer = new MessageRenderer();

// Render a message with render blocks
const renderedElement = renderer.render(message);

// Or render a specific block
const blockElement = renderer.renderBlock(block);
```

**Supported Renderers:**
- `renderText()` - Plain text
- `renderMarkdown()` - Basic markdown parsing
- `renderCode()` - Code blocks with language support
- `renderJson()` - Pretty-printed JSON
- `renderProfileCard()` - Beautiful profile cards
- `renderTable()` - Sortable data tables
- `renderList()` - Bullet/numbered lists
- `renderExecutionStatus()` - Animated execution indicators
- `renderSuccess/Error/Warning/Info()` - Alert messages

#### 2. `message-renderer.css`
Comprehensive styles for all rendering blocks:

- Profile cards with gradient backgrounds
- Responsive tables
- Syntax-highlighted code blocks
- Animated execution status indicators
- Alert boxes with appropriate colors
- Dark mode support

#### 3. `index.html` Integration
The chat interface automatically uses the renderer:

```javascript
// Messages with render_blocks use dynamic rendering
if (msg.render_blocks && msg.render_blocks.length > 0) {
    const renderedContent = messageRenderer.render(msg);
    messageEl.appendChild(renderedContent);
}
```

## Usage Examples

### Example 1: Profile Data
When the assistant returns user profile data:

```json
{
  "user_id": "9Q9LSOGfxtBo...",
  "username": "avyasnew",
  "email": "amitvyas.cse@gmail.com",
  "display_name": "Amit Vyas",
  "role": "admin",
  "mobile_number": "9925188036",
  "created_at": "2025-10-15T18:27:19.895142"
}
```

It's automatically rendered as a beautiful profile card with:
- Avatar
- Display name
- Username
- Email with icon
- Role badge
- Mobile number with verification status
- Member since date

### Example 2: Function Execution
When the assistant calls a function:

```
⚡ Executing...

• Calling get_user_profile()
✅ get_user_profile:
```json
{...}
```
```

The renderer creates:
1. **Execution Status** block (animated ⚡)
2. **Success** block (✅)
3. **Profile Card** block (from JSON data)

### Example 3: Table Data
When returning a list of items:

```json
[
  {"name": "Item 1", "status": "active", "count": 42},
  {"name": "Item 2", "status": "inactive", "count": 17}
]
```

Renders as a sortable table with headers and hover effects.

## Extending the System

### Adding a New Renderer

#### Backend:
```python
# In rendering_blocks.py
registry.register_renderer(
    name="my_custom_type",
    detector=lambda data: isinstance(data, dict) and "special_key" in data,
    render_type=RenderType.CARD,
    metadata_extractor=lambda data: {"title": data.get("special_key")}
)
```

#### Frontend:
```javascript
// In message-renderer.js
class MessageRenderer {
    constructor() {
        this.renderTypes['my_custom_type'] = this.renderCustomType.bind(this);
    }
    
    renderCustomType(data, metadata) {
        const container = document.createElement('div');
        container.className = 'render-custom-type';
        // ... your rendering logic
        return container;
    }
}
```

```css
/* In message-renderer.css */
.render-custom-type {
    /* Your custom styles */
}
```

## Data Flow

```
1. User sends message
   ↓
2. Digital Twin processes and returns response with JSON data
   ↓
3. Backend (chat.py) calls parse_message_for_rendering()
   ↓
4. Rendering registry detects data types and creates render blocks
   ↓
5. Message stored with render_blocks metadata
   ↓
6. Frontend loads message
   ↓
7. MessageRenderer.render() creates appropriate DOM elements
   ↓
8. Styled components displayed to user
```

## Benefits

1. **Automatic**: No manual formatting needed - the system detects data types
2. **Extensible**: Easy to add new render types and components
3. **Consistent**: All data of the same type looks the same
4. **Beautiful**: Professional UI components for each data type
5. **Responsive**: Works on mobile and desktop
6. **Dark Mode**: Supports dark theme automatically
7. **Performance**: Only renders what's needed

## Future Enhancements

- **Charts**: Line, bar, pie charts for numeric data
- **Images**: Image galleries and lightbox
- **Files**: File attachments with download
- **Forms**: Interactive forms within chat
- **Timeline**: Event timelines
- **Steps**: Step-by-step procedures
- **Interactive Tables**: Sorting, filtering, pagination
- **Code Syntax Highlighting**: Using Prism or Highlight.js
- **LaTeX Math**: For mathematical expressions
- **Mermaid Diagrams**: Flowcharts, sequence diagrams, etc.

## Testing

### Test the Parse Endpoint
```bash
curl -X POST http://localhost:8000/chat-app/api/render/parse \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "✅ get_user_profile:\n```json\n{\"username\": \"test\"}\n```",
    "sender": "assistant"
  }'
```

### Test in Chat Interface
1. Ask: "Get my profile"
2. The response should show a beautifully formatted profile card
3. Try: "List all nodes" - Should show a table
4. Try: "What's the node status?" - Should show JSON or structured data

## Troubleshooting

**Render blocks not showing:**
- Check browser console for JavaScript errors
- Ensure `message-renderer.js` is loaded
- Verify `messageRenderer` is initialized in `init()`

**Styling issues:**
- Check `message-renderer.css` is loaded
- Verify CSS variables are defined in `:root`
- Check browser compatibility

**Backend not parsing:**
- Verify `rendering_blocks.py` is imported in `chat.py`
- Check `parse_message_for_rendering()` is called
- Look for errors in server logs
