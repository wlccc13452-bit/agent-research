from pathlib import Path
import argparse
import json
import time
import uuid
from urllib import error, request


def load_env_values() -> dict[str, str]:
    env_path = Path(__file__).resolve().parents[2] / "backend" / ".env"
    values: dict[str, str] = {}

    with env_path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")

    return values


def load_feishu_credentials(values: dict[str, str]) -> tuple[str, str]:
    app_id = values.get("FEISHU_APP_ID", "")
    app_secret = values.get("FEISHU_APP_SECRET", "")
    if not app_id or not app_secret:
        env_path = Path(__file__).resolve().parents[2] / "backend" / ".env"
        raise RuntimeError(f"backend/.env 中缺少 FEISHU_APP_ID 或 FEISHU_APP_SECRET: {env_path}")

    return app_id, app_secret


ENV_VALUES = load_env_values()
FEISHU_APP_ID, FEISHU_APP_SECRET = load_feishu_credentials(ENV_VALUES)


def fetch_tenant_access_token(app_id: str, app_secret: str) -> dict:
    payload = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode("utf-8")
    req = request.Request(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with request.urlopen(req, timeout=20) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body)


def send_text_message(
    tenant_access_token: str,
    receive_id: str,
    message: str,
    receive_id_type: str = "chat_id",
) -> dict:
    payload = json.dumps(
        {
            "receive_id": receive_id,
            "msg_type": "text",
            "content": json.dumps({"text": message}, ensure_ascii=False),
        },
        ensure_ascii=False,
    ).encode("utf-8")
    req = request.Request(
        f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type={receive_id_type}",
        data=payload,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {tenant_access_token}",
        },
        method="POST",
    )
    with request.urlopen(req, timeout=20) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body)


def send_mock_user_message_to_backend(
    backend_url: str,
    chat_id: str,
    user_id: str,
    text: str,
) -> dict:
    now_ms = int(time.time() * 1000)
    payload = {
        "schema": "2.0",
        "header": {
            "event_id": str(uuid.uuid4()),
            "event_type": "im.message.receive_v1",
            "create_time": str(now_ms),
        },
        "event": {
            "sender": {"sender_id": {"user_id": user_id}},
            "message": {
                "message_id": str(uuid.uuid4()),
                "chat_id": chat_id,
                "chat_type": "group",
                "message_type": "text",
                "content": json.dumps({"text": text}, ensure_ascii=False),
                "create_time": str(now_ms),
            },
        },
    }
    req = request.Request(
        f"{backend_url.rstrip('/')}/feishu/webhook",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with request.urlopen(req, timeout=20) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receive-id", default=ENV_VALUES.get("FEISHU_TEST_RECEIVE_ID", ""))
    parser.add_argument("--receive-id-type", default=ENV_VALUES.get("FEISHU_TEST_RECEIVE_ID_TYPE", "chat_id"))
    parser.add_argument("--message", default=ENV_VALUES.get("FEISHU_TEST_MESSAGE", "stock-peg 飞书连通性测试"))
    parser.add_argument("--conversation", action="store_true")
    parser.add_argument("--chat-id", default=ENV_VALUES.get("FEISHU_TEST_CHAT_ID", ""))
    parser.add_argument("--backend-url", default=ENV_VALUES.get("FEISHU_TEST_BACKEND_URL", "http://127.0.0.1:8000"))
    parser.add_argument("--sender-user-id", default=ENV_VALUES.get("FEISHU_TEST_SENDER_USER_ID", "cli_test_user"))
    return parser.parse_args()


def main():
    args = parse_args()
    app_id_masked = f"{FEISHU_APP_ID[:6]}***{FEISHU_APP_ID[-4:]}" if len(FEISHU_APP_ID) > 10 else "***"
    print(f"正在验证飞书连接，AppID: {app_id_masked}")
    try:
        result = fetch_tenant_access_token(FEISHU_APP_ID, FEISHU_APP_SECRET)
    except error.HTTPError as e:
        print(f"请求失败，HTTP {e.code}")
        raise
    except error.URLError as e:
        print(f"网络错误: {e}")
        raise

    if result.get("code") == 0 and result.get("tenant_access_token"):
        expire = result.get("expire", "")
        print(f"连接成功，tenant_access_token 获取成功，expire={expire}")
        if args.conversation:
            chat_id = args.chat_id or (args.receive_id if args.receive_id_type == "chat_id" else "")
            if not chat_id:
                raise RuntimeError("对话模式需要 --chat-id，或提供 --receive-id 且 --receive-id-type=chat_id")
            print(f"进入对话测试模式，chat_id={chat_id}，输入 /exit 退出")
            while True:
                text = input("你: ").strip()
                if not text:
                    continue
                if text in {"/exit", "exit", "quit"}:
                    print("已退出对话测试")
                    break
                webhook_result = send_mock_user_message_to_backend(
                    backend_url=args.backend_url,
                    chat_id=chat_id,
                    user_id=args.sender_user_id,
                    text=text,
                )
                print(f"已投递到后端: {webhook_result}")
                print("请在飞书中查看 @HSA 回复")
            return
        if args.receive_id:
            send_result = send_text_message(
                tenant_access_token=result["tenant_access_token"],
                receive_id=args.receive_id,
                message=args.message,
                receive_id_type=args.receive_id_type,
            )
            if send_result.get("code") == 0:
                message_id = (send_result.get("data") or {}).get("message_id", "")
                print(f"测试消息发送成功，message_id={message_id}")
            else:
                raise RuntimeError(f"测试消息发送失败: {send_result}")
        else:
            print("未提供 receive_id，已跳过发消息测试")
        return

    print(f"连接失败: {result}")
    raise RuntimeError("飞书鉴权失败")


if __name__ == "__main__":
    main()
