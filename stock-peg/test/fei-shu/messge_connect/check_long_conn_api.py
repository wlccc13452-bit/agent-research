import requests

print("Checking long-connection-status...")
try:
    resp = requests.get("http://localhost:8000/api/feishu/long-connection-status", timeout=5)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as e:
    print(f"Error: {e}")
