"""
Simple WebSocket client to test broadcast
"""
import asyncio
import websockets
import json
from datetime import datetime

async def test_websocket_client():
    """Connect to WebSocket and listen for messages"""
    uri = "ws://localhost:8000/ws"
    print("=" * 60)
    print(f"Connecting to WebSocket: {uri}")
    print("=" * 60)
    
    try:
        async with websockets.connect(uri) as websocket:
            print("[OK] Connected to WebSocket")
            print("\nListening for messages (Press Ctrl+C to stop)...\n")
            
            message_count = 0
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=60.0)
                    message_count += 1
                    data = json.loads(message)
                    
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    msg_type = data.get("type", "unknown")
                    
                    print(f"[{timestamp}] Message #{message_count}: {msg_type}")
                    
                    if msg_type == "feishu-chat-message":
                        print("  [SUCCESS] Received Feishu chat message!")
                        print(f"  Data: {json.dumps(data.get('data'), indent=2, ensure_ascii=False)}")
                    elif msg_type == "pong":
                        # Skip pong messages for clarity
                        pass
                    else:
                        print(f"  Data: {json.dumps(data, indent=2, ensure_ascii=False)}")
                        
                except asyncio.TimeoutError:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Timeout - no message for 60 seconds")
                    break
                    
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    except Exception as e:
        print(f"[ERROR] {e}")
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_websocket_client())
