"""
Rendering Blocks Registry for Chat App
Defines how different types of data should be rendered in the chat interface.
"""
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel


class RenderType(str, Enum):
    """Types of rendering blocks available."""
    TEXT = "text"
    CODE = "code"
    JSON = "json"
    PROFILE_CARD = "profile_card"
    TABLE = "table"
    LIST = "list"
    FORM = "form"
    CARD = "card"
    EXECUTION_STATUS = "execution_status"
    ERROR = "error"
    SUCCESS = "success"
    WARNING = "warning"
    INFO = "info"
    MARKDOWN = "markdown"
    CHART = "chart"
    IMAGE = "image"
    FILE = "file"
    LINK = "link"
    TIMELINE = "timeline"
    STEPS = "steps"


class RenderBlock(BaseModel):
    """Definition of a rendering block."""
    type: RenderType
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True


class RenderingRegistry:
    """Registry for rendering blocks and data type detection."""
    
    def __init__(self):
        self.renderers = {}
        self._register_default_renderers()
    
    def _register_default_renderers(self):
        """Register default rendering blocks."""
        
        # Profile Card Renderer
        self.register_renderer(
            name="profile",
            detector=lambda data: isinstance(data, dict) and "user_id" in data and "username" in data,
            render_type=RenderType.PROFILE_CARD,
            metadata_extractor=self._extract_profile_metadata
        )
        
        # JSON Renderer
        self.register_renderer(
            name="json",
            detector=lambda data: isinstance(data, dict) and not self._is_special_type(data),
            render_type=RenderType.JSON,
            metadata_extractor=lambda data: {"keys": list(data.keys())}
        )
        
        # List Renderer
        self.register_renderer(
            name="list",
            detector=lambda data: isinstance(data, list),
            render_type=RenderType.LIST,
            metadata_extractor=lambda data: {"count": len(data), "item_type": type(data[0]).__name__ if data else "empty"}
        )
        
        # Execution Status Renderer
        self.register_renderer(
            name="execution_status",
            detector=lambda data: isinstance(data, dict) and "function_name" in data and "status" in data,
            render_type=RenderType.EXECUTION_STATUS,
            metadata_extractor=lambda data: {"function": data.get("function_name"), "status": data.get("status")}
        )
        
        # Error Renderer
        self.register_renderer(
            name="error",
            detector=lambda data: isinstance(data, dict) and ("error" in data or "error_message" in data),
            render_type=RenderType.ERROR,
            metadata_extractor=lambda data: {"error": data.get("error") or data.get("error_message")}
        )
        
        # Table Renderer (for arrays of objects)
        self.register_renderer(
            name="table",
            detector=lambda data: isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict),
            render_type=RenderType.TABLE,
            metadata_extractor=lambda data: {
                "columns": list(data[0].keys()) if data else [],
                "row_count": len(data)
            }
        )
    
    def register_renderer(self, name: str, detector: callable, render_type: RenderType, 
                         metadata_extractor: Optional[callable] = None):
        """Register a new renderer."""
        self.renderers[name] = {
            "detector": detector,
            "render_type": render_type,
            "metadata_extractor": metadata_extractor or (lambda data: {})
        }
    
    def detect_render_type(self, data: Any) -> RenderType:
        """Detect the appropriate render type for given data."""
        if isinstance(data, str):
            # Check if it's markdown or code
            if data.startswith("```"):
                return RenderType.CODE
            elif data.startswith("#") or "*" in data or "[" in data:
                return RenderType.MARKDOWN
            return RenderType.TEXT
        
        # Check custom renderers
        for name, renderer in self.renderers.items():
            try:
                if renderer["detector"](data):
                    return renderer["render_type"]
            except Exception:
                continue
        
        # Default fallback
        return RenderType.TEXT
    
    def create_render_block(self, data: Any, render_type: Optional[RenderType] = None) -> RenderBlock:
        """Create a render block for the given data."""
        if render_type is None:
            render_type = self.detect_render_type(data)
        
        # Extract metadata based on renderer
        metadata = {}
        for name, renderer in self.renderers.items():
            try:
                if renderer["render_type"] == render_type and renderer["detector"](data):
                    metadata = renderer["metadata_extractor"](data)
                    break
            except Exception:
                continue
        
        return RenderBlock(
            type=render_type,
            data=self._normalize_data(data, render_type),
            metadata=metadata
        )
    
    def _normalize_data(self, data: Any, render_type: RenderType) -> Dict[str, Any]:
        """Normalize data for rendering."""
        if isinstance(data, str):
            return {"content": data}
        elif isinstance(data, (dict, list)):
            return {"content": data}
        else:
            return {"content": str(data)}
    
    def _is_special_type(self, data: dict) -> bool:
        """Check if dict is a special type (not just generic JSON)."""
        special_keys = ["user_id", "username", "error", "function_name", "status"]
        return any(key in data for key in special_keys)
    
    def _extract_profile_metadata(self, data: dict) -> dict:
        """Extract metadata from profile data."""
        return {
            "username": data.get("username"),
            "email": data.get("email"),
            "role": data.get("role"),
            "display_name": data.get("display_name")
        }


# Predefined rendering templates for common patterns
RENDERING_TEMPLATES = {
    "profile_card": {
        "type": RenderType.PROFILE_CARD,
        "fields": [
            {"key": "display_name", "label": "Name", "icon": "person"},
            {"key": "username", "label": "Username", "icon": "at"},
            {"key": "email", "label": "Email", "icon": "envelope"},
            {"key": "role", "label": "Role", "icon": "shield"},
            {"key": "mobile_number", "label": "Mobile", "icon": "phone"},
            {"key": "created_at", "label": "Member Since", "icon": "calendar", "format": "date"}
        ]
    },
    "execution_status": {
        "type": RenderType.EXECUTION_STATUS,
        "statuses": {
            "executing": {"icon": "⚡", "color": "blue", "label": "Executing"},
            "success": {"icon": "✅", "color": "green", "label": "Success"},
            "error": {"icon": "❌", "color": "red", "label": "Error"},
            "pending": {"icon": "⏳", "color": "orange", "label": "Pending"}
        }
    },
    "table": {
        "type": RenderType.TABLE,
        "features": ["sortable", "searchable", "paginated"]
    },
    "list": {
        "type": RenderType.LIST,
        "variants": ["bullet", "numbered", "checklist", "cards"]
    }
}


# Function calling detection
def detect_function_call_pattern(text: str) -> Optional[Dict[str, Any]]:
    """Detect if text contains function call patterns."""
    if "Executing..." in text or "Calling" in text:
        # Extract function name
        if "(" in text and ")" in text:
            start = text.find("Calling") + 8 if "Calling" in text else 0
            end = text.find("(", start)
            if end > start:
                function_name = text[start:end].strip()
                return {
                    "type": "function_call",
                    "function_name": function_name,
                    "status": "executing"
                }
    elif "✅" in text and ":" in text:
        # Function result
        lines = text.split("\n")
        for line in lines:
            if "✅" in line:
                parts = line.split(":")
                if len(parts) >= 2:
                    function_name = parts[0].replace("✅", "").strip()
                    return {
                        "type": "function_result",
                        "function_name": function_name,
                        "status": "success"
                    }
    return None


# Global registry instance
rendering_registry = RenderingRegistry()


def get_rendering_registry() -> RenderingRegistry:
    """Get the global rendering registry instance."""
    return rendering_registry
