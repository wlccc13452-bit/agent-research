"""
Watchlist Card Builder - 关注列表卡片构建器

Contains card builders for watchlist management.
Business data passed via parameters, no direct service dependencies.

Refactored to include all watchlist-related card creation methods:
- Watchlist menu card
- Add to watchlist card
- Watchlist display card
- Empty watchlist card
"""

from typing import Any, override
from datetime import datetime, date
from services.feishu_bot.cards.feishu_bot_card_base import BaseCardBuilder


class WatchlistCardBuilder(BaseCardBuilder):
    """
    Builder for watchlist-related cards.
    Business data passed via build() parameters.
    """
    
    @override
    def build(
        self,
        card_type: str = "menu",
        **kwargs
    ) -> dict[str, Any]:
        """
        Build watchlist card based on type.
        
        Args:
            card_type: Type of card ("menu", "display", "add", "empty")
            **kwargs: Additional parameters for specific card types
            
        Returns:
            dict[str, Any]: Watchlist card JSON structure
        """
        if card_type == "menu":
            return self.create_watchlist_menu_card()
        elif card_type == "display":
            return self.create_watchlist_display_card(
                stocks=kwargs.get("stocks", []),
                date_count=kwargs.get("date_count", 0)
            )
        elif card_type == "add":
            return self.create_add_to_watchlist_card(
                holdings_stocks=kwargs.get("holdings_stocks")
            )
        elif card_type == "empty":
            return self.create_empty_watchlist_card()
        else:
            return self.create_watchlist_menu_card()
    
    def create_watchlist_menu_card(self) -> dict[str, Any]:
        """Create watchlist management menu card (Schema 2.0)"""
        return {
            "schema": "2.0",
            "header": {
                "template": "blue",
                "title": {"tag": "plain_text", "content": "Watchlist Management"}
            },
            "body": {
                "elements": [
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": "Manage your dynamic watchlist stocks"}
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
                                "elements": [{
                                    "tag": "button",
                                    "text": {"tag": "plain_text", "content": "View Watchlist"},
                                    "type": "primary",
                                    "value": {"action": "view_watchlist"}
                                }]
                            },
                            {
                                "tag": "column",
                                "width": "weighted",
                                "weight": 1,
                                "elements": [{
                                    "tag": "button",
                                    "text": {"tag": "plain_text", "content": "Add Watch"},
                                    "type": "default",
                                    "value": {"action": "add_to_watchlist"}
                                }]
                            },
                            {
                                "tag": "column",
                                "width": "weighted",
                                "weight": 1,
                                "elements": [{
                                    "tag": "button",
                                    "text": {"tag": "plain_text", "content": "Remove Watch"},
                                    "type": "default",
                                    "value": {"action": "view_watchlist"}
                                }]
                            }
                        ]
                    }
                ]
            }
        }
    
    def create_add_to_watchlist_card(
        self,
        holdings_stocks: list[dict] = None
    ) -> dict[str, Any]:
        """Create add stock to watchlist card (Schema 2.0)
        
        简化版：直接使用 input 输入股票名称/代码
        """
        today = date.today().isoformat()
        
        return {
            "schema": "2.0",
            "header": {
                "template": "blue",
                "title": {"tag": "plain_text", "content": f"➕ 添加关注 ({today})"}
            },
            "body": {
                "elements": [
                    {
                        "tag": "div",
                        "text": {"tag": "plain_text", "content": "请输入股票名称或代码"}
                    },
                    {
                        "tag": "input",
                        "name": "stock_input",
                        "action_type": "request",
                        "placeholder": {"tag": "plain_text", "content": "如: 中国银行 或 601988"},
                        "label": {"tag": "plain_text", "content": "股票"}
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
                                        "text": {"tag": "plain_text", "content": "确认添加"},
                                        "type": "primary",
                                        "value": {"action": "confirm_add_watchlist"}
                                    }
                                ]
                            },
                            {
                                "tag": "column",
                                "width": "weighted",
                                "weight": 1,
                                "elements": [
                                    {
                                        "tag": "button",
                                        "text": {"tag": "plain_text", "content": "取消"},
                                        "type": "default",
                                        "value": {"action": "cancel_add"}
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
    
    def create_watchlist_display_card(self, stocks: list[dict], date_count: int) -> dict[str, Any]:
        """Create watchlist display card with Schema 2.0"""
        # Build stocks content grouped by date
        date_groups = {}
        for stock in stocks:
            date = stock.get("date", "")
            if date not in date_groups:
                date_groups[date] = []
            date_groups[date].append(stock)
        
        # Build elements for each date
        collapse_elements = []
        
        for date, group_stocks in sorted(date_groups.items(), reverse=True):
            # Add date title
            collapse_elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**{date}** ({len(group_stocks)}只)"
                }
            })
            
            # Build buttons for each stock
            stock_buttons = []
            for stock in group_stocks:
                stock_name = stock.get('stock_name', '')
                stock_code = stock.get('stock_code', '')
                
                # Build button text
                button_text = stock_name
                if stock.get('target_price'):
                    button_text += f" 目标:{float(stock['target_price']):.2f}"
                
                # Add button for this stock
                stock_buttons.append({
                    "tag": "button",
                    "text": {"tag": "plain_text", "content": button_text},
                    "type": "default",
                    "size": "medium",
                    "value": {
                        "action": "show_watchlist_actions",
                        "stock_code": stock_code,
                        "stock_name": stock_name,
                        "watch_date": date
                    }
                })
            
            # Group buttons into rows of 3
            for i in range(0, len(stock_buttons), 3):
                row_buttons = stock_buttons[i:i+3]
                columns = []
                for btn in row_buttons:
                    columns.append({
                        "tag": "column",
                        "width": "weighted",
                        "weight": 1,
                        "elements": [btn]
                    })
                
                if columns:
                    collapse_elements.append({
                        "tag": "column_set",
                        "flex_mode": "stretch",
                        "columns": columns
                    })
        
        # Build card
        card = {
            "schema": "2.0",
            "header": {
                "template": "blue",
                "title": {"tag": "plain_text", "content": f"👀 关注列表 ({len(stocks)}只)"}
            },
            "body": {
                "elements": [
                    *collapse_elements,
                    {"tag": "hr"},
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"🕐 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n💡 点击股票查看详情或操作"
                        }
                    }
                ]
            }
        }
        
        return card
    
    def create_empty_watchlist_card(self) -> dict[str, Any]:
        """Create empty watchlist card with guidance"""
        card = {
            "schema": "2.0",
            "header": {
                "template": "grey",
                "title": {"tag": "plain_text", "content": "👀 关注列表为空"}
            },
            "body": {
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": "您可以通过以下方式添加关注:\n\n• 点击下方按钮「➕ 添加关注」\n• 发送命令: 添加关注 [股票名称]"
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
                                        "text": {"tag": "plain_text", "content": "➕ 添加关注"},
                                        "type": "primary",
                                        "size": "medium",
                                        "value": {"action": "add_to_watchlist"}
                                    }
                                ]
                            },
                            {
                                "tag": "column",
                                "width": "weighted",
                                "weight": 1,
                                "elements": [
                                    {
                                        "tag": "button",
                                        "text": {"tag": "plain_text", "content": "🏠 主菜单"},
                                        "type": "default",
                                        "size": "medium",
                                        "value": {"action": "main_menu"}
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        return card
    
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
            "columns": columns
        }
