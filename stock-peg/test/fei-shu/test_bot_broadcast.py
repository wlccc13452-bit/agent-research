"""
Test Feishu Bot WebSocket broadcast
"""
import asyncio
import sys
import os

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
sys.path.insert(0, backend_path)

# Import only what we need to avoid module import issues
import importlib.util
spec = importlib.util.spec_from_file_location("websocket_manager", 
    os.path.join(backend_path, "services", "websocket_manager.py"))
ws_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ws_module)
manager = ws_module.manager




async def test_broadcast():
    """Test if broadcast works correctly"""
    print("=" * 60)
    print("Testing Feishu Bot WebSocket Broadcast")
    print("=" * 60)
    
    # Create a mock WebSocket connection
    class MockWebSocket:
        def __init__(self):
            self.messages = []
            
        async def accept(self):
            print("[OK] Mock WebSocket accepted")
            
        async def send_json(self, message):
            self.messages.append(message)
            print(f"[OK] Mock WebSocket received: {message}")
    
    # Add mock connection
    mock_ws = MockWebSocket()
    await manager.connect(mock_ws)
    print(f"[OK] Mock WebSocket connected. Active connections: {manager.get_connection_count()}")
    
    # Test 1: Direct broadcast (user message)
    print("\n[Test 1] Broadcasting user message...")
    await manager.broadcast({
        "type": "feishu-chat-message",
        "data": {
            "chat_id": "test_chat",
            "message_id": "test_msg_1",
            "sender_type": "user",
            "content": "Test direct broadcast"
        }
    })
    
    if mock_ws.messages:
        print(f"[PASS] Test 1 PASSED: Received {len(mock_ws.messages)} message(s)")
        for msg in mock_ws.messages:
            print(f"   - Type: {msg.get('type')}")
    else:
        print("[FAIL] Test 1 FAILED: No message received")
    
    # Test 2: Broadcast bot message
    print("\n[Test 2] Broadcasting bot message...")
    from datetime import datetime
    mock_ws.messages = []  # Clear previous messages
    
    await manager.broadcast({
        "type": "feishu-chat-message",
        "data": {
            "chat_id": "test_chat_2",
            "message_id": "test_msg_2",
            "sender_id": "bot",
            "sender_type": "bot",
            "content": "Test bot broadcast",
            "send_time": datetime.now().isoformat()
        }
    })
    
    if mock_ws.messages:
        print(f"[PASS] Test 2 PASSED: Received {len(mock_ws.messages)} message(s)")
        for msg in mock_ws.messages:
            print(f"   - Type: {msg.get('type')}, Sender: {msg.get('data', {}).get('sender_type')}")
    else:
        print("[FAIL] Test 2 FAILED: No message received")
    
    # Cleanup
    manager.disconnect(mock_ws)
    print(f"\n[OK] Mock WebSocket disconnected. Active connections: {manager.get_connection_count()}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_broadcast())
