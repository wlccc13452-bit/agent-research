"""
Action Cards Builder - 操作菜单卡片构建器

Contains card builders for action menus and quick actions.
Business data passed via parameters, no direct service dependencies.
"""

from typing import Any, override
from services.feishu_bot.cards.feishu_bot_card_base import BaseCardBuilder
from services.feishu_bot.cards.feishu_bot_card_templates import StandardCards


class ActionCardsBuilder(BaseCardBuilder):
    """
    Builder for action menu and quick action cards.
    Business data passed via build() parameters.
    """
    
    @override
    def build(
        self,
        card_type: str = "error",
        **kwargs
    ) -> dict[str, Any]:
        """
        Build action card based on type.
        
        Args:
            card_type: Type of card ("error", "stock_action_menu")
            **kwargs: Additional parameters for specific card types
            
        Returns:
            dict[str, Any]: Card JSON structure
        """
        if card_type == "error":
            return self.create_error_card(
                error_msg=kwargs.get("error_msg", "未知错误"),
                title=kwargs.get("title", "[ERROR] 系统错误"),
                show_menu_button=kwargs.get("show_menu_button", True)
            )
        elif card_type == "stock_action_menu":
            return self.create_stock_action_menu(
                stock_code=kwargs.get("stock_code", ""),
                stock_name=kwargs.get("stock_name", ""),
                is_holdings=kwargs.get("is_holdings", True),
                sector_name=kwargs.get("sector_name", ""),
                watch_date=kwargs.get("watch_date", "")
            )
        else:
            return self.create_error_card("未知卡片类型")
    
    def create_error_card(
        self,
        error_msg: str,
        title: str = "[ERROR] 系统错误",
        show_menu_button: bool = True
    ) -> dict[str, Any]:
        """Create error card with optional menu button
        
        Args:
            error_msg: Error message to display
            title: Card title
            show_menu_button: Whether to show "返回主菜单" button
            
        Returns:
            dict[str, Any]: Error card JSON structure
        """
        # Build error card manually since StandardCards.error_card has different signature
        card = self._create_card_base(title, "red")
        
        # Add error message
        error_content = f"**错误信息：**\n{error_msg}"
        if show_menu_button:
            error_content += "\n\n💡 请稍后重试或联系管理员。"
        
        self._add_elements(card, self._create_div(error_content))
        
        # Add menu button if requested
        if show_menu_button:
            menu_button = self._create_button(
                "返回主菜单",
                {"action": "main_menu"},
                "primary"
            )
            # Schema 2.0: button directly in elements, no action wrapper
            self._add_elements(card, menu_button)
        
        return card
    
    def create_stock_action_menu(
        self,
        stock_code: str,
        stock_name: str,
        is_holdings: bool = True,
        sector_name: str = "",
        watch_date: str = ""
    ) -> dict[str, Any]:
        """Create stock action menu card (Schema 2.0)
        
        Show inline action menu for stock operations:
        - 查询行情 (query_stock_price)
        - 查看详情 (query_stock_detail)
        - 技术分析 (technical_analysis)
        - 删除持仓/关注 (delete_stock_from_holdings/watchlist)
        
        Args:
            stock_code: Stock code
            stock_name: Stock name
            is_holdings: Whether this is holdings (True) or watchlist (False)
            sector_name: Sector name (for holdings)
            watch_date: Watch date (for watchlist)
            
        Returns:
            dict[str, Any]: Action menu card JSON structure
        """
        card = self._create_card_base(f"[CHART] {stock_name} 操作", "blue")
        
        # Stock info
        self._add_elements(card,
            self._create_markdown(f"**{stock_name}** ({stock_code})"),
            self._create_hr()
        )
        
        # Query actions
        query_actions = [
            {
                "tag": "button",
                "text": {"tag": "plain_text", "content": "查询行情"},
                "type": "primary",
                "value": {
                    "action": "query_stock_price",
                    "stock_code": stock_code,
                    "stock_name": stock_name
                }
            },
            {
                "tag": "button",
                "text": {"tag": "plain_text", "content": "查看详情"},
                "type": "default",
                "value": {
                    "action": "query_stock_detail",
                    "stock_code": stock_code,
                    "stock_name": stock_name
                }
            }
        ]
        self._add_elements(card, self._create_button_row(query_actions))
        
        # Technical analysis
        tech_actions = [
            {
                "tag": "button",
                "text": {"tag": "plain_text", "content": "技术分析"},
                "type": "default",
                "value": {
                    "action": "technical_analysis",
                    "stock_code": stock_code,
                    "stock_name": stock_name
                }
            }
        ]
        self._add_elements(card, self._create_button_row(tech_actions))
        
        # Divider
        self._add_elements(card, self._create_hr())
        
        # Delete and back actions
        delete_action = "delete_stock_from_holdings" if is_holdings else "delete_stock_from_watchlist"
        back_action = "view_holdings" if is_holdings else "view_watchlist"
        delete_text = "删除持仓" if is_holdings else "删除关注"
        
        delete_value = {
            "action": delete_action,
            "stock_code": stock_code,
            "stock_name": stock_name
        }
        
        # Add context-specific fields
        if is_holdings and sector_name:
            delete_value["sector_name"] = sector_name
        elif not is_holdings and watch_date:
            delete_value["watch_date"] = watch_date
        
        final_actions = [
            {
                "tag": "button",
                "text": {"tag": "plain_text", "content": delete_text},
                "type": "danger",
                "value": delete_value
            },
            {
                "tag": "button",
                "text": {"tag": "plain_text", "content": "返回"},
                "type": "default",
                "value": {"action": back_action}
            }
        ]
        
        self._add_elements(card, self._create_action_row(final_actions))
        
        return card
    
    def _create_action_row(self, actions: list[dict]) -> dict[str, Any]:
        """DEPRECATED: Schema 2.0 does not support action tag
        Use _create_button_row() instead
        """
        # Redirect to button_row for Schema 2.0 compatibility
        return self._create_button_row(actions)
