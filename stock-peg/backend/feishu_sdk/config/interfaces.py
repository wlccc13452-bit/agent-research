"""
Feishu SDK Core Interfaces - 飞书SDK核心接口定义

本模块定义飞书SDK的核心抽象接口，遵循依赖倒置原则：
- 应用层依赖接口，而非具体实现
- 配置通过构造函数注入，不依赖项目全局配置
- 业务逻辑（股票查询、持仓管理等）保留在应用层
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, Callable, Awaitable
from datetime import datetime


@dataclass
class FeishuConfig:
    """飞书SDK配置类
    
    所有配置通过构造函数注入，不依赖项目全局配置（如config.settings）。
    支持可选配置项，使用Optional类型和默认值。
    
    Attributes:
        app_id: 飞书应用ID
        app_secret: 飞书应用密钥
        encrypt_key: 飞书加密密钥（可选）
        verification_token: 飞书验证令牌（可选）
        bot_name: 机器人名称（默认: PegBot）
        log_level: 日志级别（默认: INFO）
    """
    app_id: str
    app_secret: str
    encrypt_key: Optional[str] = None
    verification_token: Optional[str] = None
    bot_name: str = "PegBot"
    log_level: str = "INFO"
    
    # 长连接配置（可选）
    enable_long_connection: bool = False
    heartbeat_interval: int = 30  # 心跳间隔（秒）
    heartbeat_timeout: int = 90   # 心跳超时（秒）
    
    # 并发控制配置（可选）
    max_concurrent_actions: int = 10
    action_timeout: int = 30
    
    def __post_init__(self) -> None:
        """验证配置完整性"""
        if not self.app_id:
            raise ValueError("app_id is required")
        if not self.app_secret:
            raise ValueError("app_secret is required")
    
    @property
    def is_configured(self) -> bool:
        """检查是否配置完整"""
        return bool(self.app_id and self.app_secret)


class FeishuConfigBuilder:
    """FeishuConfig构建器
    
    提供流式API构建配置对象。
    
    Example:
        config = (FeishuConfigBuilder()
            .with_app_id("your_app_id")
            .with_app_secret("your_app_secret")
            .with_encrypt_key("your_encrypt_key")
            .build())
    """
    
    def __init__(self):
        """初始化构建器"""
        self._config_data = {}
    
    def with_app_id(self, app_id: str) -> "FeishuConfigBuilder":
        """设置app_id"""
        self._config_data["app_id"] = app_id
        return self
    
    def with_app_secret(self, app_secret: str) -> "FeishuConfigBuilder":
        """设置app_secret"""
        self._config_data["app_secret"] = app_secret
        return self
    
    def with_encrypt_key(self, encrypt_key: str) -> "FeishuConfigBuilder":
        """设置encrypt_key"""
        self._config_data["encrypt_key"] = encrypt_key
        return self
    
    def with_verification_token(self, verification_token: str) -> "FeishuConfigBuilder":
        """设置verification_token"""
        self._config_data["verification_token"] = verification_token
        return self
    
    def with_bot_name(self, bot_name: str) -> "FeishuConfigBuilder":
        """设置bot_name"""
        self._config_data["bot_name"] = bot_name
        return self
    
    def with_log_level(self, log_level: str) -> "FeishuConfigBuilder":
        """设置log_level"""
        self._config_data["log_level"] = log_level
        return self
    
    def with_long_connection(
        self, 
        enable: bool = True,
        heartbeat_interval: int = 30,
        heartbeat_timeout: int = 90
    ) -> "FeishuConfigBuilder":
        """配置长连接"""
        self._config_data["enable_long_connection"] = enable
        self._config_data["heartbeat_interval"] = heartbeat_interval
        self._config_data["heartbeat_timeout"] = heartbeat_timeout
        return self
    
    def with_concurrency(
        self,
        max_concurrent_actions: int = 10,
        action_timeout: int = 30
    ) -> "FeishuConfigBuilder":
        """配置并发控制"""
        self._config_data["max_concurrent_actions"] = max_concurrent_actions
        self._config_data["action_timeout"] = action_timeout
        return self
    
    def build(self) -> FeishuConfig:
        """构建FeishuConfig实例
        
        Returns:
            FeishuConfig: 配置对象
            
        Raises:
            ValueError: 如果缺少必需字段
        """
        return FeishuConfig(**self._config_data)


@dataclass
class MessageContext:
    """消息上下文
    
    包含完整的飞书消息事件信息，用于消息处理器处理业务逻辑。
    
    Attributes:
        message_id: 消息唯一ID
        chat_id: 会话ID（群聊或私聊）
        user_id: 发送者ID
        user_name: 发送者名称（可选）
        content: 消息内容
        message_type: 消息类型（text, post, image等）
        send_time: 消息发送时间
        parent_id: 父消息ID（回复消息时使用，可选）
        extra: 额外元数据（可选）
    """
    message_id: str
    chat_id: str
    user_id: str
    content: str
    message_type: str = "text"
    send_time: datetime = field(default_factory=datetime.now)
    user_name: Optional[str] = None
    parent_id: Optional[str] = None
    extra: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """序列化为字典，便于日志记录和数据传输"""
        return {
            "message_id": self.message_id,
            "chat_id": self.chat_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "content": self.content,
            "message_type": self.message_type,
            "send_time": self.send_time.isoformat() if self.send_time else None,
            "parent_id": self.parent_id,
            "extra": self.extra,
        }


@dataclass
class CardActionContext:
    """卡片交互上下文
    
    包含完整的飞书卡片交互事件信息，用于卡片动作处理器处理业务逻辑。
    
    Attributes:
        action_id: 动作ID（按钮、表单提交等）
        message_id: 卡片消息ID
        chat_id: 会话ID
        user_id: 触发者ID
        user_name: 触发者名称（可选）
        action_value: 动作携带的值（dict）
        action_type: 动作类型（button, form_submit等）
        trigger_time: 触发时间
        open_id: 用户open_id（可选，用于权限校验）
        union_id: 用户union_id（可选，用于跨应用识别）
        extra: 额外元数据（可选）
    """
    action_id: str
    message_id: str
    chat_id: str
    user_id: str
    action_value: dict[str, Any]
    action_type: str = "button"
    trigger_time: datetime = field(default_factory=datetime.now)
    user_name: Optional[str] = None
    open_id: Optional[str] = None
    union_id: Optional[str] = None
    extra: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """序列化为字典，便于日志记录和数据传输"""
        return {
            "action_id": self.action_id,
            "message_id": self.message_id,
            "chat_id": self.chat_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "action_value": self.action_value,
            "action_type": self.action_type,
            "trigger_time": self.trigger_time.isoformat() if self.trigger_time else None,
            "open_id": self.open_id,
            "union_id": self.union_id,
            "extra": self.extra,
        }


class FeishuEventHandler(ABC):
    """飞书事件处理器基类
    
    定义事件处理的标准接口，应用层通过继承此基类实现具体业务逻辑。
    所有业务逻辑（股票查询、持仓管理等）保留在应用层实现类中。
    
    Example:
        class StockQueryHandler(FeishuEventHandler):
            async def on_message(self, context: MessageContext) -> str:
                # 实现股票查询逻辑
                stock_name = context.content
                return f"查询结果: {stock_name}"
    """
    
    @abstractmethod
    async def on_message(self, context: MessageContext) -> Optional[str]:
        """处理文本消息
        
        Args:
            context: 消息上下文，包含消息详情
            
        Returns:
            响应消息文本（可选），返回None表示不回复
        """
        pass
    
    @abstractmethod
    async def on_card_action(self, context: CardActionContext) -> Optional[dict[str, Any]]:
        """处理卡片交互
        
        Args:
            context: 卡片交互上下文，包含动作详情
            
        Returns:
            响应卡片内容（dict），返回None表示不更新卡片
        """
        pass
    
    async def on_command(self, command: str, context: MessageContext) -> Optional[str]:
        """处理命令（可选）
        
        Args:
            command: 命令字符串（如"查询 平安银行"）
            context: 消息上下文
            
        Returns:
            响应消息文本（可选），返回None表示不回复
            
        Note:
            此方法为可选实现，默认返回None
        """
        return None
    
    async def on_error(self, error: Exception, context: MessageContext | CardActionContext) -> str:
        """处理错误（可选）
        
        Args:
            error: 异常对象
            context: 事件上下文
            
        Returns:
            错误响应消息
            
        Note:
            此方法为可选实现，默认返回通用错误消息
        """
        return f"[WARN]️ 处理失败: {str(error)}"


class CardBuilder(ABC):
    """卡片构建器接口
    
    定义卡片构建的标准接口，用于生成飞书卡片JSON结构。
    应用层通过继承此接口实现具体卡片的构建逻辑。
    
    Example:
        class StockCardBuilder(CardBuilder):
            def build(self, data: dict[str, Any]) -> dict[str, Any]:
                return {
                    "header": {"title": {"content": data["stock_name"]}},
                    "body": {"elements": [...]}
                }
    """
    
    @abstractmethod
    def build(self, **kwargs) -> dict[str, Any]:
        """构建卡片内容
        
        Args:
            **kwargs: 卡片构建所需的业务数据（如股票信息、持仓列表等）
            
        Returns:
            飞书卡片JSON结构
        """
        pass
    
    def update(self, card: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
        """Update card content (optional)
        
        Args:
            card: Original card content
            updates: Fields to update
            
        Returns:
            Updated card content
            
        Note:
            This method is optional, defaults to returning original card
        """
        return card
    
    def validate(self, card: dict[str, Any]) -> bool:
        """Validate card structure (optional)
        
        Args:
            card: Card content
            
        Returns:
            True if valid
            
        Note:
            This method is optional, defaults to returning True
        """
        return True


class FeishuPlugin(ABC):
    """飞书插件基类
    
    定义插件的标准接口，用于扩展飞书SDK功能。
    插件可以注册事件处理器、命令处理器等。
    
    Example:
        class AlertPlugin(FeishuPlugin):
            def register(self, sdk):
                sdk.register_handler("alert", AlertHandler())
                
            async def on_load(self):
                # 启动告警监控
                pass
    """
    
    @abstractmethod
    def register(self, sdk: Any) -> None:
        """注册插件到SDK
        
        Args:
            sdk: 飞书SDK实例（具体类型由实现层定义）
        """
        pass
    
    async def on_load(self) -> None:
        """插件加载时执行（可选）
        
        Note:
            用于初始化插件资源，如启动后台任务、连接数据库等
        """
        pass
    
    async def on_unload(self) -> None:
        """插件卸载时执行（可选）
        
        Note:
            用于清理插件资源，如停止后台任务、关闭连接等
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """插件名称
        
        Returns:
            插件唯一标识
        """
        pass
    
    @property
    def version(self) -> str:
        """插件版本（可选）
        
        Returns:
            版本号（默认: 1.0.0）
        """
        return "1.0.0"


# 类型别名
EventHandler = Callable[[MessageContext], Awaitable[Optional[str]]]
CardActionHandler = Callable[[CardActionContext], Awaitable[Optional[dict[str, Any]]]]
CommandHandler = Callable[[str, MessageContext], Awaitable[Optional[str]]]


# 导出列表
__all__ = [
    # 配置类
    'FeishuConfig',
    'FeishuConfigBuilder',
    # 上下文类
    'MessageContext',
    'CardActionContext',
    # 事件处理器接口
    'FeishuEventHandler',
    # 卡片构建器接口
    'CardBuilder',
    # 插件基类
    'FeishuPlugin',
    # 类型别名
    'EventHandler',
    'CardActionHandler',
    'CommandHandler',
]
