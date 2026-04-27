"""
Type Protocols for Feishu Services

This module defines Protocol interfaces for dependency injection,
ensuring type safety across the service layer.

Following AGENTS.md principle: "Type Safety - Use explicit types, avoid Any"
"""
from typing import Protocol, runtime_checkable, Any, Optional, Callable, Awaitable


@runtime_checkable
class CardServiceProtocol(Protocol):
    """Protocol for FeishuCardService dependency injection"""
    
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
            message_id: Optional message ID for updates
            
        Returns:
            Tuple of (success, message_id)
        """
        ...
    
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
            update_strategy: Update strategy (replace/merge)
            
        Returns:
            True if update succeeded
        """
        ...
    
    def set_long_connection_service(self, service: Any) -> None:
        """Inject long connection service"""
        ...


@runtime_checkable
class LongConnectionServiceProtocol(Protocol):
    """Protocol for FeishuLongConnectionService dependency injection"""
    
    def set_card_service(self, card_service: CardServiceProtocol) -> None:
        """Inject card service"""
        ...
    
    def start(self) -> bool:
        """Start the long connection service"""
        ...
    
    def stop(self) -> bool:
        """Stop the long connection service"""
        ...


@runtime_checkable
class BusinessLogicServiceProtocol(Protocol):
    """Protocol for BusinessLogicService dependency injection"""
    
    def set_card_service(self, card_service: CardServiceProtocol) -> None:
        """Inject card service"""
        ...
    
    def set_main_loop(self, loop: Any) -> None:
        """Set main event loop"""
        ...
    
    async def handle_command(
        self,
        command: str,
        user_id: str,
        chat_id: str,
        message_id: str,
        **kwargs: Any
    ) -> bool:
        """Handle a user command
        
        Args:
            command: Command to execute
            user_id: User ID
            chat_id: Chat ID
            message_id: Message ID
            **kwargs: Additional parameters
            
        Returns:
            True if command handled successfully
        """
        ...


@runtime_checkable
class CardActionServiceProtocol(Protocol):
    """Protocol for CardActionService dependency injection"""
    
    def set_card_service(self, card_service: CardServiceProtocol) -> None:
        """Inject card service"""
        ...
    
    def set_business_service(self, business_service: BusinessLogicServiceProtocol) -> None:
        """Inject business logic service"""
        ...
    
    async def handle_card_action(self, data: Any) -> dict[str, Any]:
        """Handle card interaction event
        
        Args:
            data: Card action event data
            
        Returns:
            Response dict
        """
        ...


@runtime_checkable
class WebSocketConnectionServiceProtocol(Protocol):
    """Protocol for WebSocketConnectionService dependency injection"""
    
    def start(self) -> bool:
        """Start WebSocket connection"""
        ...
    
    def stop(self) -> None:
        """Stop WebSocket connection"""
        ...
    
    def set_on_message_callback(self, callback: Any) -> None:
        """Set message callback"""
        ...


@runtime_checkable
class MessageDispatcherProtocol(Protocol):
    """Protocol for MessageDispatcher dependency injection"""
    
    def set_card_service(self, card_service: CardServiceProtocol) -> None:
        """Inject card service"""
        ...
    
    async def dispatch_message(
        self,
        user_id: str,
        chat_id: str,
        message: str,
        message_id: str,
        **kwargs: Any
    ) -> bool:
        """Dispatch message to appropriate handler
        
        Args:
            user_id: User ID
            chat_id: Chat ID
            message: Message content
            message_id: Message ID
            **kwargs: Additional parameters
            
        Returns:
            True if dispatched successfully
        """
        ...


@runtime_checkable
class CardStateManagerProtocol(Protocol):
    """Protocol for CardStateManager dependency injection"""
    
    def get_card_state(self, message_id: str) -> Optional[tuple[str, float]]:
        """Get card state by message ID
        
        Args:
            message_id: Message ID
            
        Returns:
            Tuple of (status, timestamp) or None
        """
        ...
    
    def set_card_state(self, message_id: str, status: str, timestamp: Optional[float] = None) -> None:
        """Set card state
        
        Args:
            message_id: Message ID
            status: Card status
            timestamp: Optional timestamp (defaults to now)
        """
        ...
    
    def clear_card_state(self, message_id: str) -> None:
        """Clear card state
        
        Args:
            message_id: Message ID
        """
        ...


@runtime_checkable
class CardBuilderProtocol(Protocol):
    """Protocol for card builders dependency injection"""
    
    def build(self, **kwargs: Any) -> dict[str, Any]:
        """Build a card with keyword arguments"""
        ...
    
    def build_card(self, data: Any, **kwargs: Any) -> dict[str, Any]:
        """Build a card
        
        Args:
            data: Data to build card from
            **kwargs: Additional parameters
            
        Returns:
            Card JSON structure
        """
        ...


@runtime_checkable
class EventHandlerProtocol(Protocol):
    """Protocol for event handlers dependency injection"""
    
    async def on_message(self, user_id: str, chat_id: str, message: str, message_id: str) -> None:
        """Handle message event
        
        Args:
            user_id: User ID
            chat_id: Chat ID
            message: Message content
            message_id: Message ID
        """
        ...
    
    async def on_card_action(self, data: Any) -> dict[str, Any]:
        """Handle card action event
        
        Args:
            data: Card action data
            
        Returns:
            Response dict
        """
        ...


@runtime_checkable
class MessageHandlerProtocol(Protocol):
    """Protocol for message handling (save, log, etc.)"""
    
    async def save_message(self, user_id: str, chat_id: str, message: str) -> None:
        """Save message to storage
        
        Args:
            user_id: User ID
            chat_id: Chat ID
            message: Message content
        """
        ...


# Type aliases for common patterns
CardContent = dict[str, Any]
EventHandler = Callable[[Any], Awaitable[None]]
MessageCallback = Callable[[str, str, str, str], Awaitable[bool]]


__all__ = [
    'CardServiceProtocol',
    'LongConnectionServiceProtocol',
    'BusinessLogicServiceProtocol',
    'CardActionServiceProtocol',
    'WebSocketConnectionServiceProtocol',
    'MessageDispatcherProtocol',
    'CardStateManagerProtocol',
    'CardBuilderProtocol',
    'EventHandlerProtocol',
    'MessageHandlerProtocol',
    'CardContent',
    'EventHandler',
    'MessageCallback',
]
