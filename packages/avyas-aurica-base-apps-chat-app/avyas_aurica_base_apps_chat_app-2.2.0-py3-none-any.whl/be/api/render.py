"""
Rendering API endpoints for parsing and structuring chat messages
with rendering metadata.
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import json
import re

# Import Aurica Auth SDK
try:
    from src.aurica_auth import protected, get_current_user
except ImportError:
    print("⚠️  Warning: Could not import aurica_auth SDK")
    def protected(func):
        return func
    def get_current_user(request, required=True):
        return type('User', (), {"username": "unknown", "user_id": "unknown"})()

# Import rendering blocks
import sys
from pathlib import Path
chat_be_dir = Path(__file__).parent.parent
if str(chat_be_dir) not in sys.path:
    sys.path.insert(0, str(chat_be_dir))

from rendering_blocks import (
    RenderBlock, RenderType, get_rendering_registry,
    detect_function_call_pattern, RENDERING_TEMPLATES
)

router = APIRouter()


class ParseMessageRequest(BaseModel):
    """Request to parse a message and return rendering blocks."""
    content: str
    sender: str = "assistant"


class ParsedMessage(BaseModel):
    """Parsed message with rendering blocks."""
    original_content: str
    blocks: List[RenderBlock]
    metadata: Optional[Dict[str, Any]] = None


@router.post("/parse", response_model=ParsedMessage)
@protected
async def parse_message(request: Request, req: ParseMessageRequest):
    """
    Parse a message and return structured rendering blocks.
    
    This endpoint analyzes message content and determines:
    - What type of data is being displayed
    - How it should be rendered (card, table, json, etc.)
    - What metadata should be shown
    """
    user = get_current_user(request)
    registry = get_rendering_registry()
    
    content = req.content
    blocks = []
    metadata = {}
    
    # Pattern 1: Detect function execution patterns
    function_pattern = detect_function_call_pattern(content)
    if function_pattern:
        metadata["has_function_call"] = True
        metadata["function_info"] = function_pattern
    
    # Pattern 2: Extract JSON blocks from markdown code fences
    json_blocks = re.findall(r'```json\s*(.*?)\s*```', content, re.DOTALL)
    
    if json_blocks:
        # Split content into text and JSON parts
        parts = re.split(r'```json\s*.*?\s*```', content, flags=re.DOTALL)
        
        for i, part in enumerate(parts):
            # Add text block if not empty
            part = part.strip()
            if part:
                # Check for execution status patterns
                if "Executing" in part or "Calling" in part:
                    blocks.append(RenderBlock(
                        type=RenderType.EXECUTION_STATUS,
                        data={"content": part, "status": "executing"},
                        metadata={"animated": True}
                    ))
                elif "✅" in part:
                    blocks.append(RenderBlock(
                        type=RenderType.SUCCESS,
                        data={"content": part},
                        metadata={"icon": "✅"}
                    ))
                else:
                    blocks.append(RenderBlock(
                        type=RenderType.MARKDOWN,
                        data={"content": part},
                        metadata={}
                    ))
            
            # Add JSON block if exists
            if i < len(json_blocks):
                try:
                    json_data = json.loads(json_blocks[i])
                    render_block = registry.create_render_block(json_data)
                    blocks.append(render_block)
                except json.JSONDecodeError:
                    # If not valid JSON, treat as code
                    blocks.append(RenderBlock(
                        type=RenderType.CODE,
                        data={"content": json_blocks[i], "language": "json"},
                        metadata={}
                    ))
    
    else:
        # No JSON blocks found - try to parse as single block
        try:
            # Try parsing as pure JSON
            data = json.loads(content)
            render_block = registry.create_render_block(data)
            blocks.append(render_block)
        except json.JSONDecodeError:
            # Regular text/markdown
            blocks.append(RenderBlock(
                type=RenderType.MARKDOWN,
                data={"content": content},
                metadata={}
            ))
    
    return ParsedMessage(
        original_content=content,
        blocks=blocks,
        metadata=metadata
    )


@router.get("/templates")
async def get_templates():
    """Get available rendering templates."""
    return {
        "templates": RENDERING_TEMPLATES,
        "render_types": [t.value for t in RenderType]
    }


@router.post("/preview")
@protected
async def preview_render_block(request: Request, data: Dict[str, Any]):
    """
    Preview how data would be rendered.
    
    This is useful for testing and debugging rendering blocks.
    """
    registry = get_rendering_registry()
    
    render_type = data.get("render_type")
    content = data.get("data")
    
    if render_type:
        try:
            render_type_enum = RenderType(render_type)
            render_block = RenderBlock(
                type=render_type_enum,
                data={"content": content},
                metadata={}
            )
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid render type: {render_type}")
    else:
        # Auto-detect render type
        render_block = registry.create_render_block(content)
    
    return {
        "render_block": render_block.dict(),
        "html_preview": generate_html_preview(render_block)
    }


def generate_html_preview(block: RenderBlock) -> str:
    """Generate HTML preview for a render block (for testing)."""
    if block.type == RenderType.PROFILE_CARD:
        data = block.data.get("content", {})
        return f"""
        <div class="profile-card">
            <h3>{data.get('display_name', 'Unknown')}</h3>
            <p>@{data.get('username', 'unknown')}</p>
            <p>{data.get('email', 'No email')}</p>
        </div>
        """
    elif block.type == RenderType.TABLE:
        return "<table>...</table>"
    else:
        return f"<div>{block.data.get('content', '')}</div>"
