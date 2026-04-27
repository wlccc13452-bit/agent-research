"""
Menu Card Builder - 菜单卡片构建器

Contains card builders for menus and navigation.
Business data passed via parameters, no direct service dependencies.
"""

from typing import Any, override
from services.feishu_bot.cards.feishu_bot_card_base import BaseCardBuilder
from config.constants import BOT_NAME, BOT_VERSION


class MenuCardBuilder(BaseCardBuilder):
    """
    Builder for menu and navigation cards.
    Business data passed via build() parameters.
    """
    
    @override
    def build(
        self,
        card_type: str = "main_menu",
        **kwargs
    ) -> dict[str, Any]:
        """
        Build menu card based on type.
        
        Args:
            card_type: Type of card ("main_menu", "monitor_setup")
            **kwargs: Additional parameters for specific card types
            
        Returns:
            dict[str, Any]: Menu card JSON structure
        """
        if card_type == "main_menu":
            return self.create_main_menu_card()
        elif card_type == "monitor_setup":
            return self.create_monitor_setup_card()
        else:
            return self.create_main_menu_card()
    
    def create_main_menu_card(self) -> dict[str, Any]:
        """Create main menu card"""
        card = self._create_card_base(f"[BOT] {BOT_NAME} - 智能股票助手", "blue")
        
        self._add_elements(card,
            self._create_div(f"**{BOT_NAME} v{BOT_VERSION}** - 请选择功能模块"),
            self._create_hr(),
            self._create_div("[CHART] **查询功能**")
        )
        
        # Query buttons
        query_buttons = [
            self._create_button("股票查询", {"action": "stock_query_menu"}, "primary"),
            self._create_button("价格查询", {"action": "price_query_menu"}, "primary"),
        ]
        self._add_elements(card, self._create_button_row(query_buttons))
        
        # View section
        self._add_elements(card,
            self._create_hr(),
            self._create_div("📈 **查看列表**")
        )
        
        view_buttons = [
            self._create_button("查看持仓", {"action": "view_holdings"}, "primary"),
            self._create_button("查看关注", {"action": "view_watchlist"}, "primary"),
        ]
        self._add_elements(card, self._create_button_row(view_buttons))
        
        # Management section
        self._add_elements(card,
            self._create_hr(),
            self._create_div("💼 **管理功能**")
        )
        
        mgmt_buttons = [
            self._create_button("持仓管理", {"action": "holdings_menu"}, "default"),
            self._create_button("关注管理", {"action": "watchlist_menu"}, "default"),
            self._create_button("价格提醒", {"action": "price_alert_menu"}, "default"),
        ]
        self._add_elements(card, self._create_button_row(mgmt_buttons))
        
        # Tips
        self._add_elements(card,
            self._create_hr(),
            self._create_div("💡 提示: 点击功能按钮即可使用\n📚 文档: 查看帮助中心了解更多")
        )
        
        return card
    
    def create_monitor_setup_card(self) -> dict[str, Any]:
        """
        Create monitor setup card
        
        IMPORTANT: All form inputs and submit button must be wrapped in a single <form> tag
        to ensure form_data is properly captured on button click.
        """
        # Build form elements (all inputs must have input_type="text")
        form_elements = [
            {
                "tag": "input",
                "name": "reference_price",
                "input_type": "text",
                "placeholder": {"tag": "plain_text", "content": "Enter reference price"},
                "label": {"tag": "plain_text", "content": "参考价格"},
                "required": True
            },
            {
                "tag": "input",
                "name": "change_threshold",
                "input_type": "text",
                "placeholder": {"tag": "plain_text", "content": "Enter change threshold %"},
                "label": {"tag": "plain_text", "content": "涨跌幅阈值(%)"},
                "required": True
            },
            {
                "tag": "input",
                "name": "monitor_interval",
                "input_type": "text",
                "placeholder": {"tag": "plain_text", "content": "Enter monitor interval (seconds)"},
                "label": {"tag": "plain_text", "content": "监控间隔(秒)"},
                "required": True
            },
            {
                "tag": "button",
                "text": {"tag": "plain_text", "content": "保存配置"},
                "type": "primary",
                "action_type": "form_submit",
                "value": {"action": "save_monitor_config"}
            },
            {
                "tag": "button",
                "text": {"tag": "plain_text", "content": "取消"},
                "type": "default",
                "value": {"action": "cancel"}
            }
        ]
        
        # Wrap all form elements in a <form> tag
        form_container = {
            "tag": "form",
            "name": "monitor_setup_form",
            "elements": form_elements
        }
        
        card = self._create_card_base("监控设置", "blue")
        
        self._add_elements(card,
            self._create_div("配置价格监控参数"),
            self._create_hr(),
            form_container  # Form container with all inputs and submit buttons
        )
        
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
