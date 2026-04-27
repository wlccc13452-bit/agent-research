"""
Base Card Builder - 基础卡片构建器

Provides common utilities and base methods for card creation.
Implements CardBuilder interface for SDK-level consistency.
"""

from typing import Any, override

# 从interfaces.py导入CardBuilder接口，避免重复定义
from feishu_sdk.config.interfaces import CardBuilder


class BaseCardBuilder(CardBuilder):
    """
    Base class for card builders with common utilities.
    Implements CardBuilder interface and provides helper methods.
    
    支持参数化构建：
    - 通过 set_data() 注入业务数据
    - 通过 build() 的 **kwargs 传递参数
    - 支持链式调用
    """
    
    def __init__(self) -> None:
        """初始化builder，创建数据存储"""
        self._data: dict[str, Any] = {}
    
    def set_data(self, **kwargs: Any) -> 'BaseCardBuilder':
        """
        设置业务数据（支持链式调用）
        
        Args:
            **kwargs: 业务数据键值对
            
        Returns:
            BaseCardBuilder: self（支持链式调用）
        """
        self._data.update(kwargs)
        return self
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """
        获取业务数据
        
        Args:
            key: 数据键
            default: 默认值
            
        Returns:
            Any: 数据值
        """
        return self._data.get(key, default)
    
    @override
    def build(self, **kwargs: Any) -> dict[str, Any]:
        """
        Default build implementation - should be overridden by subclasses.
        
        Args:
            **kwargs: Business data for card construction
            
        Returns:
            dict[str, Any]: Default error card indicating unimplemented
        """
        # 合并kwargs到_data
        self._data.update(kwargs)
        return self._create_error_card(
            "卡片构建器未实现 build() 方法",
            "构建错误"
        )
    
    def build_card(self, data: Any | None = None, **kwargs: Any) -> dict[str, Any]:
        """Compatibility method for SDK protocol callers"""
        if isinstance(data, dict):
            kwargs = {**data, **kwargs}
        return self.build(**kwargs)
    
    @staticmethod
    def _create_div(text: str, tag: str = "lark_md") -> dict[str, Any]:
        """Create a div element with text"""
        return {
            "tag": "div",
            "text": {
                "tag": tag,
                "content": text
            }
        }
    
    @staticmethod
    def _create_markdown(content: str) -> dict[str, Any]:
        """Create a div element with markdown content (alias for _create_div with lark_md tag)"""
        return {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": content
            }
        }
    
    @staticmethod
    def _create_action(*actions: dict[str, Any]) -> dict[str, Any]:
        """
        DEPRECATED: Schema 2.0 does not support action tag
        Use _create_button_row() instead
        
        This method now returns a button row for backward compatibility
        """
        # Convert to button row for Schema 2.0
        return BaseCardBuilder._create_button_row(list(actions))
    
    @staticmethod
    def _create_hr() -> dict[str, Any]:
        """Create a horizontal rule element"""
        return {"tag": "hr"}
    
    @staticmethod
    def _create_select_static(
        name: str,
        placeholder: str,
        options: list[dict[str, Any]],
        required: bool = False  # Keep param for backward compatibility but don't use
    ) -> dict[str, Any]:
        """Create a select_static dropdown element"""
        return {
            "tag": "select_static",
            "name": name,
            "placeholder": {"tag": "plain_text", "content": placeholder},
            "options": options
        }
    
    @staticmethod
    def _create_column_set(columns: list[dict[str, Any]]) -> dict[str, Any]:
        """Create a column_set with multiple columns"""
        return {
            "tag": "column_set",
            "flex_mode": "stretch",
            "columns": columns
        }
    
    @staticmethod
    def _create_column(elements: list[dict[str, Any]], width: str = "weighted", weight: int = 1) -> dict[str, Any]:
        """Create a column element"""
        return {
            "tag": "column",
            "width": width,
            "weight": weight,
            "elements": elements
        }
    
    @staticmethod
    def _create_button_row(buttons: list[dict[str, Any]]) -> dict[str, Any]:
        """Create a row of buttons using column_set"""
        columns = []
        for btn in buttons:
            columns.append({
                "tag": "column",
                "width": "weighted",
                "weight": 1,
                "elements": [btn]
            })
        
        return {
            "tag": "column_set",
            "flex_mode": "stretch",
            "columns": columns
        }
    
    @staticmethod
    def _create_button(
        text: str,
        value: dict[str, Any],
        button_type: str = "primary",
        name: str | None = None,
        size: str = "medium",
        disabled: bool = False
    ) -> dict[str, Any]:
        """Create a button element for column_set"""
        button = {
            "tag": "button",
            "text": {"tag": "plain_text", "content": text},
            "type": button_type,
            "size": size,
            "disabled": disabled,
            "value": value
        }
        if name:
            button["name"] = name
        return button
    
    @staticmethod
    def _create_input(
        placeholder: str,
        name: str,
        input_type: str = "text",
        required: bool = False,
        label: str | None = None
    ) -> dict[str, Any]:
        """Create an input element (Schema 2.0 compliant)
        
        Args:
            placeholder: Input placeholder text
            name: Input field name (used as key in form_data)
            input_type: Input type (text, number, etc.)
            required: Whether field is required (uses validate.allow_empty)
            label: Optional label text
            
        Returns:
            dict[str, Any]: Schema 2.0 compliant input element
        """
        element = {
            "tag": "input",
            "name": name,
            "action_type": "request",  # Required for backend callback
            "placeholder": {
                "tag": "plain_text",
                "content": placeholder
            },
            "input_type": input_type
        }
        
        # Schema 2.0: validate not supported in input element
        # Validation should be handled in backend logic
        # if required:
        #     # Backend validation required
        #     pass
        
        if label:
            element["label"] = {"tag": "plain_text", "content": label}
        
        return element
    
    @staticmethod
    def _create_card_base(
        title: str,
        template: str = "blue",
        wide_screen: bool = True
    ) -> dict[str, Any]:
        """Create a basic card structure with header"""
        card = {
            "schema": "2.0",
            "header": {
                "template": template,
                "title": {
                    "tag": "plain_text",
                    "content": title
                }
            },
            "body": {
                "elements": []
            }
        }
        if wide_screen:
            card["config"] = {"wide_screen_mode": True}
        return card
    
    @staticmethod
    def _add_elements(card: dict[str, Any], *elements: dict[str, Any]) -> None:
        """Add elements to card body"""
        if "body" in card and "elements" in card["body"]:
            card["body"]["elements"].extend(elements)
        elif "elements" in card:
            # Schema 1.0格式
            card["elements"].extend(elements)
    
    @staticmethod
    def _create_loading_indicator(message: str = "加载中...") -> dict[str, Any]:
        """Create loading indicator element"""
        return {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"⏳ {message}"
            }
        }
    
    @staticmethod
    def _create_error_card(error_msg: str, title: str = "操作失败") -> dict[str, Any]:
        """Create error card"""
        return {
            "schema": "2.0",
            "header": {
                "template": "red",
                "title": {"tag": "plain_text", "content": title}
            },
            "body": {
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"[ERROR] {error_msg}"
                        }
                    }
                ]
            }
        }
    
    @staticmethod
    def _create_success_card(message: str, title: str = "操作成功") -> dict[str, Any]:
        """Create success card"""
        return {
            "schema": "2.0",
            "header": {
                "template": "green",
                "title": {"tag": "plain_text", "content": title}
            },
            "body": {
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"[OK] {message}"
                        }
                    }
                ]
            }
        }
