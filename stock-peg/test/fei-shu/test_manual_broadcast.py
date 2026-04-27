"""
Simple test: Listen for WebSocket + Manual trigger broadcast
"""
import asyncio
import websockets
import json
import requests
from datetime import datetime

async def test_manual_broadcast():
    """Connect to WebSocket and manually trigger broadcast"""
    uri = "ws://localhost:8000/ws"
    print("=" * 60)
    print("Manual Broadcast Test")
    print("=" * 60)
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"\n[WS] Connected to {uri}")
            print(f"[WS] Active connections: Check via /api/feishu/websocket-status\n")
            
            # Trigger manual broadcast
            print("[HTTP] Triggering manual broadcast via /api/feishu/test-broadcast...")
            response = requests.post("http://localhost:8000/api/feishu/test-broadcast")
            print(f"[HTTP] Response: {response.json()}\n")
            
            # Listen for messages
            print("[WS] Listening for messages (5 seconds)...\n")
            for _ in range(10):
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                    data = json.loads(message)
                    msg_type = data.get("type")
                    
                    if msg_type == "feishu-chat-message":
                        print(f"[SUCCESS] Received broadcast message!")
                        print(f"  Type: {msg_type}")
                        print(f"  Data: {json.dumps(data['data'], indent=2, ensure_ascii=False)}\n")
                        return
                    elif msg_type == "pong":
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Received pong (ignored)")
                    else:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Received: {msg_type}")
                        
                except asyncio.TimeoutError:
                    continue
                    
            print("[FAIL] No broadcast message received after 5 seconds")
            
    except Exception as e:
        print(f"[ERROR] {e}")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_manual_broadcast())
