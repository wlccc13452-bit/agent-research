import requests
import json

print("Checking message stats...")
try:
    resp = requests.get("http://localhost:8000/api/feishu/message-stats", timeout=5)
    print(f"Status: {resp.status_code}")
    data = resp.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    print("\n" + "="*50)
    if data.get("real_messages", 0) > 0:
        print("[OK] 收到过真实飞书消息！")
        print(f"    最新消息: {data.get('latest_real', {}).get('content', '')[:40]}")
    else:
        print("[WARN] 没有收到真实飞书消息")
        print("    只有测试消息会被记录")
    
    if data.get("long_connection_running"):
        print("[OK] 长连接服务运行中")
    else:
        print("[WARN] 长连接服务未运行")
        print("    真实消息需要通过webhook接收")
        print("    请在飞书开发者后台配置事件回调URL")
    
    if data.get("websocket_connections", 0) > 0:
        print(f"[OK] WebSocket有{data.get('websocket_connections')}个连接")
    else:
        print("[WARN] 没有WebSocket连接，前端可能未运行")
    
except Exception as e:
    print(f"Error: {e}")
