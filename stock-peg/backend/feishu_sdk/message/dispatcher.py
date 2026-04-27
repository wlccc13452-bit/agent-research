"""
Message Dispatcher - 消息分发器模块

负责消息和事件的路由分发：
- 文本命令路由
- 菜单事件路由
- 卡片回调路由
"""

import json
import logging
from typing import Any, Optional, Callable, Awaitable

from feishu_sdk.config.protocols import CardServiceProtocol

logger = logging.getLogger(__name__)


class MessageDispatcher:
    """
    消息分发器
    
    负责将不同类型的消息和事件路由到对应的处理方法。
    """
    
    def __init__(self):
        """初始化消息分发器"""
        self._card_service: Optional[CardServiceProtocol] = None
        self._command_mapping: dict[str, tuple[str, bool, str]] = {}
        self._menu_commands: dict[str, str] = {}
    
    def set_card_service(self, card_service: CardServiceProtocol) -> None:
        """
        设置卡片服务
        
        Args:
            card_service: FeishuCardService 实例
        """
        self._card_service = card_service
    
    def set_command_mapping(self, mapping: dict[str, tuple[str, bool, str]]) -> None:
        """
       设置命令映射表
        
        Args:
            mapping: 命令映射字典
                {
                    "关键词": (方法名, 是否需要参数, 描述),
                    "查询": ("send_stock_query_card", True, "查询股票"),
                }
        """
        self._command_mapping = mapping
    
    def set_menu_commands(self, commands: dict[str, str]) -> None:
        """
        设置菜单命令映射表
        
        Args:
            commands: 菜单命令映射字典
                {
                    "MENU_EVENT_KEY": "方法名",
                    "STOCK_RESEARCH_START": "send_main_menu_card",
                }
        """
        self._menu_commands = commands
    
    async def dispatch_text_command(
        self,
        chat_id: str,
        user_text: str,
        sender_id: str
    ) -> bool:
        """
        分发文本命令
        
        Args:
            chat_id: 聊天ID
            user_text: 用户输入的文本
            sender_id: 发送者ID
        
        Returns:
            True 如果分发成功
        """
        if not self._card_service:
            logger.error("Card service not available")
            return False
        
        cmd = user_text.strip()
        
        # 空命令发送主菜单
        if not cmd:
            return await self._execute_card_method(chat_id, "send_main_menu_card", "主菜单")
        
        # 1. 优先匹配菜单事件 key（精确匹配）
        if cmd in self._menu_commands:
            method_name = self._menu_commands[cmd]
            logger.info(f"[MENU] 菜单事件匹配: '{cmd}' -> {method_name}")
            return await self._execute_card_method(chat_id, method_name, cmd)
        
        # 2. 匹配文本命令（模糊匹配）
        matched_method = None
        matched_param = None
        matched_desc = ""
        
        for keyword, (method_name, requires_param, desc) in self._command_mapping.items():
            if keyword in cmd:
                # 检查是否需要提取参数
                if requires_param:
                    param = cmd.replace(keyword, "").strip()
                    if param:
                        matched_method = method_name
                        matched_param = param
                        matched_desc = desc
                        break
                    else:
                        # 需要参数但没有提供
                        matched_method = method_name
                        matched_param = None
                        matched_desc = desc
                        break
                else:
                    matched_method = method_name
                    matched_param = None
                    matched_desc = desc
                    break
        
        if matched_method:
            logger.info(f"[NOTE] 文本命令匹配: '{cmd}' -> {matched_method}")
            
            # 特殊处理：带参数的查询命令
            if matched_param and matched_method == "send_stock_query_card":
                return await self._handle_direct_stock_query(chat_id, matched_param)
            else:
                return await self._execute_card_method(chat_id, matched_method, matched_desc)
        else:
            # 未匹配的命令，发送导航卡片
            logger.info(f"❓ 未匹配命令: '{cmd}'，发送导航卡片")
            return await self._execute_card_method(chat_id, "send_main_menu_card", "导航")
    
    async def dispatch_menu_event(
        self,
        chat_id: str,
        event_key: str,
        **kwargs: Any
    ) -> bool:
        """
        分发菜单事件
        
        Args:
            chat_id: 聊天ID
            event_key: 菜单事件 key
            **kwargs: 额外参数
        
        Returns:
            True 如果分发成功
        """
        if not self._card_service:
            logger.error("Card service not available")
            return False
        
        # 使用菜单命令映射表
        method_name = self._menu_commands.get(event_key)
        
        if method_name:
            logger.info(f"[MENU] 菜单事件 '{event_key}' -> {method_name}")
            return await self._execute_card_method(chat_id, method_name, event_key)
        else:
            # 未知事件，fallback 到主菜单
            logger.warning(f"❓ 未知菜单事件: '{event_key}'，发送主菜单")
            return await self._execute_card_method(chat_id, "send_main_menu_card", "主菜单")
    
    async def dispatch_card_callback(
        self,
        chat_id: str,
        user_id: str,
        action: str,
        stock_code: str
    ) -> bool:
        """
        分发卡片回调
        
        Args:
            chat_id: 聊天ID
            user_id: 用户ID
            action: 动作类型
            stock_code: 股票代码
        
        Returns:
            True 如果分发成功
        """
        if not self._card_service:
            logger.error("Card service not available")
            return False
        
        logger.info(f"📨 处理卡片回调: action={action}, stock_code={stock_code}, user={user_id}")
        
        # 验证股票代码
        if not stock_code or not stock_code.strip():
            logger.error("股票代码不能为空")
            return False
        
        stock_code = stock_code.strip()
        
        # 根据动作类型分发
        if hasattr(self._card_service, 'handle_card_callback'):
            return await self._card_service.handle_card_callback(
                chat_id=chat_id,
                user_id=user_id,
                action=action,
                stock_code=stock_code
            )
        else:
            logger.error("Card service does not have handle_card_callback method")
            return False
    
    async def _execute_card_method(
        self,
        chat_id: str,
        method_name: str,
        desc: str = ""
    ) -> bool:
        """
        执行卡片发送方法
        
        Args:
            chat_id: 聊天ID
            method_name: 卡片服务方法名
            desc: 描述（用于日志）
        
        Returns:
            True 如果成功
        """
        method = getattr(self._card_service, method_name, None)
        if method and callable(method):
            try:
                success = await method(chat_id)
                if success:
                    logger.info(f"[OK] 卡片发送成功: {desc or method_name}")
                else:
                    logger.warning(f"[WARN]️ 卡片发送失败: {desc or method_name}")
                return success
            except Exception as e:
                logger.error(f"[ERROR] 卡片发送异常: {e}", exc_info=True)
                return False
        else:
            logger.error(f"[ERROR] 方法不存在: {method_name}")
            # Fallback: 发送主菜单
            if hasattr(self._card_service, 'send_main_menu_card'):
                await self._card_service.send_main_menu_card(chat_id)
            return False
    
    async def _handle_direct_stock_query(self, chat_id: str, stock_code: str) -> bool:
        """
        处理直接股票查询
        
        Args:
            chat_id: 聊天ID
            stock_code: 股票代码或名称
        
        Returns:
            True 如果成功
        """
        try:
            if not self._card_service:
                return False
            
            # 检查是否有 handle_card_callback 方法
            if hasattr(self._card_service, 'handle_card_callback'):
                return await self._card_service.handle_card_callback(
                    chat_id=chat_id,
                    user_id="",
                    action="query_stock",
                    stock_code=stock_code
                )
            else:
                logger.error("Card service does not have handle_card_callback method")
                return False
            
        except Exception as e:
            logger.error(f"[ERROR] Stock query failed: {e}", exc_info=True)
            return False


