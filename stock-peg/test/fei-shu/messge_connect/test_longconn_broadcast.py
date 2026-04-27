"""
Test to verify long connection service broadcast works correctly
"""
import sys
import asyncio
import json
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parent.parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from services.websocket_manager import manager
from services.feishu_long_connection_service import feishu_long_connection_service
import websockets

WS_URL = "ws://localhost:8000/ws"


async def test_broadcast_from_thread():
    """Test if broadcast from long connection thread works"""
    received = []
    
    async def ws_client():
        async with websockets.connect(WS_URL) as ws:
            print("[WS] Connected")
            while True:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=1)
                    data = json.loads(msg)
                    if data.get('type') in ['feishu-chat-message', 'feishu_chat_message']:
                        received.append(data)
                        print(f"[WS] Received: {data.get('type')}")
                except asyncio.TimeoutError:
                    continue
    
    # Start WebSocket client
    ws_task = asyncio.create_task(ws_client())
    
    # Wait for connection
    await asyncio.sleep(2)
    
    # Test 1: Direct broadcast (should work)
    print("\n[TEST 1] Direct broadcast from main loop...")
    await manager.broadcast({
        "type": "feishu-chat-message",
        "data": {"content": "Direct broadcast test"}
    })
    
    await asyncio.sleep(1)
    print(f"  Received: {len([r for r in received if 'Direct' in r.get('data', {}).get('content', '')])}")
    
    # Test 2: Broadcast via long connection service's _broadcast method
    print("\n[TEST 2] Broadcast via long connection service _broadcast...")
    feishu_long_connection_service._broadcast({
        "type": "feishu-chat-message",
        "data": {"content": "Long connection broadcast test"}
    })
    
    await asyncio.sleep(1)
    print(f"  Received: {len([r for r in received if 'Long connection' in r.get('data', {}).get('content', '')])}")
    
    # Test 3: Check if long connection service has correct loop
    print("\n[TEST 3] Check long connection service state...")
    print(f"  _loop set: {feishu_long_connection_service._loop is not None}")
    print(f"  _running: {feishu_long_connection_service._running}")
    print(f"  Current loop: {asyncio.get_running_loop()}")
    print(f"  Service loop matches: {feishu_long_connection_service._loop == asyncio.get_running_loop()}")
    
    # Cancel WebSocket task
    ws_task.cancel()
    try:
        await ws_task
    except asyncio.CancelledError:
        pass
    
    # Summary
    print("\n" + "="*60)
    print("Results:")
    print(f"  Direct broadcast: {'PASS' if any('Direct' in r.get('data', {}).get('content', '') for r in received) else 'FAIL'}")
    print(f"  Long conn broadcast: {'PASS' if any('Long connection' in r.get('data', {}).get('content', '') for r in received) else 'FAIL'}")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_broadcast_from_thread())
