"""
Real-time test with backend log capture
Tests WebSocket broadcast in background task
"""
import sys
import json
import time
import asyncio
import requests
import websockets
from datetime import datetime
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parent.parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

received_messages = []


async def websocket_client():
    """Connect to WebSocket and listen for messages"""
    global received_messages
    
    print("[WS] Connecting...")
    async with websockets.connect(WS_URL) as ws:
        print("[WS] Connected!")
        
        # Send initial ping
        await ws.send(json.dumps({"action": "ping"}))
        
        while True:
            try:
                message = await asyncio.wait_for(ws.recv(), timeout=1)
                data = json.loads(message)
                received_messages.append(data)
                msg_type = data.get('type', 'unknown')
                print(f"[WS] Received: type={msg_type}")
                
                if msg_type in ['feishu-chat-message', 'feishu_chat_message']:
                    print(f"[WS] >>> FEISHU MESSAGE: {data.get('data', {}).get('content', '')[:50]}")
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"[WS] Error: {e}")
                break


async def run_test():
    """Run the test"""
    global received_messages
    
    print("\n" + "="*60)
    print("Real-time WebSocket Broadcast Test")
    print("="*60)
    
    # Start WebSocket client in background
    ws_task = asyncio.create_task(websocket_client())
    
    # Wait for connection
    await asyncio.sleep(2)
    
    # Test 1: Direct broadcast via API
    print("\n[TEST 1] Direct broadcast via /test-broadcast...")
    resp = requests.post(f"{BASE_URL}/api/feishu/test-broadcast")
    print(f"  Response: {resp.json()}")
    
    await asyncio.sleep(2)
    
    # Check if received
    test_broadcasts = [m for m in received_messages if m.get('type') == 'feishu-chat-message']
    print(f"  Received broadcasts: {len(test_broadcasts)}")
    
    # Test 2: Webhook with simulated message
    print("\n[TEST 2] Webhook simulated message...")
    
    # Clear previous messages
    received_messages.clear()
    
    test_msg_id = f"realtime_test_{int(time.time())}"
    webhook_payload = {
        "schema": "2.0",
        "header": {
            "event_id": test_msg_id,
            "event_type": "im.message.receive_v1",
            "create_time": str(int(time.time() * 1000)),
            "token": "test_token",
            "app_id": "cli_test",
            "tenant_key": "test_tenant"
        },
        "event": {
            "sender": {
                "sender_id": {"user_id": "test_user"},
                "sender_type": "user"
            },
            "message": {
                "message_id": test_msg_id,
                "root_id": "",
                "parent_id": "",
                "create_time": str(int(time.time() * 1000)),
                "chat_id": "test_chat_realtime",
                "message_type": "text",
                "content": json.dumps({"text": f"Realtime test {datetime.now().strftime('%H:%M:%S')}"}),
                "mentions": []
            }
        }
    }
    
    resp = requests.post(f"{BASE_URL}/api/feishu/webhook", json=webhook_payload)
    print(f"  Response: {resp.json()}")
    
    # Wait for broadcast
    print("  Waiting for broadcast...")
    await asyncio.sleep(5)
    
    # Check results
    feishu_msgs = [m for m in received_messages if m.get('type') in ['feishu-chat-message', 'feishu_chat_message']]
    
    if feishu_msgs:
        print(f"  [OK] Received {len(feishu_msgs)} feishu messages via WebSocket")
    else:
        print(f"  [FAIL] No feishu messages received!")
        print(f"  Received types: {[m.get('type') for m in received_messages]}")
    
    # Cancel WebSocket task
    ws_task.cancel()
    try:
        await ws_task
    except asyncio.CancelledError:
        pass
    
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print(f"Test 1 (Direct broadcast): {'PASS' if test_broadcasts else 'FAIL'}")
    print(f"Test 2 (Webhook broadcast): {'PASS' if feishu_msgs else 'FAIL'}")
    print("="*60 + "\n")
    
    return len(test_broadcasts) > 0 or len(feishu_msgs) > 0


if __name__ == "__main__":
    asyncio.run(run_test())
