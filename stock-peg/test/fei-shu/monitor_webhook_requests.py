"""Monitor ALL incoming requests to detect real Feishu webhooks"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from datetime import datetime

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/feishu/webhook")
async def webhook_monitor(request: Request):
    """Monitor all incoming Feishu webhook requests"""
    print("\n" + "=" * 60)
    print(f"[WEBHOOK RECEIVED] {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)
    
    # Log headers
    headers = dict(request.headers)
    print("\nHeaders:")
    for key, value in headers.items():
        if key.lower().startswith('x-lark') or key.lower() in ['content-type', 'content-length']:
            print(f"  {key}: {value}")
    
    # Log body
    body = await request.body()
    body_str = body.decode('utf-8')
    
    try:
        body_json = json.loads(body_str)
        print("\nBody (JSON):")
        print(json.dumps(body_json, indent=2, ensure_ascii=False))
        
        # Check event type
        event_type = body_json.get("header", {}).get("event_type", "unknown")
        print(f"\nEvent Type: {event_type}")
        
        if event_type == "im.message.receive_v1":
            print("\n>>> THIS IS A MESSAGE EVENT! <<<")
            message = body_json.get("event", {}).get("message", {})
            content = json.loads(message.get("content", "{}"))
            print(f"Message: {content.get('text', '')}")
        
    except Exception as e:
        print(f"\nBody (raw): {body_str[:500]}")
        print(f"Parse error: {e}")
    
    print("=" * 60 + "\n")
    
    # Return challenge if URL verification
    if body_str:
        try:
            data = json.loads(body_str)
            if data.get("type") == "url_verification":
                return {"challenge": data.get("challenge", "")}
        except:
            pass
    
    return {"status": "monitored"}

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Feishu Webhook Request Monitor")
    print("=" * 60)
    print("\nThis will show ALL requests to /api/feishu/webhook")
    print("\nInstructions:")
    print("1. Keep this running")
    print("2. Send a message from Feishu mobile app")
    print("3. Watch for [WEBHOOK RECEIVED] logs below")
    print("\nIf you don't see any logs, Feishu is NOT calling your webhook!")
    print("=" * 60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="error")
