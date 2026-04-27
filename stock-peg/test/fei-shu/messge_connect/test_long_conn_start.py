# Test long connection service start
import sys
import asyncio
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

async def test():
    print("Starting long connection service...")
    
    from services.feishu_long_connection_service import feishu_long_connection_service
    
    print(f"Before start - Enabled: {feishu_long_connection_service.enabled}")
    print(f"Before start - Running: {feishu_long_connection_service._running}")
    
    try:
        await feishu_long_connection_service.start()
        print(f"After start - Running: {feishu_long_connection_service._running}")
        print(f"After start - Loop: {feishu_long_connection_service._loop}")
        print(f"After start - Thread: {feishu_long_connection_service._thread}")
        
        # Wait a bit for thread to start
        await asyncio.sleep(3)
        
        print(f"After 3s - Running: {feishu_long_connection_service._running}")
        print(f"After 3s - Thread alive: {feishu_long_connection_service._thread and feishu_long_connection_service._thread.is_alive()}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
