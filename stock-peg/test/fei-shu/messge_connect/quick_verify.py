"""
Quick test - Run this after restarting backend
Tests if the fixes are working
"""
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parent.parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

print("\n" + "="*60)
print("Quick Verification - Run AFTER restarting backend")
print("="*60)

# Check 1: Long connection service status
print("\n[Check 1] Long Connection Service Status")
try:
    from services.feishu_long_connection_service import feishu_long_connection_service
    
    enabled = feishu_long_connection_service.enabled
    running = feishu_long_connection_service._running
    loop_set = feishu_long_connection_service._loop is not None
    
    print(f"  Enabled: {enabled}")
    print(f"  Running: {running}")
    print(f"  Loop set: {loop_set}")
    
    if enabled and running and loop_set:
        print("  [OK] Long connection service is properly configured!")
    elif enabled and not running:
        print("  [WARN] Service enabled but not running - restart backend needed")
    elif not enabled:
        print("  [WARN] Service not enabled - check FEISHU_APP_ID and FEISHU_APP_SECRET")
        
except Exception as e:
    print(f"  [ERROR] {e}")

# Check 2: WebSocket manager
print("\n[Check 2] WebSocket Manager")
try:
    from services.websocket_manager import manager
    
    connections = manager.get_connection_count()
    print(f"  Active connections: {connections}")
    
    if connections > 0:
        print("  [OK] WebSocket has active connections")
    else:
        print("  [INFO] No active connections (start frontend to connect)")
        
except Exception as e:
    print(f"  [ERROR] {e}")

# Check 3: Test broadcast method
print("\n[Check 3] Broadcast Method Test")
try:
    import asyncio
    from services.websocket_manager import manager
    from services.feishu_long_connection_service import feishu_long_connection_service
    
    async def test_broadcast():
        # Check if loop is properly set
        try:
            loop = asyncio.get_running_loop()
            print(f"  Current loop: {loop}")
            
            if feishu_long_connection_service._loop == loop:
                print("  [OK] Long connection service loop matches current loop")
            else:
                print(f"  [WARN] Loop mismatch!")
                print(f"    Service loop: {feishu_long_connection_service._loop}")
        except:
            print("  [WARN] Could not check loop (no running loop)")
        
        # Test broadcast
        try:
            await manager.broadcast({"type": "test", "data": {"message": "test"}})
            print("  [OK] Broadcast method works")
        except Exception as e:
            print(f"  [FAIL] Broadcast failed: {e}")
    
    asyncio.run(test_broadcast())
    
except Exception as e:
    print(f"  [ERROR] {e}")

# Summary
print("\n" + "="*60)
print("Next Steps:")
print("="*60)
print("""
1. If long connection service shows Running: False
   -> Restart backend service (run start.bat or restart_backend.bat)

2. After restart, run this script again to verify

3. Test real Feishu message:
   a. Open frontend (http://localhost:5173)
   b. Go to "飞书Bot对话" tab
   c. Send message from Feishu mobile app
   d. Check if message appears in frontend

4. If still not working, check browser console (F12) for errors
""")
print("="*60 + "\n")
