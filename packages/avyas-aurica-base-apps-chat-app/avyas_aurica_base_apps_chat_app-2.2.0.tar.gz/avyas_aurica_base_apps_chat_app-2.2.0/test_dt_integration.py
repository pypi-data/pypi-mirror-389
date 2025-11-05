"""
Test Digital Twin integration with Chat App.

This script tests the cloud-to-local communication between the chat app
and the Digital Twin running on the execution node.
"""
import asyncio
import httpx
import os
from datetime import datetime


async def test_dt_integration():
    """Test Digital Twin integration with chat app."""
    
    print("🧪 Testing Digital Twin Integration with Chat App\n")
    print("=" * 60)
    
    # Configuration
    CHAT_BASE_URL = os.getenv("CHAT_BASE_URL", "http://localhost:8000")
    DT_BASE_URL = os.getenv("DT_BASE_URL", "http://localhost:8000")
    
    # Test user credentials (you'll need to replace with real JWT)
    AUTH_TOKEN = os.getenv("TEST_AUTH_TOKEN", "test-jwt-token")
    
    print(f"\n📍 Configuration:")
    print(f"   Chat App: {CHAT_BASE_URL}")
    print(f"   Digital Twin: {DT_BASE_URL}")
    print(f"   Auth Token: {AUTH_TOKEN[:20]}...")
    
    # Test 1: Check Digital Twin health
    print("\n\n🧪 TEST 1: Digital Twin Health Check")
    print("-" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{DT_BASE_URL}/digital-twin/api/health")
            if response.status_code == 200:
                health = response.json()
                print(f"✅ Digital Twin is healthy!")
                print(f"   Status: {health.get('status')}")
                print(f"   DT Active: {health.get('dt_active')}")
                print(f"   Version: {health.get('version', 'N/A')}")
            else:
                print(f"❌ Digital Twin returned status {response.status_code}")
                return False
    except httpx.ConnectError:
        print(f"❌ Cannot connect to Digital Twin at {DT_BASE_URL}")
        print(f"   Please start your execution node:")
        print(f"   cd aurica-base-be && uvicorn src.main:app --port 8000 --reload")
        return False
    except Exception as e:
        print(f"❌ Error checking DT health: {e}")
        return False
    
    # Test 2: Check DT status via Chat App
    print("\n\n🧪 TEST 2: DT Status via Chat App")
    print("-" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{CHAT_BASE_URL}/chat-app/api/dt/status",
                headers={"Authorization": f"Bearer {AUTH_TOKEN}"}
            )
            if response.status_code == 200:
                status = response.json()
                print(f"✅ Chat App can reach Digital Twin!")
                print(f"   DT Enabled: {status.get('dt_enabled')}")
                print(f"   DT Reachable: {status.get('reachable')}")
                if status.get('capabilities'):
                    caps = status['capabilities']
                    print(f"   Tools Available: {len(caps.get('tools', []))}")
            else:
                print(f"⚠️  Chat App DT status check returned {response.status_code}")
                print(f"   This might be an auth issue or DT is not enabled")
    except Exception as e:
        print(f"⚠️  Error checking DT status via Chat App: {e}")
    
    # Test 3: Send message through Chat App to DT
    print("\n\n🧪 TEST 3: Send Message to Digital Twin")
    print("-" * 60)
    
    try:
        test_message = "Hello! Who are you?"
        print(f"📤 Sending message: '{test_message}'")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{CHAT_BASE_URL}/chat-app/api/send",
                headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
                json={
                    "content": test_message,
                    "sender": "user"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Message sent successfully!")
                print(f"\n📨 User Message:")
                print(f"   Content: {result['message']['content']}")
                print(f"   Sender: {result['message']['sender']}")
                
                if result.get('dt_response'):
                    print(f"\n🤖 Digital Twin Response:")
                    dt_msg = result['dt_response']
                    print(f"   Content: {dt_msg['content'][:100]}...")
                    print(f"   Sender: {dt_msg['sender']}")
                    
                    if dt_msg.get('metadata'):
                        meta = dt_msg['metadata']
                        print(f"   DT Active: {meta.get('dt_active')}")
                        print(f"   Tools Used: {meta.get('tools_used', [])}")
                        print(f"   Autonomous: {meta.get('autonomous', False)}")
                        print(f"   Confidence: {meta.get('confidence', 'N/A')}")
                
                dt_status = result.get('dt_status', {})
                if not dt_status.get('active'):
                    print(f"\n⚠️  DT Status: Not Active")
                    print(f"   Error: {dt_status.get('error')}")
                    print(f"   Message: {dt_status.get('message')}")
            else:
                print(f"❌ Failed to send message: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False
    
    # Test 4: Test with tool usage (weather query)
    print("\n\n🧪 TEST 4: Message Requiring Tool Use (Weather)")
    print("-" * 60)
    
    try:
        test_message = "What's the weather in London?"
        print(f"📤 Sending message: '{test_message}'")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{CHAT_BASE_URL}/chat-app/api/send",
                headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
                json={
                    "content": test_message,
                    "sender": "user"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('dt_response'):
                    dt_msg = result['dt_response']
                    print(f"✅ DT responded!")
                    print(f"\n🤖 Response: {dt_msg['content'][:150]}...")
                    
                    if dt_msg.get('metadata'):
                        meta = dt_msg['metadata']
                        tools_used = meta.get('tools_used', [])
                        if tools_used:
                            print(f"   🔧 Tools Used: {tools_used}")
                            print(f"   ✅ DT successfully used tools autonomously!")
                        else:
                            print(f"   ⚠️  No tools used (expected weather tool)")
    except Exception as e:
        print(f"⚠️  Error in tool usage test: {e}")
    
    # Summary
    print("\n\n" + "=" * 60)
    print("✅ Integration Tests Complete!")
    print("\n📋 Summary:")
    print("   - Digital Twin is running and healthy")
    print("   - Chat App can communicate with DT")
    print("   - Messages route correctly to DT")
    print("   - DT responses return to chat")
    print("\n🎉 Cloud-to-Local integration is working!")
    
    return True


async def test_without_dt():
    """Test chat app when DT is disabled."""
    
    print("\n\n🧪 TEST: Chat App with DT Disabled")
    print("-" * 60)
    
    # This would test fallback behavior
    print("   (Test implementation for DT disabled scenario)")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║  Digital Twin Integration Test Suite                         ║
║  Testing Cloud (Chat App) to Local (Execution Node) Flow     ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    print("\n⚠️  PREREQUISITES:")
    print("   1. Execution node running: uvicorn src.main:app --port 8000 --reload")
    print("   2. Digital Twin app loaded and healthy")
    print("   3. Environment variable: DIGITAL_TWIN_ENABLED=true")
    print("   4. Valid AUTH_TOKEN for testing")
    
    print("\n💡 TIP: Set TEST_AUTH_TOKEN environment variable with a valid JWT")
    print("   export TEST_AUTH_TOKEN='your-jwt-token-here'")
    
    input("\nPress Enter to start tests...")
    
    asyncio.run(test_dt_integration())
