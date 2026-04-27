"""
飞书机器人独立对话 Demo
使用 WebSocket 长连接模式，无需公网域名

运行方式：
    使用项目虚拟环境：
    cd d:\\play-ground\\股票研究\\stock-peg\\test\\fei-shu
    d:\\play-ground\\股票研究\\stock-peg\\backend\\.venv\\Scripts\\python.exe bot_chat.py
"""
import json
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

# ==========================================
# 1. 配置加载
# ==========================================
def load_env_values() -> dict[str, str]:
    """加载 .env 配置文件"""
    candidates = [
        Path(__file__).resolve().parent / ".env",
        Path(__file__).resolve().parents[2] / "backend" / ".env",
    ]

    # 查找存在的文件
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
    print(f"[调试] trading_logic_handler 收到: '{cmd}'")
    
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
    print("\n" + "="*60)
    print("[调试] 收到消息事件")
    print("="*60)
    
    try:
        # 调试：打印整个 data 结构
        print(f"[调试] data 类型: {type(data)}")
        print(f"[调试] data 属性: {dir(data)}")
        
        # 获取消息基本信息
        event = data.event
        print(f"[调试] event 类型: {type(event)}")
        print(f"[调试] event 属性: {dir(event)}")
        
        message = event.message
        print(f"[调试] message 类型: {type(message)}")
        print(f"[调试] message 属性: {[x for x in dir(message) if not x.startswith('_')]}")
        print(f"[调试] message_id: {message.message_id}")
        # message_type 在 EventMessage 中可能叫 message_type 或其他名称
        if hasattr(message, 'message_type'):
            print(f"[调试] message_type: {message.message_type}")
        print(f"[调试] content 原始: {message.content}")
        
        sender = event.sender
        print(f"[调试] sender: {sender}")
        
        # 飞书文本消息 content 是 JSON 字符串 {"text":"xxx"}
        content_dict = json.loads(message.content)
        print(f"[调试] content_dict: {content_dict}")
        
        user_text = content_dict.get("text", "")
        print(f"[调试] user_text: '{user_text}'")

        sender_id = sender.sender_id.user_id or sender.sender_id.open_id
        print(f"[收到] 消息 [来自: {sender_id}]: {user_text}")

        # 调用交易逻辑获取回复内容
        reply_content = trading_logic_handler(user_text)
        print(f"[调试] reply_content: {reply_content}")

        # 构造回复消息的请求
        reply_req = ReplyMessageRequest.builder() \
            .message_id(message.message_id) \
            .request_body(ReplyMessageRequestBody.builder()
                .content(json.dumps({"text": reply_content}, ensure_ascii=False))
                .msg_type("text")
                .build()) \
            .build()
        
        print(f"[调试] 准备发送回复...")

        # 发送回复
        client = lark.Client.builder() \
            .app_id(APP_ID) \
            .app_secret(APP_SECRET) \
            .log_level(lark.LogLevel.INFO) \
            .build()

        resp = client.im.v1.message.reply(reply_req)

        print(f"[调试] 响应 code: {resp.code}")
        print(f"[调试] 响应 msg: {resp.msg}")
        
        if resp.code != 0:
            print(f"[失败] 回复失败: {resp.code}, {resp.msg}")
        else:
            print(f"[成功] 回复成功")
            
        print("="*60 + "\n")

    except Exception as e:
        print(f"[异常] 处理消息异常: {e}")
        import traceback
        traceback.print_exc()
        print("="*60 + "\n")


def handle_p2p_chat_entered(data: Any) -> None:
    """
    处理进入私聊会话事件
    """
    try:
        event = data.event
        chat_id = event.chat_id
        print(f"[进入会话] 用户打开了机器人聊天窗口: {chat_id[:20]}...")
    except Exception as e:
        print(f"[异常] 处理进入会话事件: {e}")


def handle_all_events(data: Any) -> None:
    """
    通用事件处理器 - 捕获所有未注册的事件
    """
    try:
        print("\n" + "="*60)
        print("[调试] 通用事件处理器被触发")
        print("="*60)
        print(f"[调试] data 类型: {type(data)}")
        print(f"[调试] data 内容: {data}")
        
        # 尝试获取事件类型
        if hasattr(data, 'header'):
            print(f"[调试] header: {data.header}")
        if hasattr(data, 'event'):
            print(f"[调试] event: {data.event}")
            
        print("="*60 + "\n")
    except Exception as e:
        print(f"[异常] 通用事件处理器: {e}")


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
    print("[模式] WebSocket 长连接 (无需公网域名)")
    print("------------------------------------------")

    # 创建事件处理器
    builder = EventDispatcherHandler.builder("", "") \
        .register_p2_im_message_receive_v1(handle_message_receive) \
        .register_p2_im_chat_access_event_bot_p2p_chat_entered_v1(handle_p2p_chat_entered)
    
    # 注册通用事件处理器（捕获所有事件）
    # 注意：这需要在 builder 上使用 do 方法
    event_handler = builder.build()
    
    print("[调试] 已注册事件处理器:")
    print("  - im.message.receive_v1 (消息接收)")
    print("  - im.chat.access_event.bot_p2p_chat_entered_v1 (进入会话)")

    # 创建 WebSocket 客户端
    ws_client = WSClient(
        app_id=APP_ID,
        app_secret=APP_SECRET,
        event_handler=event_handler,
        log_level=lark.LogLevel.INFO
    )

    print("\n[监听] 正在监听消息...")
    print("[提示] 在飞书手机端或网页端给机器人发送消息")
    print("[停止] 按 Ctrl+C 停止\n")

    # 启动 WebSocket 长连接（阻塞运行）
    try:
        ws_client.start()
    except KeyboardInterrupt:
        print("\n\n[停止] 机器人已停止")


if __name__ == "__main__":
    main()
