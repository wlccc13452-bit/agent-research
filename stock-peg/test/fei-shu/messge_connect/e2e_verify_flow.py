"""
End-to-end verification test for Feishu message flow
Tests from webhook to frontend API call
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

# Store received messages
received_messages = []

async def websocket_listener():
    """Listen for WebSocket messages"""
    global received_messages
    
    print("\n[WebSocket] Connecting...")
    async with websockets.connect(WS_URL) as ws:
        print("[WebSocket] Connected")
        
        # Wait for test broadcast
        start = time.time()
        while time.time() - start < 10:
            try:
                message = await asyncio.wait_for(ws.recv(), timeout=1)
                data = json.loads(message)
                received_messages.append(data)
                print(f"[WebSocket] Received: type={data.get('type')}")
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"[WebSocket] Error: {e}")
                break


async def run_e2e_test():
    """Run end-to-end test"""
    global received_messages
    
    print("\n" + "="*60)
    print("End-to-End Feishu Message Flow Test")
    print("="*60)
    
    # Step 1: Check WebSocket connections
    print("\n1. Checking WebSocket connections...")
    resp = requests.get(f"{BASE_URL}/api/feishu/websocket-status")
    data = resp.json()
    print(f"   Active connections: {data['active_connections']}")
    
    if data['active_connections'] == 0:
        print("   [WARN] No frontend WebSocket connections detected")
    
    # Step 2: Get current messages count
    print("\n2. Getting current message count...")
    resp = requests.get(f"{BASE_URL}/api/feishu-chat/recent?limit=100")
    before_messages = resp.json()
    before_count = len(before_messages)
    print(f"   Current message count: {before_count}")
    
    # Step 3: Create WebSocket listener task
    print("\n3. Starting WebSocket listener...")
    
    # Step 4: Send test webhook
    test_msg_id = f"e2e_test_{int(time.time())}"
    test_content = f"E2E Verification {datetime.now().strftime('%H:%M:%S')}"
    
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
                "sender_id": {"user_id": "e2e_user"},
                "sender_type": "user"
            },
            "message": {
                "message_id": test_msg_id,
                "root_id": "",
                "parent_id": "",
                "create_time": str(int(time.time() * 1000)),
                "chat_id": "e2e_test_chat",
                "message_type": "text",
                "content": json.dumps({"text": test_content}),
                "mentions": []
            }
        }
    }
    
    print(f"\n4. Sending webhook message...")
    print(f"   Message ID: {test_msg_id}")
    print(f"   Content: {test_content}")
    
    # Start WebSocket listener in background
    listener_task = asyncio.create_task(websocket_listener())
    
    # Small delay to let WebSocket connect
    await asyncio.sleep(1)
    
    # Send webhook
    resp = requests.post(
        f"{BASE_URL}/api/feishu/webhook",
        json=webhook_payload,
        timeout=5
    )
    
    print(f"   Response: {resp.status_code} - {resp.json()}")
    
    # Wait for WebSocket messages
    print("\n5. Waiting for WebSocket broadcast...")
    await asyncio.sleep(3)
    
    # Cancel listener
    listener_task.cancel()
    try:
        await listener_task
    except asyncio.CancelledError:
        pass
    
    # Step 5: Check if message was received via WebSocket
    print("\n6. Checking WebSocket broadcast result...")
    feishu_messages = [m for m in received_messages if m.get('type') in ['feishu-chat-message', 'feishu_chat_message']]
    
    if feishu_messages:
        print(f"   [OK] Received {len(feishu_messages)} feishu-chat-message broadcasts")
        for msg in feishu_messages:
            data = msg.get('data', {})
            print(f"   - {data.get('sender_type')}: {data.get('content', '')[:40]}...")
    else:
        print("   [FAIL] No feishu-chat-message received via WebSocket")
        print(f"   Received types: {[m.get('type') for m in received_messages]}")
    
    # Step 6: Verify message in database
    print("\n7. Verifying message in database...")
    from database.session import get_db_sync
    from database.models import FeishuChatMessage
    
    db = get_db_sync()
    msg = db.query(FeishuChatMessage).filter(
        FeishuChatMessage.message_id == test_msg_id
    ).first()
    
    if msg:
        print(f"   [OK] Message saved: {msg.content}")
    else:
        print("   [FAIL] Message not found in database")
    
    db.close()
    
    # Step 7: Verify API returns the message
    print("\n8. Verifying API returns the message...")
    resp = requests.get(f"{BASE_URL}/api/feishu-chat/recent?limit=5")
    recent_messages = resp.json()
    
    found = any(m.get('message_id') == test_msg_id for m in recent_messages)
    if found:
        print(f"   [OK] API returns the test message")
    else:
        print(f"   [FAIL] API does not return the test message")
    
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    results = {
        "WebSocket Broadcast": len(feishu_messages) > 0,
        "Database Save": msg is not None,
        "API Response": found
    }
    
    for test, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {test}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n[SUCCESS] All tests passed!")
        print("The backend flow is working correctly.")
        print("\nIf frontend still doesn't show messages, the issue is in:")
        print("  1. Frontend WebSocket connection")
        print("  2. Event listener setup in BotChatTab")
        print("  3. React Query cache invalidation")
    else:
        print("\n[ISSUE] Some tests failed")
    
    print("="*60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    asyncio.run(run_e2e_test())
