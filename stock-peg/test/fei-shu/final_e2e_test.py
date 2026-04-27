"""
Final end-to-end test with WebSocket listener
"""
import asyncio
import websockets
import json
import requests
from datetime import datetime

received_messages = []

async def websocket_listener():
    """Listen for WebSocket messages"""
    uri = "ws://localhost:8000/ws"
    
    async with websockets.connect(uri) as websocket:
        print("[WS] Connected, listening for messages...\n")
        
        # Send webhook after connection
        await asyncio.sleep(0.5)
        
        webhook_payload = {
            "schema_version": "2.0",
            "header": {
                "event_id": "final_test",
                "event_type": "im.message.receive_v1",
                "create_time": str(int(datetime.now().timestamp() * 1000)),
                "token": "test",
                "app_id": "test",
                "tenant_key": "test"
            },
            "event": {
                "sender": {
                    "sender_id": {"user_id": "final_user", "open_id": "ou_final"},
                    "sender_type": "user",
                    "tenant_key": "test"
                },
                "message": {
                    "message_id": "final_msg",
                    "create_time": str(int(datetime.now().timestamp() * 1000)),
                    "chat_id": "oc_final_test",
                    "message_type": "text",
                    "content": json.dumps({"text": "查询 000001"})
                }
            }
        }
        
        print("[HTTP] Sending webhook...")
        response = requests.post(
            "http://localhost:8000/api/feishu/webhook",
            json=webhook_payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"[HTTP] Response: {response.status_code}\n")
        
        # Listen for messages for 5 seconds
        for i in range(10):
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                data = json.loads(message)
                msg_type = data.get("type")
                
                if msg_type == "feishu-chat-message":
                    received_messages.append(data)
                    print(f"[SUCCESS] Received Feishu broadcast!")
                    print(f"  Sender: {data['data']['sender_type']}")
                    print(f"  Content: {data['data']['content']}")
                    print(f"  Chat ID: {data['data']['chat_id']}\n")
                elif msg_type != "pong":
                    print(f"[{i}] Received: {msg_type}")
                    
            except asyncio.TimeoutError:
                continue


async def main():
    """Main test"""
    print("=" * 70)
    print("FINAL END-TO-END TEST")
    print("=" * 70)
    
    # Check status
    response = requests.get("http://localhost:8000/api/feishu/websocket-status")
    print(f"\nWebSocket Status: {response.json()}\n")
    
    # Run test
    await websocket_listener()
    
    # Report
    print("=" * 70)
    print("TEST RESULT")
    print("=" * 70)
    
    if received_messages:
        print(f"\n[PASS] Received {len(received_messages)} broadcast message(s)!")
        print("\nFIX SUCCESSFUL!")
        print("\nNext steps:")
        print("1. Test from real Feishu app")
        print("2. Monitor frontend console for automatic updates")
    else:
        print("\n[FAIL] No broadcast messages received")
        print("\nPossible issues:")
        print("1. Backend code not reloaded (restart backend)")
        print("2. Exception in process_message_event (check logs)")
        print("3. WebSocket connection issues")
    
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