def parse_message_event(data: Any) -> dict[str, Any]:
    """
    解析飞书消息事件
    
    Args:
        data: 飞书事件数据
    
    Returns:
        解析后的消息信息字典
    """
    try:
        event = data.event
        message = event.message
        sender = event.sender
        content_dict = json.loads(message.content)
        
        return {
            "chat_id": message.chat_id,
            "message_id": message.message_id,
            "user_text": content_dict.get("text", ""),
            "sender_id": sender.sender_id.user_id or sender.sender_id.open_id,
            "sender_name": sender.sender_id.open_id or sender.sender_id.user_id,
            "message_type": getattr(message, "message_type", "text"),
            "create_time": getattr(message, "create_time", 0),
        }
    except Exception as e:
        logger.error(f"解析消息事件失败: {e}", exc_info=True)
        return {}


def parse_menu_event(data: Any) -> dict[str, Any]:
    """
    解析飞书菜单事件
    
    Args:
        data: 飞书事件数据
    
    Returns:
        解析后的菜单事件信息字典
    """
    try:
        event = getattr(data, 'event', None)
        event_dict = getattr(data, '__dict__', {}) if hasattr(data, '__dict__') else {}
        
        def _pick_value(source: Any, *keys: str) -> Any:
            if not source:
                return None
            for key in keys:
                value = getattr(source, key, None)
                if value:
                    return value
                if isinstance(source, dict):
                    value = source.get(key)
                    if value:
                        return value
            return None
        
        chat_id = None
        event_key = None
        user_id = None
        
        if event:
            operator = getattr(event, 'operator', None)
            context = getattr(event, 'context', None)
            chat = getattr(event, 'chat', None)
            event_header = getattr(data, 'header', None)
            
            if operator:
                user_id = _pick_value(operator, 'user_id', 'open_id', 'union_id')
            
            chat_id = (
                _pick_value(context, 'open_chat_id', 'chat_id')
                or _pick_value(event, 'chat_id', 'open_chat_id')
                or _pick_value(chat, 'chat_id', 'open_chat_id')
                or _pick_value(event_header, 'open_chat_id', 'chat_id')
                or _pick_value(data, 'open_chat_id', 'chat_id')
            )
            
            event_key = (
                _pick_value(event, 'event_key', 'menu_key')
                or _pick_value(event_header, 'event_key')
                or _pick_value(data, 'event_key', 'menu_key')
            )
        
        if not chat_id and event_dict:
            operator_dict = event_dict.get('operator') or {}
            context_dict = event_dict.get('context') or {}
            chat_dict = event_dict.get('chat') or {}
            
            if not user_id:
                user_id = _pick_value(operator_dict, 'user_id', 'open_id', 'union_id')
            chat_id = (
                chat_id
                or _pick_value(context_dict, 'open_chat_id', 'chat_id')
                or _pick_value(chat_dict, 'chat_id', 'open_chat_id')
                or _pick_value(operator_dict, 'chat_id')
            )
            event_key = event_key or _pick_value(event_dict, 'event_key', 'menu_key')
        
        return {
            "chat_id": chat_id,
            "event_key": event_key,
            "user_id": user_id,
        }
    except Exception as e:
        logger.error(f"解析菜单事件失败: {e}", exc_info=True)
        return {}
