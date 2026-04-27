import requests
import json

# 检查SDK状态
url = "http://localhost:8000/api/feishu/sdk-status"

try:
    response = requests.get(url)
    print("SDK Status:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Error: {e}")
