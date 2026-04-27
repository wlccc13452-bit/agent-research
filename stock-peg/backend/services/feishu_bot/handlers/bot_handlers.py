"""
Feishu Bot Service - Handle Feishu bot commands for stock queries
"""
import asyncio
import hashlib
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from config.settings import settings
from config.constants import FEISHU_MESSAGE_ID_PREFIX, ErrorCode, RateLimit, LoggingConfig, FEISHU_MAX_CONTENT_LENGTH
from database.session import async_session_maker
from database.operations import save_chat_message as save_chat_message_op
from services.bot_chat_logger import bot_chat_logger
from services.websocket_manager import manager
from utils.logging_utils import safe_log_message_id, truncate_for_logging

logger = logging.getLogger(__name__)


class MessageHandler:
    """Message handler adapter for long connection service
    
    Wraps save_chat_message_async function to match the expected interface.
    The long_connection_service expects a handler with handle_message method.
    """
    
    async def handle_message(
        self,
        chat_id: str,
        message_id: str,
        sender_id: str,
        content: str,
        message_type: str = "text"
    ) -> bool:
        """Handle incoming message by saving to database
        
        Args:
            chat_id: Chat ID
            message_id: Message ID
            sender_id: Sender ID
            content: Message content
            message_type: Message type (text, image, etc.)
            
        Returns:
            True if saved successfully
        """
        return await save_chat_message_async(
            chat_id=chat_id,
            message_id=message_id,
            sender_id=sender_id,
            sender_name=None,
            sender_type="user",
            content=content,
            send_time=datetime.now(),
            message_type=message_type,
        )


async def save_chat_message_async(
    chat_id: str,
    message_id: str,
    sender_id: Optional[str],
    sender_name: Optional[str],
    sender_type: str,
    content: str,
    send_time: datetime,
    message_type: str = "text",
    reply_to_id: Optional[str] = None,
) -> bool:
    """
    Save chat message to database (async version)
    
    Non-blocking database operation for message logging.
    Uses database operations layer for all database access.

    Args:
        chat_id: Feishu chat ID
        message_id: Feishu message ID
        sender_id: Sender user ID
        sender_name: Sender name
        sender_type: 'user' or 'bot'
        content: Message content
        send_time: Message send time
        message_type: Message type
        reply_to_id: Reply to message ID

    Returns:
        True if saved successfully, False if message already exists or error
    """
    try:
        async with async_session_maker() as db:
            return await save_chat_message_op(
                db=db,
                chat_id=chat_id,
                message_id=message_id,
                sender_id=sender_id,
                sender_name=sender_name,
                sender_type=sender_type,
                content=content,
                send_time=send_time,
                message_type=message_type,
                reply_to_id=reply_to_id,
            )
    except Exception as e:
        logger.error(f"Failed to save chat message: {e}")
        return False


def save_chat_message(
    chat_id: str,
    message_id: str,
    sender_id: Optional[str],
    sender_name: Optional[str],
    sender_type: str,
    content: str,
    send_time: datetime,
    message_type: str = "text",
    reply_to_id: Optional[str] = None,
) -> bool:
    """
    Save chat message to database (sync version - legacy support)
    
    DEPRECATED: Use save_chat_message_async for new code.
    This function is kept for backward compatibility.

    Args:
        chat_id: Feishu chat ID
        message_id: Feishu message ID
        sender_id: Sender user ID
        sender_name: Sender name
        sender_type: 'user' or 'bot'
        content: Message content
        send_time: Message send time
        message_type: Message type
        reply_to_id: Reply to message ID

    Returns:
        True if saved successfully, False if message already exists or error
    """
    try:
        # Run async version in event loop
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            # If already in event loop, run in new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    save_chat_message_async(
                        chat_id=chat_id,
                        message_id=message_id,
                        sender_id=sender_id,
                        sender_name=sender_name,
                        sender_type=sender_type,
                        content=content,
                        send_time=send_time,
                        message_type=message_type,
                        reply_to_id=reply_to_id,
                    )
                )
                return future.result(timeout=5)
        except RuntimeError:
            # No running event loop, use asyncio.run
            return asyncio.run(
                save_chat_message_async(
                    chat_id=chat_id,
                    message_id=message_id,
                    sender_id=sender_id,
                    sender_name=sender_name,
                    sender_type=sender_type,
                    content=content,
                    send_time=send_time,
                    message_type=message_type,
                    reply_to_id=reply_to_id,
                )
            )
    except Exception as e:
        logger.error(f"Failed to save chat message: {e}")
        return False



