import requests
import json

# 测试发送消息
url = "http://localhost:8000/api/feishu/test-send-message"
payload = {"message": "测试消息"}

try:
    response = requests.post(url, json=payload)
    print("Status Code:", response.status_code)
    print("Response:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Error: {e}")
    print("Response text:", response.text if 'response' in locals() else "N/A")
