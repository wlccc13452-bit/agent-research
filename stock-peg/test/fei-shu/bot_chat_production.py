"""
飞书机器人独立对话 Demo（生产版本）
使用 WebSocket 长连接模式，无需公网域名

运行方式：
    使用项目虚拟环境：
    cd d:\\play-ground\\股票研究\\stock-peg\\test\\fei-shu
    d:\\play-ground\\股票研究\\stock-peg\\backend\\.venv\\Scripts\\python.exe bot_chat_production.py
"""
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 导入飞书官方 SDK
import lark_oapi as lark
from lark_oapi.api.im.v1 import (
    ReplyMessageRequest,
    ReplyMessageRequestBody,
)
from lark_oapi.ws import Client as WSClient
from lark_oapi.event.dispatcher_handler import EventDispatcherHandler

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from services.feishu_bot import save_chat_message
except Exception:
    save_chat_message = None

# ==========================================
# 1. 配置加载
# ==========================================
def load_env_values() -> dict[str, str]:
    """加载 .env 配置文件"""
    candidates = [
        Path(__file__).resolve().parent / ".env",
        Path(__file__).resolve().parents[2] / "backend" / ".env",
    ]

    env_path = None
    for path in candidates:
        if path.exists():
            env_path = path
            break

    if not env_path:
        env_path = candidates[0]

    values: dict[str, str] = {}
    if not env_path.exists():
        print(f"[警告] 未找到 .env 文件: {env_path}")
        return values

    with env_path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")

    return values


ENV_VALUES = load_env_values()
APP_ID = ENV_VALUES.get("FEISHU_APP_ID", "")
APP_SECRET = ENV_VALUES.get("FEISHU_APP_SECRET", "")

# ==========================================
# 2. 交易指令处理器
# ==========================================
def trading_logic_handler(command: str) -> str:
    """
    处理交易指令
    可替换为实际的业务逻辑
    """
    cmd = command.strip()
    
    if not cmd:
        return "终端就绪，请输入交易指令（如：查询 700）"

    # 模拟逻辑处理
    if "查询" in cmd:
        stock_name = cmd.replace('查询','').strip()
        return f"[行情查询] 股票: {stock_name}\n当前价格: 380.50 HKD\n涨跌幅: +1.2%"
    elif "买入" in cmd:
        stock_name = cmd.replace('买入','').strip()
        return f"[交易指令] 正在执行买入操作...\n标的: {stock_name}\n状态: 委托已提交"
    elif "帮助" in cmd or "help" in cmd.lower():
        return """可用命令:

1. 查询股票
   - 查询 [股票名称或代码]
   - 例: 查询 紫金矿业

2. 买入股票
   - 买入 [股票名称或代码]
   - 例: 买入 700

3. 帮助
   - 帮助
   - help"""
    else:
        return f"收到指令: {cmd}\n未知命令，输入'帮助'查看可用指令。"


# ==========================================
# 3. 飞书消息事件回调
# ==========================================
def handle_message_receive(data: Any) -> None:
    """
    处理接收到的消息事件
    """
    try:
        # 获取消息基本信息
        event = data.event
        message = event.message
        sender = event.sender

        # 解析消息内容
        content_dict = json.loads(message.content)
        user_text = content_dict.get("text", "")

        # 获取发送者 ID
        sender_id = sender.sender_id.user_id or sender.sender_id.open_id
        sender_name = sender.sender_id.open_id or sender_id
        chat_id = message.chat_id
        message_type = getattr(message, "message_type", "text")
        create_time_raw = getattr(message, "create_time", 0)
        try:
            create_time_ms = int(create_time_raw) if create_time_raw else 0
        except (TypeError, ValueError):
            create_time_ms = 0
        send_time = datetime.fromtimestamp(create_time_ms / 1000) if create_time_ms else datetime.now()

        print(f"[收到消息] {sender_id}: {user_text}")

        if save_chat_message:
            save_chat_message(
                chat_id=chat_id,
                message_id=message.message_id,
                sender_id=sender_id,
                sender_name=sender_name,
                sender_type="user",
                content=user_text,
                send_time=send_time,
                message_type=message_type,
            )

        # 调用交易逻辑获取回复内容
        reply_content = trading_logic_handler(user_text)

        # 构造回复消息的请求
        reply_req = ReplyMessageRequest.builder() \
            .message_id(message.message_id) \
            .request_body(ReplyMessageRequestBody.builder()
                .content(json.dumps({"text": reply_content}, ensure_ascii=False))
                .msg_type("text")
                .build()) \
            .build()

        # 发送回复
        client = lark.Client.builder() \
            .app_id(APP_ID) \
            .app_secret(APP_SECRET) \
            .log_level(lark.LogLevel.ERROR) \
            .build()

        resp = client.im.v1.message.reply(reply_req)

        if resp.code != 0:
            print(f"[回复失败] {resp.code}: {resp.msg}")
        else:
            print(f"[回复成功] {user_text[:20]}...")
            if save_chat_message:
                bot_message_id = f"bot_{message.message_id}"
                if hasattr(resp, "data") and resp.data and hasattr(resp.data, "message_id"):
                    bot_message_id = resp.data.message_id or bot_message_id
                save_chat_message(
                    chat_id=chat_id,
                    message_id=bot_message_id,
                    sender_id="bot",
                    sender_name="股票助手",
                    sender_type="bot",
                    content=reply_content,
                    send_time=datetime.now(),
                    message_type="text",
                    reply_to_id=message.message_id,
                )

    except Exception as e:
        print(f"[处理异常] {e}")


def handle_p2p_chat_entered(data: Any) -> None:
    """
    处理进入私聊会话事件
    """
    try:
        event = data.event
        chat_id = event.chat_id
        print(f"[进入会话] {chat_id[:20]}...")
    except Exception as e:
        print(f"[异常] {e}")


# ==========================================
# 4. 初始化并启动 WebSocket 长连接
# ==========================================
def main():
    """主函数"""
    if not APP_ID or not APP_SECRET:
        print("[错误] 请先在 .env 中配置 FEISHU_APP_ID 和 FEISHU_APP_SECRET")
        return

    print("------------------------------------------")
    print("[STOCK] 交易机器人正在启动...")
    print(f"[App ID] {APP_ID[:10]}***")
    print("[模式] WebSocket 长连接")
    print("------------------------------------------")

    # 创建事件处理器
    event_handler = EventDispatcherHandler.builder("", "") \
        .register_p2_im_message_receive_v1(handle_message_receive) \
        .register_p2_im_chat_access_event_bot_p2p_chat_entered_v1(handle_p2p_chat_entered) \
        .build()
    
    print("\n[监听] 等待消息... (Ctrl+C 停止)\n")

    # 创建 WebSocket 客户端
    ws_client = WSClient(
        app_id=APP_ID,
        app_secret=APP_SECRET,
        event_handler=event_handler,
        log_level=lark.LogLevel.ERROR  # 减少日志输出
    )

    # 启动 WebSocket 长连接（阻塞运行）
    try:
        ws_client.start()
    except KeyboardInterrupt:
        print("\n\n[停止] 机器人已停止")


if __name__ == "__main__":
    main()