class FeishuBotService:
    """Feishu Bot Service for stock queries
    
    Uses SDK layer client for all Feishu API operations.
    No direct lark_oapi imports - all delegated to SDK.
    """

    def __init__(self) -> None:
        """Initialize Feishu bot service (without client)
        
        Client is injected via set_sdk_client() after initialization.
        """
        self._sdk_client: Optional[Any] = None  # FeishuClient from SDK layer
        self.last_send_error: str | None = None
    
    def set_sdk_client(self, client: Any) -> None:
        """Inject SDK layer client
        
        Args:
            client: FeishuClient instance from feishu_sdk.core.client
        """
        self._sdk_client = client
        logger.info("[APP_LAYER] SDK client injected into FeishuBotService")

    def verify_signature(self, timestamp: str, nonce: str, body: str, signature: str) -> bool:
        """
        Verify Feishu webhook signature

        Args:
            timestamp: Request timestamp
            nonce: Random nonce
            body: Request body
            signature: Signature from Feishu

        Returns:
            True if signature is valid
        """
        if not settings.feishu_encrypt_key:
            logger.warning("FEISHU_ENCRYPT_KEY not set, skipping signature verification")
            return True

        # Generate signature: sha256(timestamp + nonce + encrypt_key + body)
        sign_str = f"{timestamp}{nonce}{settings.feishu_encrypt_key}{body}"
        expected_signature = hashlib.sha256(sign_str.encode()).hexdigest()

        return signature == expected_signature

    def parse_command(self, text: str) -> dict[str, str] | None:
        """
        Parse command from user message

        Args:
            text: User message text

        Returns:
            Parsed command dict with 'action' and 'params', or None if invalid
        """
        text = text.strip()
        
        # Remove # symbols from start and end (飞书手机端快捷输入格式)
        if text.startswith('#') and text.endswith('#'):
            text = text[1:-1].strip()

        # Command patterns
        commands = {
            "查询": self._parse_stock_query,
            "行情": self._parse_stock_query,
            "股票": self._parse_stock_query,
            "持仓": self._parse_holdings,
            "自持": self._parse_holdings,
            "关注": self._parse_watchlist,
            "动态关注": self._parse_watchlist,
            "查看关注": self._parse_watchlist,
            "帮助": self._parse_help,
            "help": self._parse_help,
        }

        for keyword, parser in commands.items():
            if text.startswith(keyword):
                return parser(text)

        return None

    def _parse_stock_query(self, text: str) -> dict[str, str]:
        """Parse stock query command"""
        # Extract stock name/code from text
        # Examples: "查询平安银行", "行情 000001", "股票 贵州茅台"
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return {"action": "error", "params": "请提供股票名称或代码，例如：查询 平安银行"}

        stock_query = parts[1].strip()
        return {"action": "stock_query", "params": stock_query}

    def _parse_holdings(self, text: str) -> dict[str, str]:
        """Parse holdings command"""
        return {"action": "view_holdings", "params": ""}
    
    def _parse_watchlist(self, text: str) -> dict[str, str]:
        """Parse watchlist command"""
        return {"action": "view_watchlist", "params": ""}
    
    def _parse_help(self, text: str) -> dict[str, str]:
        """Parse help command"""
        return {"action": "help", "params": ""}

    async def handle_command(self, command: dict[str, str], user_id: str) -> str:
        """
        Handle parsed command and return response

        Args:
            command: Parsed command dict
            user_id: Feishu user ID

        Returns:
            Response message
        """
        action = command.get("action")
        params = command.get("params", "")

        if action == "stock_query":
            return await self._handle_stock_query(params)
        elif action == "view_holdings":
            return await self._handle_view_holdings()
        elif action == "view_watchlist":
            return await self._handle_view_watchlist()
        elif action == "help":
            return self._get_help_message()
        elif action == "error":
            return params
        else:
            return f"未知命令: {action}"

    async def _handle_stock_query(self, stock_query: str) -> str:
        """
        Handle stock query command

        Args:
            stock_query: Stock name or code

        Returns:
            Stock information message
        """
        try:
            # Import here to avoid circular dependency
            from datasource import get_datasource, DataSourceType

            akshare_source = get_datasource().get_source(DataSourceType.AKSHARE)
            if not akshare_source:
                return f"[ERROR] AKShare 服务不可用"

            # Try to get real-time quote
            quote = await akshare_source.get_realtime_quote(stock_query)

            if not quote:
                return f"[ERROR] 未找到股票: {stock_query}"

            # Determine trend emoji
            change_percent = quote.get('change_percent', 0)
            if isinstance(change_percent, str):
                try:
                    change_percent = float(change_percent.replace('%', ''))
                except (TypeError, ValueError):
                    change_percent = 0

            trend_emoji = "📈" if change_percent > 0 else "📉" if change_percent < 0 else "➡️"
            status_emoji = "🔴" if change_percent > 0 else "🟢" if change_percent < 0 else "⚪"

            # Format response with emoji
            response = f"""[CHART] 股票信息

{status_emoji} **{quote['stock_name']}** ({quote['stock_code']})

💰 最新价: {quote['current_price']}
{trend_emoji} 涨跌幅: {quote['change_percent']}%
📦 成交量: {quote['volume']}
💵 成交额: {quote['amount']}

🕐 更新时间: {quote['update_time']}
"""
            return response

        except Exception as e:
            logger.error(f"Error querying stock {stock_query}: {e}")
            return f"[WARN]️ 查询失败: {str(e)}"

    async def _handle_view_holdings(self) -> str:
        """
        Handle view holdings command

        Returns:
            Holdings list message
        """
        try:
            from services.holdings_manager import holdings_manager
            
            holdings = holdings_manager.read_holdings()
            
            if not holdings or not holdings.get("sectors"):
                return "[CHART] 持仓列表为空\n\n您可以通过以下方式添加持仓:\n• 点击卡片按钮「持仓管理」→「添加股票」\n• 编辑 backend/data/自持股票.md 文件"
            
            # Build holdings summary message
            message = "[CHART] **持仓概览**\n\n"
            total_stocks = 0
            
            for sector in holdings.get("sectors", []):
                stocks = sector.get("stocks", [])
                if stocks:
                    message += f"**{sector['name']}**:\n"
                    for stock in stocks:
                        stock_name = ""
                        stock_code = ""
                        if isinstance(stock, dict):
                            stock_name = str(stock.get("name", "")).strip()
                            stock_code = str(stock.get("code", "")).strip()
                        elif hasattr(stock, "name"):
                            stock_name = str(getattr(stock, "name", "")).strip()
                            stock_code = str(getattr(stock, "code", "") or "").strip()
                        else:
                            stock_name = str(stock).strip()
                        message += f"  • {stock_name}"
                        if stock_code:
                            message += f" ({stock_code})"
                        message += "\n"
                    message += "\n"
                    total_stocks += len(stocks)
            
            message += f"━━━━━━━━━━━━\n共 {total_stocks} 只股票"
            return message

        except Exception as e:
            logger.error(f"Error viewing holdings: {e}")
            return f"[WARN]️ 查询持仓失败: {str(e)}"
    
    async def _handle_view_watchlist(self) -> str:
        """
        Handle view watchlist command

        Returns:
            Watchlist message
        """
        try:
            from services.daily_watchlist_manager import daily_watchlist_manager
            from database.session import async_session_maker
            
            async with async_session_maker() as db:
                try:
                    # 使用异步方法获取所有日期
                    watch_dates = await daily_watchlist_manager.get_all_dates(db)

                    if not watch_dates:
                        return "👀 动态关注列表为空\n\n您可以通过以下方式添加关注:\n• 点击卡片按钮「关注管理」→「添加关注」\n• 发送命令: 添加关注 [股票名称]"

                    message = "👀 **动态关注股票（按日期）**\n\n"
                    total_stocks = 0

                    for watch_date in watch_dates:
                        # 使用异步方法获取每个日期的关注列表
                        stocks = await daily_watchlist_manager.get_watchlist_by_date(db, watch_date)
                        if not stocks:
                            continue

                        message += f"📅 **{watch_date}**\n"
                        for stock in stocks:
                            message += f"• **{stock.stock_name}**"
                            if stock.stock_code:
                                message += f" ({stock.stock_code})"
                            message += "\n"

                            if stock.target_price:
                                message += f"  [TARGET] 目标价: {float(stock.target_price):.2f}\n"
                            if stock.stop_loss_price:
                                message += f"  🛡️ 止损价: {float(stock.stop_loss_price):.2f}\n"
                            if stock.reason:
                                message += f"  [NOTE] 理由: {stock.reason}\n"
                            message += "\n"

                        total_stocks += len(stocks)

                    message += f"━━━━━━━━━━━━\n共 {len(watch_dates)} 天，{total_stocks} 只股票"
                    return message
                    
                except Exception as e:
                    await db.rollback()
                    raise

        except Exception as e:
            logger.error(f"Error viewing watchlist: {e}")
            return f"[WARN]️ 查询关注列表失败: {str(e)}"
    
    def _get_help_message(self) -> str:
        """Get help message"""
        return """[BOT] PegBot - 智能股票助手

💡 **可用命令**:

1️⃣ 查询股票
   - 查询 [股票名称或代码]
   - 例: 查询 平安银行
   - 例: 行情 000001

2️⃣ 查看持仓
   - 持仓
   - 自持股票
   - [CHART] 查看当前持仓列表

3️⃣ 查看关注
   - 关注
   - 动态关注
   - 👀 查看按日期分组的动态关注列表

4️⃣ 帮助
   - 帮助
   - help

[NOTE] **功能说明**:
- [OK] 实时股票行情查询
- [OK] 持仓管理
- [OK] 动态关注列表
- [OK] 支持股票名称和代码查询
- [OK] emoji表情支持

[WARN]️ **提示**:
- [CHART] 股票数据来源于东方财富
- 🇨🇳 仅支持A股查询
- ⏱️ 数据可能有延迟
"""

    async def send_message(self, receive_id: str, content: str, msg_type: str = "text") -> bool:
        """
        Send message to Feishu user or group (delegated to SDK layer)

        Args:
            receive_id: User ID or Chat ID
            content: Message content
            msg_type: Message type (text, post, etc.)

        Returns:
            True if message sent successfully
        """
        if not self._sdk_client:
            logger.error("SDK client not injected, cannot send message")
            self.last_send_error = "SDK客户端未注入"
            return False
        
        self.last_send_error = None
        
        try:
            # Determine receive_id_type based on ID prefix
            # ou_ = open_id, on_ = union_id, oc_ = chat_id
            if receive_id.startswith("ou_"):
                receive_id_type = "open_id"
                logger.info(f"Sending to open_id: {receive_id[:20]}...")
            elif receive_id.startswith("on_"):
                receive_id_type = "union_id"
                logger.info(f"Sending to union_id: {receive_id[:20]}...")
            elif receive_id.startswith("oc_"):
                receive_id_type = "chat_id"
                logger.info(f"Sending to chat_id: {receive_id[:20]}...")
            else:
                receive_id_type = "chat_id"  # Default
                logger.warning(f"Unknown ID format, using chat_id type: {receive_id[:20]}...")
            
            # Delegate to SDK layer
            success = await self._sdk_client.send_message(
                receive_id=receive_id,
                content=content,
                msg_type=msg_type,
                receive_id_type=receive_id_type
            )
            
            if success:
                logger.info(f"[OK] Message sent to {receive_id[:20]}... via SDK")
                
                # Save bot message to database
                message_id = f"bot_{uuid.uuid4().hex[:16]}"
                save_chat_message(
                    chat_id=receive_id,
                    message_id=message_id,
                    sender_id="bot",
                    sender_name="PegBot",
                    sender_type="bot",
                    content=content,
                    send_time=datetime.now(),
                    message_type=msg_type,
                )
                bot_chat_logger.log_message(
                    message_id=message_id,
                    sender_type="bot",
                    sender_id="bot",
                    content=content,
                    chat_id=receive_id,
                )
                
                # Broadcast bot message via WebSocket
                logger.info(f"[WEBSOCKET] Broadcasting bot message to {manager.get_connection_count()} connections")
                await manager.broadcast({
                    "type": "feishu-chat-message",
                    "data": {
                        "chat_id": receive_id,
                        "message_id": message_id,
                        "sender_id": "bot",
                        "sender_name": "PegBot",
                        "content": content,
                        "send_time": datetime.now().isoformat(),
                    }
                })
            else:
                logger.warning(f"[WARN] Failed to send message via SDK")
                self.last_send_error = "消息发送失败"
            
            return success

        except Exception as e:
            logger.error(f"Error sending message via SDK: {e}")
            self.last_send_error = f"飞书发送异常: {e}"
            return False

    async def get_user_info(self, user_id: str) -> dict[str, Any] | None:
        """
        Get Feishu user info

        Args:
            user_id: Feishu user ID

        Returns:
            User info dict or None
        """
        if not self._sdk_client:
            logger.error("SDK client not injected, cannot get user info")
            return None
        
        try:
            # Delegate to SDK layer
            user_info = await self._sdk_client.get_user_info(user_id)
            
            if user_info:
                logger.info(f"[OK] Retrieved user info: {user_id}")
            else:
                logger.warning(f"[WARN] User not found: {user_id}")
            
            return user_info

        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None

    async def patch_message_card(
        self, 
        message_id: str, 
        card_content: dict,
        enable_retry: bool = True,
        max_retries: int = 3
    ) -> bool:
        """
        Use PATCH interface to update Feishu card in-place (with content truncation, then delegate to SDK)

        使用 PATCH 接口原位更新飞书卡片，适用于表单提交后更新卡片内容
        
        **增强功能**:
        1. 内容截断 - 超过30KB时自动截断非核心内容（应用层）
        2. 自动重试 - Rate Limit (99991400/429) 时使用指数退避重试（SDK层）
        3. 日志脱敏 - 所有日志使用 safe_log_message_id

        Args:
            message_id: ID of the message to update (must be bot's own message, format: om_xxxx)
            card_content: New card content (dict)
            enable_retry: Enable retry on rate limit (default: True)
            max_retries: Max retry attempts (default: 3)

        Returns:
            True if patched successfully
        
        Note:
            - content must be JSON string (handled automatically)
            - Only bot's own messages can be updated
            - message_id must be in "om_xxxx" format
        """
        if not self._sdk_client:
            logger.error("SDK client not injected, cannot patch card")
            return False
        
        try:
            # Validate message_id format
            if not message_id or not message_id.startswith(FEISHU_MESSAGE_ID_PREFIX):
                logger.warning(f"[WARN]️ Invalid message_id format, expected '{FEISHU_MESSAGE_ID_PREFIX}xxxx'")
                return False
            
            # Check content size and truncate if necessary (application layer logic)
            content_str = json.dumps(card_content, ensure_ascii=False)
            content_bytes = content_str.encode('utf-8')
            content_size = len(content_bytes)
            
            final_card_content = card_content
            
            if content_size > FEISHU_MAX_CONTENT_LENGTH:
                logger.warning(
                    f"[WARN]️ Card content too large: {content_size} bytes "
                    f"(limit: {FEISHU_MAX_CONTENT_LENGTH} bytes), attempting truncation"
                )
                
                # Truncate card content (application layer)
                truncated_str = self._truncate_card_content(card_content, content_size)
                truncated_size = len(truncated_str.encode('utf-8'))
                
                # Parse truncated JSON back to dict for SDK
                final_card_content = json.loads(truncated_str)
                
                logger.info(
                    f"[OK] Card content truncated: {content_size} → {truncated_size} bytes "
                    f"({safe_log_message_id(message_id)})"
                )
            
            # Delegate to SDK layer (with retry logic built-in)
            success = await self._sdk_client.patch_message_card(
                message_id=message_id,
                card_content=final_card_content,
                enable_retry=enable_retry,
                max_retries=max_retries
            )
            
            if success:
                logger.info(f"[OK] Card patched successfully via SDK: {safe_log_message_id(message_id)}")
            else:
                logger.warning(f"[WARN] Failed to patch card via SDK: {safe_log_message_id(message_id)}")
            
            return success
            
        except Exception as e:
            logger.error(
                f"Error patching card {safe_log_message_id(message_id)}: {e}", 
                exc_info=True
            )
            return False
    
    def _truncate_card_content(self, card_content: dict, original_size: int) -> str:
        """
        Truncate card content to fit within size limit
        
        **截断策略**:
        1. 移除非核心元素 (note, hr)
        2. 截断长文本内容
        3. 保留 header 和核心 elements
        
        Args:
            card_content: Original card content
            original_size: Original content size in bytes
            
        Returns:
            Truncated JSON string
        """
        from config.constants import ContentLimits
        
        # Step 1: Remove non-essential elements
        truncated_card = card_content.copy()
        
        if "elements" in truncated_card:
            essential_elements = []
            for element in truncated_card["elements"]:
                # Keep only core elements: div, action, column_set
                # Remove: note, hr, chart (if too large)
                tag = element.get("tag", "")
                if tag in ["div", "action", "column_set", "input"]:
                    essential_elements.append(element)
                elif tag == "note" and len(essential_elements) < 5:
                    # Keep note if not too many elements
                    essential_elements.append(element)
            
            truncated_card["elements"] = essential_elements
        
        # Check if truncation is enough
        content_str = json.dumps(truncated_card, ensure_ascii=False)
        if len(content_str.encode('utf-8')) <= FEISHU_MAX_CONTENT_LENGTH:
            return content_str
        
        # Step 2: Truncate long text in elements
        if "elements" in truncated_card:
            for element in truncated_card["elements"]:
                # Truncate text in div elements
                if element.get("tag") == "div" and "text" in element:
                    text_obj = element["text"]
                    if "content" in text_obj and len(text_obj["content"]) > 500:
                        text_obj["content"] = text_obj["content"][:500] + ContentLimits.TRUNCATION_NOTE
                
                # Truncate text in column_set elements
                elif element.get("tag") == "column_set":
                    for column in element.get("columns", []):
                        for col_element in column.get("elements", []):
                            if "text" in col_element and "content" in col_element["text"]:
                                if len(col_element["text"]["content"]) > 200:
                                    col_element["text"]["content"] = (
                                        col_element["text"]["content"][:200] + 
                                        ContentLimits.TRUNCATION_NOTE
                                    )
        
        content_str = json.dumps(truncated_card, ensure_ascii=False)
        
        # Step 3: Fallback - minimal error card
        if len(content_str.encode('utf-8')) > FEISHU_MAX_CONTENT_LENGTH:
            logger.error(f"[WARN]️ Card truncation failed, using minimal error card")
            minimal_card = {
                "config": {"wide_screen_mode": True},
                "header": {
                    "template": "red",
                    "title": {"tag": "plain_text", "content": "[ERROR] 内容过长"}
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"卡片内容超过限制({original_size} bytes)，已自动截断。\n请简化内容后重试。"
                        }
                    }
                ]
            }
            content_str = json.dumps(minimal_card, ensure_ascii=False)
        
        return content_str
