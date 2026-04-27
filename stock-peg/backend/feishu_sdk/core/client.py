"""
Feishu Client Core Module

Core client for Feishu API operations with dependency injection support.
No business logic - only provides API methods for messaging, signing, and user queries.
"""
import asyncio
import hashlib
import json
import logging
from typing import Any, Optional, Dict

from lark_oapi.api.im.v1 import (
    CreateMessageRequest,
    CreateMessageRequestBody,
    PatchMessageRequest,
    PatchMessageRequestBody,
)

from feishu_sdk.config.config import FeishuConfig
from feishu_sdk.config.interfaces import FeishuEventHandler

logger = logging.getLogger(__name__)


class FeishuClientError(Exception):
    """Base exception for Feishu client errors"""
    pass


class ConfigurationError(FeishuClientError):
    """Raised when configuration is invalid"""
    pass


class APIError(FeishuClientError):
    """Raised when API call fails"""
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"API Error {code}: {message}")


class FeishuClient:
    """Feishu Client Core
    
    Core client for Feishu API operations.
    Uses dependency injection for configuration and event handling.
    
    Features:
    - Message API (send_text, send_card, update_card)
    - Signature verification
    - User info query
    - Async-first design
    - Clear error handling
    - Detailed logging
    
    Example:
        config = FeishuConfig(app_id="xxx", app_secret="xxx")
        handler = MyEventHandler()
        client = FeishuClient(config, handler)
        await client.send_text(chat_id="oc_xxx", content="Hello!")
    """
    
    def __init__(
        self,
        config: FeishuConfig,
        event_handler: Optional[FeishuEventHandler] = None
    ) -> None:
        """Initialize Feishu client
        
        Args:
            config: Feishu configuration
            event_handler: Event handler for callbacks (optional)
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        self.config = config
        self.event_handler = event_handler
        self._client = None
        self.last_error: Optional[str] = None
        
        # Validate configuration
        if not config.is_configured:
            logger.warning("Feishu client not fully configured - app_id or app_secret missing")
        
        # Initialize lark client
        self._init_client()
    
    def _init_client(self) -> None:
        """Initialize lark client"""
        try:
            from lark_oapi import Client, LogLevel
            
            log_level = LogLevel.INFO
            if self.config.log_level == "DEBUG":
                log_level = LogLevel.DEBUG
            elif self.config.log_level == "ERROR":
                log_level = LogLevel.ERROR
            
            self._client = Client.builder() \
                .app_id(self.config.app_id or "") \
                .app_secret(self.config.app_secret or "") \
                .log_level(log_level) \
                .build()
            
            logger.info("Feishu client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Feishu client: {e}")
            raise ConfigurationError(f"Client initialization failed: {e}")
    
    # ==================== Message API ====================
    
    async def send_text(
        self,
        chat_id: str,
        content: str,
        **kwargs
    ) -> bool:
        """Send text message
        
        Args:
            chat_id: Chat ID
            content: Text content
            **kwargs: Additional parameters
            
        Returns:
            True if sent successfully
        """
        return await self.send_message(
            receive_id=chat_id,
            content=content,
            msg_type="text",
            **kwargs
        )
    
    async def send_card(
        self,
        chat_id: str,
        card: Dict[str, Any],
        **kwargs
    ) -> bool:
        """Send card message
        
        Args:
            chat_id: Chat ID
            card: Card content dict
            **kwargs: Additional parameters
            
        Returns:
            True if sent successfully
        """
        return await self.send_message(
            receive_id=chat_id,
            content=json.dumps(card, ensure_ascii=False),
            msg_type="interactive",
            **kwargs
        )
    
    async def update_card(
        self,
        message_id: str,
        card: Dict[str, Any],
        **kwargs
    ) -> bool:
        """Update card message in-place
        
        Args:
            message_id: Message ID (must start with "om_")
            card: New card content
            **kwargs: Additional parameters
            
        Returns:
            True if updated successfully
        """
        return await self.patch_message_card(
            message_id=message_id,
            card_content=card,
            **kwargs
        )
    
    async def send_message(
        self,
        receive_id: str,
        content: str,
        msg_type: str = "text",
        receive_id_type: str = "chat_id"
    ) -> bool:
        """Send message to Feishu
        
        Args:
            receive_id: Receiver ID (user_id or chat_id)
            content: Message content
            msg_type: Message type (text, post, interactive)
            receive_id_type: ID type (chat_id, user_id, open_id)
            
        Returns:
            True if sent successfully
        """
        self.last_error = None
        
        try:
            # Validate inputs
            if not receive_id:
                self.last_error = "Receive ID is empty"
                logger.error(self.last_error)
                return False
            
            if not self.config.is_configured:
                self.last_error = "Feishu client not configured"
                logger.error(self.last_error)
                return False
            
            # Build message request
            req = CreateMessageRequest.builder() \
                .receive_id_type(receive_id_type) \
                .request_body(CreateMessageRequestBody.builder()
                    .receive_id(receive_id)
                    .msg_type(msg_type)
                    .content(self._format_content(content, msg_type))
                    .build()) \
                .build()
            
            # Send message (synchronous SDK call wrapped in async)
            resp = await asyncio.to_thread(self._client.im.v1.message.create, req)
            
            if resp.code == 0:
                logger.info(f"Message sent to {receive_id[:16]}... (msg_type={msg_type})")
                
                # Notify event handler
                if self.event_handler:
                    message_id = getattr(resp.data, 'message_id', None) if hasattr(resp, 'data') else None
                    await self.event_handler.on_message_sent(
                        message_id=message_id,
                        chat_id=receive_id,
                        content=content,
                        message_type=msg_type
                    )
                
                return True
            else:
                error_msg = f"Failed to send message: code={resp.code}, msg={resp.msg}"
                logger.error(error_msg)
                self.last_error = error_msg
                return False
                
        except Exception as e:
            error_msg = f"Error sending message: {e}"
            logger.error(error_msg, exc_info=True)
            self.last_error = error_msg
            
            # Notify event handler of error
            if self.event_handler:
                await self.event_handler.on_error(
                    error=e,
                    context={"receive_id": receive_id, "msg_type": msg_type}
                )
            
            return False
    
    async def patch_message_card(
        self,
        message_id: str,
        card_content: Dict[str, Any],
        enable_retry: bool = True,
        max_retries: int = 3
    ) -> bool:
        """Update card in-place using PATCH API
        
        Args:
            message_id: Message ID (must start with "om_")
            card_content: New card content
            enable_retry: Enable retry on rate limit
            max_retries: Max retry attempts
            
        Returns:
            True if patched successfully
        """
        self.last_error = None
        
        try:
            # Validate message_id format
            if not message_id or not message_id.startswith("om_"):
                self.last_error = f"Invalid message_id format: {message_id}"
                logger.warning(self.last_error)
                return False
            
            # Serialize card content
            content_str = json.dumps(card_content, ensure_ascii=False)
            
            # Check content size
            content_size = len(content_str.encode('utf-8'))
            if content_size > self.config.max_card_size:
                logger.warning(
                    f"Card content too large: {content_size} bytes "
                    f"(limit: {self.config.max_card_size} bytes)"
                )
            
            # Build request
            body = PatchMessageRequestBody.builder() \
                .content(content_str) \
                .build()
            
            request = PatchMessageRequest.builder() \
                .message_id(message_id) \
                .request_body(body) \
                .build()
            
            # Send with retry
            retry_count = 0
            retry_delay = 1.0
            
            while retry_count <= max_retries:
                resp = await asyncio.to_thread(self._client.im.v1.message.patch, request)
                
                if resp.code == 0:
                    logger.info(f"Card updated: {message_id[:16]}...")
                    
                    # Notify event handler
                    if self.event_handler:
                        await self.event_handler.on_card_updated(
                            message_id=message_id,
                            chat_id="",  # Not available in PATCH response
                            card_content=card_content
                        )
                    
                    return True
                
                # Rate limit handling
                elif resp.code in [99991400, 429]:
                    if not enable_retry or retry_count >= max_retries:
                        self.last_error = f"Rate limit exceeded after {retry_count} retries"
                        logger.error(self.last_error)
                        return False
                    
                    logger.warning(f"Rate limit hit, retrying in {retry_delay:.1f}s")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                    retry_count += 1
                    continue
                
                # Other errors
                else:
                    self.last_error = f"Failed to update card: code={resp.code}, msg={resp.msg}"
                    logger.error(self.last_error)
                    return False
            
            return False
            
        except Exception as e:
            error_msg = f"Error updating card: {e}"
            logger.error(error_msg, exc_info=True)
            self.last_error = error_msg
            return False
    
    # ==================== Signature Verification ====================
    
    def verify_signature(
        self,
        timestamp: str,
        nonce: str,
        body: str,
        signature: str
    ) -> bool:
        """Verify Feishu webhook signature
        
        Args:
            timestamp: Request timestamp
            nonce: Random nonce
            body: Request body
            signature: Signature from Feishu
            
        Returns:
            True if signature is valid
        """
        if not self.config.encrypt_key:
            logger.warning("encrypt_key not set, skipping signature verification")
            return True
        
        # Generate signature: sha256(timestamp + nonce + encrypt_key + body)
        sign_str = f"{timestamp}{nonce}{self.config.encrypt_key}{body}"
        expected_signature = hashlib.sha256(sign_str.encode()).hexdigest()
        
        is_valid = signature == expected_signature
        
        if not is_valid:
            logger.warning(f"Signature verification failed")
        
        return is_valid
    
    # ==================== User Info Query ====================
    
    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get Feishu user info
        
        Args:
            user_id: Feishu user ID
            
        Returns:
            User info dict or None if failed
        """
        try:
            from lark_oapi.api.contact.v3 import GetUserRequest
            
            req = GetUserRequest.builder().user_id(user_id).build()
            resp = await asyncio.to_thread(self._client.contact.v3.user.get, req)
            
            if resp.code == 0:
                return {
                    "user_id": resp.data.user.user_id,
                    "name": resp.data.user.name,
                    "en_name": resp.data.user.en_name,
                }
            else:
                logger.error(f"Failed to get user info: code={resp.code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user info: {e}", exc_info=True)
            return None
    
    # ==================== Helper Methods ====================
    
    def _format_content(self, content: str, msg_type: str) -> str:
        """Format message content based on type
        
        Args:
            content: Raw content
            msg_type: Message type
            
        Returns:
            Formatted content string
        """
        if msg_type == "text":
            return json.dumps({"text": content})
        else:
            return content
    
    def set_event_handler(self, handler: FeishuEventHandler) -> None:
        """Set event handler
        
        Args:
            handler: Event handler instance
        """
        self.event_handler = handler
        logger.info("Event handler set")
    
    @property
    def is_ready(self) -> bool:
        """Check if client is ready for operations"""
        return self._client is not None and self.config.is_configured
