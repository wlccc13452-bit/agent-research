"""
End-to-end test: WebSocket listener + Webhook sender
"""
import asyncio
import websockets
import json
import requests
import time
from datetime import datetime

# Global flag to track if we received the message
message_received = False

async def websocket_listener():
    """Listen for WebSocket messages"""
    uri = "ws://localhost:8000/ws"
    print(f"[WS] Connecting to {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("[WS] Connected! Listening for messages...\n")
            
            # Start webhook sender after a short delay
            asyncio.create_task(send_webhook_after_delay(2))
            
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    data = json.loads(message)
                    msg_type = data.get("type", "unknown")
                    
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    if msg_type == "feishu-chat-message":
                        global message_received
                        message_received = True
                        print(f"\n[{timestamp}] [SUCCESS] Received Feishu chat message!")
                        print(f"  Sender: {data['data']['sender_type']}")
                        print(f"  Content: {data['data']['content']}")
                        print(f"  Chat ID: {data['data']['chat_id']}\n")
                        return  # Exit after receiving the message
                    elif msg_type == "pong":
                        # Skip pong
                        pass
                    else:
                        print(f"[{timestamp}] [{msg_type}] {data}")
                        
                except asyncio.TimeoutError:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Timeout - no message for 30 seconds")
                    break
                    
    except Exception as e:
        print(f"[WS ERROR] {e}")


async def send_webhook_after_delay(delay_seconds: int):
    """Send webhook after delay"""
    await asyncio.sleep(delay_seconds)
    
    print(f"\n[WEBHOOK] Sending test webhook...")
    
    # Send a simple webhook with a valid command
    webhook_payload = {
        "schema_version": "2.0",
        "header": {
            "event_id": f"test_{int(time.time())}",
            "event_type": "im.message.receive_v1",
            "create_time": str(int(time.time() * 1000)),
            "token": "test",
            "app_id": "test",
            "tenant_key": "test"
        },
        "event": {
            "sender": {
                "sender_id": {"user_id": "test_user", "open_id": "ou_test"},
                "sender_type": "user",
                "tenant_key": "test"
            },
            "message": {
                "message_id": f"test_msg_{int(time.time())}",
                "create_time": str(int(time.time() * 1000)),
                "chat_id": "oc_test_chat",
                "message_type": "text",
                "content": json.dumps({"text": "查询 000001"})  # Valid command
            }
        }
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/api/feishu/webhook",
            json=webhook_payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"[WEBHOOK] Response: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[WEBHOOK ERROR] {e}")


async def main():
    """Main test"""
    print("=" * 60)
    print("End-to-End WebSocket Broadcast Test")
    print("=" * 60)
    
    # Check WebSocket status
    response = requests.get("http://localhost:8000/api/feishu/websocket-status")
    status = response.json()
    print(f"\nWebSocket Status: {status['active_connections']} active connections\n")
    
    # Start WebSocket listener
    await websocket_listener()
    
    # Report result
    print("\n" + "=" * 60)
    if message_received:
        print("[PASS] WebSocket broadcast is working!")
    else:
        print("[FAIL] No WebSocket message received!")
        print("Possible issues:")
        print("  1. Backend did not call manager.broadcast()")
        print("  2. Frontend WebSocket not connected properly")
        print("  3. Broadcast was called but message was filtered")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
