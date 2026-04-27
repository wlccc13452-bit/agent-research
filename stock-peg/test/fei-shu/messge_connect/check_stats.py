import requests
import json
import time

print("Waiting for API reload...")
time.sleep(2)

print("\nChecking message stats...")
try:
    resp = requests.get("http://localhost:8000/api/feishu/message-stats", timeout=5)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"Error response: {resp.text[:200]}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
