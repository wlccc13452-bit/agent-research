"""
Feishu Card Service - SDK Layer

Generic card service with NO business logic dependencies.
All business dependencies are injected via setters.
"""
import json
import logging
from typing import Any, Optional, Dict

from lark_oapi.api.im.v1 import (  # type: ignore[import-untyped]
    CreateMessageRequest,
    CreateMessageRequestBody,
)

from config.settings import settings
from config.constants import CardStatus
from feishu_sdk.state.card_state_manager import CardStateManager
from feishu_sdk.state.card_utils import (
    create_simple_status_card,
    prepare_card_for_send,
)
from feishu_sdk.config.protocols import (
    CardBuilderProtocol,
    EventHandlerProtocol,
)

logger = logging.getLogger(__name__)


class FeishuCardService:
    """Feishu Card Service - SDK Layer

    Generic card service with dependency injection.
    NO business logic - all dependencies are injected.
    """

    def __init__(self) -> None:
        """Initialize card service"""
        self._long_connection_service: Any = None
        self._state_manager = CardStateManager()
        self._api_client: Any = None  # API client for sending messages

        # Dependencies (to be injected)
        self._card_builders: Dict[str, CardBuilderProtocol] = {}
        self._event_handler: Optional[EventHandlerProtocol] = None
        self._bot_service: Any = None

    def _get_api_client(self) -> Any:
        """Get or create API client for sending messages"""
        if self._api_client is None:
            from lark_oapi import Client, LogLevel  # type: ignore[import-untyped]
            self._api_client = Client.builder() \
                .app_id(settings.feishu_app_id or "") \
                .app_secret(settings.feishu_app_secret or "") \
                .log_level(LogLevel.INFO) \
                .build()
        return self._api_client
    
    def set_long_connection_service(self, service: Any) -> None:
        """Inject long connection service
        
        Args:
            service: FeishuLongConnectionService instance
        """
        self._long_connection_service = service
    
    def set_card_builders(self, builders: Dict[str, CardBuilderProtocol]) -> None:
        """Inject card builders
        
        Args:
            builders: Dictionary mapping builder names to instances
                     e.g., {'stock': StockCardBuilder(), ...}
        """
        self._card_builders = builders
    
    def set_event_handler(self, handler: EventHandlerProtocol) -> None:
        """Inject event handler
        
        Args:
            handler: Event handler instance
        """
        self._event_handler = handler
    
    def set_bot_service(self, service: Any) -> None:
        """Inject bot service (for backward compatibility)
        
        Args:
            service: Bot service instance
        """
        self._bot_service = service
    
    def start_cleanup_task(self) -> None:
        """Start cleanup task in event loop"""
        self._state_manager.start_cleanup_task()
    
    # ==================== Core Methods (Protocol Implementation) ====================
    
    def send_card(
        self,
        receive_id: str,
        card_content: dict[str, Any],
        receive_id_type: str = "chat_id",
        message_id: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """Send a card message
        
        Args:
            receive_id: Target chat/user ID
            card_content: Card JSON structure
            receive_id_type: ID type (chat_id/open_id/user_id)
            message_id: Optional message ID for updates (ignored for new messages)
            
        Returns:
            Tuple of (success, message_id) - message_id is the new message ID on success
        """
        try:
            # Prepare card for sending
            card = prepare_card_for_send(card_content)
            card_json = json.dumps(card, ensure_ascii=False)
            logger.info(f"[SDK] Prepared card size: {len(card_json)} bytes")
            logger.debug(f"[SDK] Card keys: {list(card.keys())}")
            
            # Log input elements for debugging
            if "body" in card and "elements" in card["body"]:
                for idx, elem in enumerate(card["body"]["elements"]):
                    if isinstance(elem, dict) and elem.get("tag") == "input":
                        logger.info(f"[SDK] Input[{idx}]: name={elem.get('name')}, input_type={elem.get('input_type', 'text')}")
            
            if len(card_json) > 100000:  # 100KB limit
                logger.error(f"[SDK] Card too large: {len(card_json)} bytes (limit: 100KB)")
                return (False, None)

            # Get API client (NOT ws_client - WebSocket client has no 'im' attribute)
            client = self._get_api_client()
            
            # Build message request
            req = CreateMessageRequest.builder() \
                .receive_id_type(receive_id_type) \
                .request_body(CreateMessageRequestBody.builder()
                    .receive_id(receive_id)
                    .msg_type("interactive")
                    .content(card_json)
                    .build()) \
                .build()
            
            logger.info(f"[SDK] Sending to {receive_id_type}: {receive_id[:20]}...")
            
            # Send message
            resp = client.im.v1.message.create(req)
            
            if not resp.success():
                logger.error(f"[SDK] Failed to send card: code={resp.code}, msg={resp.msg}")
                logger.error(f"[SDK] Response details: {resp}")
                if resp.data:
                    logger.error(f"[SDK] Response data: {resp.data}")
                return (False, None)
            
            new_message_id = resp.data.message_id
            logger.info(f"[OK] Card sent successfully: {new_message_id}")
            
            # Track last card for this chat
            if receive_id_type == "chat_id":
                self._state_manager.set_last_card_message(receive_id, new_message_id)
            
            return (True, new_message_id)
            
        except Exception as e:
            logger.error(f"Failed to send card: {e}", exc_info=True)
            return (False, None)
    
    def update_card_status(
        self,
        message_id: str,
        status: str,
        card_content: Optional[dict[str, Any]] = None,
        update_strategy: str = "replace"
    ) -> bool:
        """Update card status and optionally content
        
        Args:
            message_id: Message ID to update
            status: New status (processing/success/error)
            card_content: Optional new card content
            update_strategy: Update strategy (replace/merge) - currently only replace supported
            
        Returns:
            True if update succeeded
        """
        try:
            # Get current card state
            current_state = self._state_manager.get_card_state(message_id)
            
            # Check if card is already completed (prevent double-click)
            if current_state:
                current_status, _ = current_state
                if current_status in [CardStatus.SUCCESS, CardStatus.ERROR]:
                    logger.warning(f"Card {message_id} already completed with status: {current_status}")
                    return False
            
            # If no new content provided, create a simple status card
            if card_content is None:
                if status == CardStatus.PROCESSING:
                    card_content = create_simple_status_card(
                        title="⏳ 处理中",
                        content="正在处理您的请求，请稍候...",
                        status="blue"
                    )
                elif status == CardStatus.SUCCESS:
                    card_content = create_simple_status_card(
                        title="[OK] 操作成功",
                        content="您的请求已处理完成。",
                        status="green"
                    )
                elif status == CardStatus.ERROR:
                    card_content = create_simple_status_card(
                        title="[ERROR] 操作失败",
                        content="处理请求时发生错误，请稍后重试。",
                        status="red"
                    )
                else:
                    card_content = create_simple_status_card(
                        title="[MENU] 状态更新",
                        content=f"当前状态: {status}",
                        status="grey"
                    )
            
            # Prepare card for update
            card = prepare_card_for_send(card_content)

            # Get API client (NOT ws_client)
            client = self._get_api_client()
            
            # Use PatchMessageRequest to update the card
            from lark_oapi.api.im.v1 import PatchMessageRequest, PatchMessageRequestBody
            
            req = PatchMessageRequest.builder() \
                .message_id(message_id) \
                .request_body(PatchMessageRequestBody.builder()
                    .content(json.dumps(card, ensure_ascii=False))
                    .build()) \
                .build()
            
            resp = client.im.v1.message.patch(req)
            
            if not resp.success():
                logger.error(f"Failed to update card: {resp.code} - {resp.msg}")
                return False
            
            # Update state
            self._state_manager.set_card_state(message_id, status)
            logger.info(f"[OK] Card updated: {message_id} -> {status}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update card status: {e}", exc_info=True)
            return False
    
    def get_builder(self, builder_name: str) -> Optional[CardBuilderProtocol]:
        """Get a card builder by name
        
        Args:
            builder_name: Name of the builder (e.g., 'stock', 'menu')
            
        Returns:
            Card builder instance or None if not found
        """
        builder = self._card_builders.get(builder_name)
        if not builder:
            logger.warning(f"Card builder not found: {builder_name}")
            return None
        return builder
    
    # ==================== Convenience Methods ====================
    
    def send_main_menu_card(self, chat_id: str) -> tuple[bool, Optional[str]]:
        """Send main menu card (convenience method for backward compatibility)
        
        Args:
            chat_id: Target chat ID
            
        Returns:
            Tuple of (success, message_id)
        """
        if not self._card_builders:
            logger.error("No card builders registered")
            return (False, None)
        
        # Use first available builder or look for menu builder
        builder = self.get_builder('menu') or self.get_builder('main')
        if not builder:
            # Use first available builder
            builder = list(self._card_builders.values())[0] if self._card_builders else None
        
        if not builder:
            logger.error("No card builder available")
            return (False, None)
        
        if hasattr(builder, "build"):
            card = builder.build(card_type="main_menu")
        else:
            card = builder.build_card({})
        return self.send_card(chat_id, card)
    
    def send_stock_query_card(self, chat_id: str, stock_code: str) -> tuple[bool, Optional[str]]:
        """Send stock query card (convenience method for backward compatibility)
        
        Args:
            chat_id: Target chat ID
            stock_code: Stock code to query
            
        Returns:
            Tuple of (success, message_id)
        """
        builder = self.get_builder('stock')
        if not builder:
            logger.error("Stock card builder not registered")
            # Send error card
            error_card = create_simple_status_card(
                title="[ERROR] 功能未配置",
                content="股票查询功能暂未配置，请联系管理员。",
                status="red"
            )
            return self.send_card(chat_id, error_card)
        
        if hasattr(builder, "build"):
            card = builder.build(card_type="query", stock_code=stock_code)
        else:
            card = builder.build_card({'stock_code': stock_code})
        return self.send_card(chat_id, card)


# Service instance (created without business dependencies)
card_service = FeishuCardService()


__all__ = [
    'FeishuCardService',
    'card_service',
]
