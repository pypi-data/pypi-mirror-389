"""
Test the rendering block detection
"""
import sys
from pathlib import Path

# Add chat-app to path
chat_be_dir = Path(__file__).parent
sys.path.insert(0, str(chat_be_dir))

from rendering_blocks import get_rendering_registry

# Test data
test_profile = {
    "user_id": "9Q9LSOGfxtBo64L2Lu41USZSpGFnTMo1Iua2fFSgkyc",
    "username": "avyasnew",
    "email": "amitvyas.cse@gmail.com",
    "display_name": "Amit Vyas",
    "role": "admin",
    "mobile_number": "9925188036",
    "mobile_verified": False,
    "created_at": "2025-10-15T18:27:19.895142"
}

registry = get_rendering_registry()

print("=" * 60)
print("Testing Rendering Block Detection")
print("=" * 60)

# Test 1: Detect render type
print("\n1. Testing detect_render_type():")
render_type = registry.detect_render_type(test_profile)
print(f"   Input: {list(test_profile.keys())}")
print(f"   Detected type: {render_type}")

# Test 2: Create render block
print("\n2. Testing create_render_block():")
render_block = registry.create_render_block(test_profile)
print(f"   Block type: {render_block.type}")
print(f"   Block data keys: {list(render_block.data.keys())}")
print(f"   Block metadata: {render_block.metadata}")

# Test 3: Test with message content
print("\n3. Testing with message content:")
message_content = """⚡ Executing...

• Calling get_user_profile()
✅ get_user_profile:
```json
{
  "user_id": "9Q9LSOGfxtBo64L2Lu41USZSpGFnTMo1Iua2fFSgkyc",
  "username": "avyasnew",
  "email": "amitvyas.cse@gmail.com",
  "display_name": "Amit Vyas",
  "role": "admin"
}
```
"""

from api.chat import parse_message_for_rendering

result = parse_message_for_rendering(message_content, "assistant")
print(f"   Number of blocks: {len(result['render_blocks'])}")
for i, block in enumerate(result['render_blocks']):
    print(f"   Block {i}: {block['type']}")
    if block['type'] == 'profile_card':
        print(f"      ✅ PROFILE CARD DETECTED!")
        print(f"      Data: {block.get('data', {}).get('content', {})}")

print("\n" + "=" * 60)
print("Test complete!")
print("=" * 60)
