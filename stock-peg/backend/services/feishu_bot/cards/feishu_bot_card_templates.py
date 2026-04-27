"""
Standard Card Templates - 标准卡片模板

Provides ready-to-use card templates for common scenarios.
"""

from typing import Any, Optional
from services.feishu_bot.cards.feishu_bot_card_base import BaseCardBuilder


class StandardCards(BaseCardBuilder):
    """标准卡片模板集合 - 提供常用卡片模板"""
    
    def build(self, **kwargs) -> dict[str, Any]:
        """Base build method - not used for template class"""
        raise NotImplementedError("Use specific template methods instead")
    
    @staticmethod
    def loading_card(
        message: str = "加载中...",
        title: str = "处理中",
        template: str = "blue"
    ) -> dict[str, Any]:
        """
        创建加载中卡片
        
        Args:
            message: 加载提示消息
            title: 卡片标题
            template: 卡片颜色模板
            
        Returns:
            dict[str, Any]: 加载中卡片结构
        """
        return {
            "schema": "2.0",
            "header": {
                "template": template,
                "title": {"tag": "plain_text", "content": title}
            },
            "body": {
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"⏳ {message}"
                        }
                    }
                ]
            }
        }
    
    @staticmethod
    def success_card(
        message: str,
        title: str = "操作成功",
        template: str = "green"
    ) -> dict[str, Any]:
        """
        创建成功卡片
        
        Args:
            message: 成功消息
            title: 卡片标题
            template: 卡片颜色模板
            
        Returns:
            dict[str, Any]: 成功卡片结构
        """
        return {
            "schema": "2.0",
            "header": {
                "template": template,
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
    
    @staticmethod
    def error_card(
        error_msg: str,
        title: str = "操作失败",
        template: str = "red",
        details: Optional[str] = None
    ) -> dict[str, Any]:
        """
        创建错误卡片
        
        Args:
            error_msg: 错误消息
            title: 卡片标题
            template: 卡片颜色模板
            details: 错误详情（可选）
            
        Returns:
            dict[str, Any]: 错误卡片结构
        """
        elements = [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"[ERROR] {error_msg}"
                }
            }
        ]
        
        if details:
            elements.append(
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**详细信息**: {details}"
                    }
                }
            )
        
        return {
            "schema": "2.0",
            "header": {
                "template": template,
                "title": {"tag": "plain_text", "content": title}
            },
            "body": {
                "elements": elements
            }
        }
    
    @staticmethod
    def input_card(
        title: str,
        fields: list[dict[str, Any]],
        submit_action: str,
        submit_text: str = "提交",
        cancel_action: Optional[str] = None,
        cancel_text: str = "取消",
        template: str = "blue"
    ) -> dict[str, Any]:
        """
        创建输入表单卡片
        
        Args:
            title: 卡片标题
            fields: 输入字段列表，每个字段包含:
                - name: 字段名
                - placeholder: 占位符文本
                - input_type: 输入类型 (text/number/etc)
                - required: 是否必填
            submit_action: 提交动作标识
            submit_text: 提交按钮文本
            cancel_action: 取消动作标识（可选）
            cancel_text: 取消按钮文本
            template: 卡片颜色模板
            
        Returns:
            dict[str, Any]: 输入表单卡片结构
        """
        elements = []
        
        # Add input fields (Schema 2.0 compliant)
        for field in fields:
            input_element = {
                "tag": "input",
                "name": field.get("name", ""),
                "action_type": "request",  # Required for backend callback
                "placeholder": {
                    "tag": "plain_text",
                    "content": field.get("placeholder", "")
                },
                "input_type": field.get("input_type", "text")
            }
            
            # Schema 2.0: validate not supported in input element
            # Validation handled in backend logic
            # if field.get("required", False):
            #     input_element["validate"] = {
            #         "error_tips": "This field is required",
            #         "allow_empty": False
            #     }
            
            elements.append(input_element)
        
        elements.append({"tag": "hr"})
        
        # Add buttons
        buttons = [
            {
                "tag": "button",
                "text": {"tag": "plain_text", "content": submit_text},
                "type": "primary",
                "value": {"action": submit_action}
            }
        ]
        
        if cancel_action:
            buttons.append(
                {
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": cancel_text},
                    "type": "default",
                    "value": {"action": cancel_action}
                }
            )
        
        # Create button row
        columns = [
            {
                "tag": "column",
                "width": "weighted",
                "weight": 1,
                "elements": [btn]
            }
            for btn in buttons
        ]
        
        elements.append(
            {
                "tag": "column_set",
                "columns": columns
            }
        )
        
        return {
            "schema": "2.0",
            "header": {
                "template": template,
                "title": {"tag": "plain_text", "content": title}
            },
            "body": {
                "elements": elements
            }
        }
    
    @staticmethod
    def confirmation_card(
        title: str,
        message: str,
        confirm_action: str,
        cancel_action: str,
        confirm_text: str = "确认",
        cancel_text: str = "取消",
        template: str = "blue"
    ) -> dict[str, Any]:
        """
        创建确认对话框卡片
        
        Args:
            title: 卡片标题
            message: 确认消息
            confirm_action: 确认动作标识
            cancel_action: 取消动作标识
            confirm_text: 确认按钮文本
            cancel_text: 取消按钮文本
            template: 卡片颜色模板
            
        Returns:
            dict[str, Any]: 确认卡片结构
        """
        buttons = [
            {
                "tag": "button",
                "text": {"tag": "plain_text", "content": confirm_text},
                "type": "primary",
                "value": {"action": confirm_action}
            },
            {
                "tag": "button",
                "text": {"tag": "plain_text", "content": cancel_text},
                "type": "default",
                "value": {"action": cancel_action}
            }
        ]
        
        columns = [
            {
                "tag": "column",
                "width": "weighted",
                "weight": 1,
                "elements": [btn]
            }
            for btn in buttons
        ]
        
        return {
            "schema": "2.0",
            "header": {
                "template": template,
                "title": {"tag": "plain_text", "content": title}
            },
            "body": {
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": message
                        }
                    },
                    {"tag": "hr"},
                    {
                        "tag": "column_set",
                        "columns": columns
                    }
                ]
            }
        }
    
    @staticmethod
    def operation_result_card(
        title: str,
        message: str,
        status: str = "success"
    ) -> dict[str, Any]:
        """
        创建操作结果卡片
        
        Args:
            title: 卡片标题
            message: 卡片内容（支持 Markdown）
            status: 操作状态 ("success", "failed", "warning")
            
        Returns:
            dict[str, Any]: 操作结果卡片结构
        """
        from datetime import datetime
        
        # 根据状态选择颜色和图标
        color_map = {
            "success": ("green", "[OK]"),
            "failed": ("red", "[ERROR]"),
            "warning": ("orange", "[WARN]️")
        }
        template_color, icon = color_map.get(status, ("blue", "ℹ️"))
        
        card = {
            "schema": "2.0",
            "header": {
                "template": template_color,
                "title": {
                    "tag": "plain_text",
                    "content": f"{icon} {title}"
                }
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": message
                    }
                },
                {"tag": "hr"},
                {
                    "tag": "column_set",
                    "flex_mode": "stretch",
                    "columns": [
                        {
                            "tag": "column",
                            "width": "weighted",
                            "weight": 1,
                            "elements": [
                                {
                                    "tag": "button",
                                    "text": {
                                        "tag": "plain_text",
                                        "content": "回到主菜单"
                                    },
                                    "type": "default",
                                    "size": "medium",
                                    "value": {"action": "main_menu"}
                                }
                            ]
                        }
                    ]
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"🕐 操作时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                }
            ]
        }
        return card
    
    @staticmethod
    def info_card(
        title: str,
        content: str | list[str],
        template: str = "blue"
    ) -> dict[str, Any]:
        """
        创建信息展示卡片
        
        Args:
            title: 卡片标题
            content: 内容字符串或字符串列表
            template: 卡片颜色模板
            
        Returns:
            dict[str, Any]: 信息卡片结构
        """
        if isinstance(content, str):
            elements = [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": content
                    }
                }
            ]
        else:
            elements = [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": line
                    }
                }
                for line in content
            ]
        
        return {
            "schema": "2.0",
            "header": {
                "template": template,
                "title": {"tag": "plain_text", "content": title}
            },
            "body": {
                "elements": elements
            }
        }
