"""
Simple WebSocket connection test
"""
import asyncio
import websockets
import json
import requests

async def test_ws_connection():
    """Test WebSocket connection step by step"""
    uri = "ws://localhost:8000/ws"
    
    print("=" * 60)
    print("WebSocket Connection Test")
    print("=" * 60)
    
    # Check before connecting
    response = requests.get("http://localhost:8000/api/feishu/websocket-status")
    print(f"\nBefore connecting: {response.json()}")
    
    print(f"\nConnecting to {uri}...")
    
    try:
        websocket = await websockets.connect(uri)
        print(f"[SUCCESS] WebSocket connected!")
        
        # Check after connecting
        await asyncio.sleep(1)
        response = requests.get("http://localhost:8000/api/feishu/websocket-status")
        print(f"After connecting: {response.json()}")
        
        # Trigger broadcast
        print("\nTriggering broadcast...")
        response = requests.post("http://localhost:8000/api/feishu/test-broadcast")
        print(f"Broadcast response: {response.json()}")
        
        # Listen for messages
        print("\nListening for messages (10 seconds)...")
        message_count = 0
        
        for i in range(20):  # 20 * 0.5 = 10 seconds
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                message_count += 1
                data = json.loads(message)
                msg_type = data.get("type")
                
                print(f"  [{i}] Received: {msg_type}")
                
                if msg_type == "feishu-chat-message":
                    print(f"  [SUCCESS] Got broadcast message!")
                    print(f"  Data: {json.dumps(data['data'], indent=4, ensure_ascii=False)}")
                    
            except asyncio.TimeoutError:
                continue
        
        print(f"\nTotal messages received: {message_count}")
        
        await websocket.close()
        print("WebSocket closed")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_ws_connection())
