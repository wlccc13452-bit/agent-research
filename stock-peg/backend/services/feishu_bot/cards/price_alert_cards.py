"""
Price Alert Card Builder - Price Alert Card Constructor

Contains card builders for price alert management.
Business data passed via parameters, no direct service dependencies.

Schema 2.0 Compliant - All cards follow Feishu Schema 2.0 specification
"""

from typing import Any, override
from services.feishu_bot.cards.feishu_bot_card_base import BaseCardBuilder


class PriceAlertCardBuilder(BaseCardBuilder):
    """
    Builder for price alert-related cards.
    Business data passed via build() parameters.
    """
    
    @override
    def build(
        self,
        card_type: str = "menu",
        **kwargs
    ) -> dict[str, Any]:
        """
        Build price alert card based on type.
        
        Args:
            card_type: Type of card ("menu", "monitor_setup", "monitor_config", "alert", "query")
            **kwargs: Additional parameters for specific card types
            
        Returns:
            dict[str, Any]: Price alert card JSON structure
        """
        if card_type == "menu":
            return self.create_price_alert_menu_card()
        elif card_type == "monitor_setup":
            return self.create_monitor_setup_card()
        elif card_type == "monitor_config":
            return self.create_monitor_config_card(
                holdings_stocks=kwargs.get("holdings_stocks")
            )
        elif card_type == "alert":
            return self.create_price_alert_card()
        elif card_type == "query":
            return self.create_price_query_card()
        else:
            return self.create_price_alert_menu_card()
    
    def create_price_alert_menu_card(self) -> dict[str, Any]:
        """Create price alert menu card (Schema 2.0)"""
        return {
            "schema": "2.0",
            "header": {
                "template": "orange",
                "title": {"tag": "plain_text", "content": "Price Alert Center"}
            },
            "body": {
                "elements": [
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": "**Price Alert Center** - Set price or change % alerts"}
                    },
                    {"tag": "hr"},
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": "Quick Actions"}
                    },
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
                                    "text": {"tag": "plain_text", "content": "View Alerts"},
                                    "type": "primary",
                                    "value": {"action": "view_price_alerts"}
                                }]
                            },
                            {
                                "tag": "column",
                                "width": "weighted",
                                "weight": 1,
                                "elements": [{
                                    "tag": "button",
                                    "text": {"tag": "plain_text", "content": "Create Alert"},
                                    "type": "default",
                                    "value": {"action": "create_price_alert"}
                                }]
                            },
                            {
                                "tag": "column",
                                "width": "weighted",
                                "weight": 1,
                                "elements": [{
                                    "tag": "button",
                                    "text": {"tag": "plain_text", "content": "Create Monitor"},
                                    "type": "default",
                                    "value": {"action": "create_price_monitor"}
                                }]
                            }
                        ]
                    },
                    {"tag": "hr"},
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": "Tip: Alerts support target price or change % trigger\nMonitor: Real-time monitoring during trading hours"}
                    }
                ]
            }
        }
    
    def create_monitor_setup_card(self) -> dict[str, Any]:
        """
        Create monitor setup card (Schema 2.0)
        
        IMPORTANT: All form inputs and submit button must be wrapped in a single <form> tag
        to ensure form_data is properly captured on button click.
        """
        # Build form elements (all inputs must have input_type="text")
        form_elements = [
            {
                "tag": "input",
                "name": "stock_code",
                "input_type": "text",
                "placeholder": {"tag": "plain_text", "content": "Stock code (e.g. 000001)"},
                "label": {"tag": "plain_text", "content": "Stock Code"}
            },
            {
                "tag": "input",
                "name": "ref_price",
                "input_type": "text",
                "placeholder": {"tag": "plain_text", "content": "Ref price (optional, e.g. 15.50)"},
                "label": {"tag": "plain_text", "content": "Ref Price"}
            },
            {
                "tag": "input",
                "name": "up_alert_pct",
                "input_type": "text",
                "placeholder": {"tag": "plain_text", "content": "Up alert % (e.g. 5.0 for 5%)"},
                "label": {"tag": "plain_text", "content": "Up Alert %"}
            },
            {
                "tag": "input",
                "name": "down_alert_pct",
                "input_type": "text",
                "placeholder": {"tag": "plain_text", "content": "Down alert % (e.g. 3.0 for 3%)"},
                "label": {"tag": "plain_text", "content": "Down Alert %"}
            },
            {
                "tag": "input",
                "name": "notes",
                "input_type": "text",
                "placeholder": {"tag": "plain_text", "content": "Notes (optional)"},
                "label": {"tag": "plain_text", "content": "Notes"}
            },
            {
                "tag": "button",
                "text": {"tag": "plain_text", "content": "Start Monitor"},
                "type": "primary",
                "action_type": "form_submit",
                "value": {"action": "save_monitor_task"}
            }
        ]
        
        # Wrap all form elements in a <form> tag
        form_container = {
            "tag": "form",
            "name": "monitor_setup_form",
            "elements": form_elements
        }
        
        return {
            "schema": "2.0",
            "header": {
                "template": "orange",
                "title": {"tag": "plain_text", "content": "Create Price Monitor"}
            },
            "body": {
                "elements": [
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": "Set monitoring parameters, system will push alerts when price reaches threshold"}
                    },
                    {"tag": "hr"},
                    form_container,  # Form container with all inputs and submit button
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": "System will monitor during trading hours and push alerts when threshold reached"}
                    }
                ]
            }
        }
    
    def create_monitor_config_card(
        self,
        holdings_stocks: list[dict] = None
    ) -> dict[str, Any]:
        """
        Create monitor config card (Schema 2.0)
        
        IMPORTANT: All form inputs and submit button must be wrapped in a single <form> tag
        to ensure form_data is properly captured on button click.
        """
        # Build form elements
        form_elements = []
        
        # Stock selector (if available)
        stock_options = []
        if holdings_stocks:
            for stock in holdings_stocks[:15]:
                stock_name = stock.get('name', '')
                stock_code = stock.get('code', '')
                stock_options.append({
                    "text": {"tag": "plain_text", "content": f"{stock_name} ({stock_code})"},
                    "value": stock_code
                })
        
        if stock_options:
            form_elements.append({
                "tag": "select_static",
                "name": "stock_select",
                "placeholder": {"tag": "plain_text", "content": "Select stock..."},
                "options": stock_options
            })
            form_elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": "Or enter stock code manually:"}
            })
        
        # Input fields (all must have input_type="text")
        form_elements.extend([
            {
                "tag": "input",
                "name": "stock_code_input",
                "input_type": "text",
                "placeholder": {"tag": "plain_text", "content": "Stock code (e.g. 000001)"},
                "label": {"tag": "plain_text", "content": "Stock Code"}
            },
            {
                "tag": "input",
                "name": "ref_price",
                "input_type": "text",
                "placeholder": {"tag": "plain_text", "content": "Ref price (optional)"},
                "label": {"tag": "plain_text", "content": "Ref Price"}
            },
            {
                "tag": "select_static",
                "name": "change_rate",
                "placeholder": {"tag": "plain_text", "content": "Select change threshold..."},
                "options": [
                    {"text": {"tag": "plain_text", "content": "1% slight"}, "value": "1"},
                    {"text": {"tag": "plain_text", "content": "2% small"}, "value": "2"},
                    {"text": {"tag": "plain_text", "content": "3% medium"}, "value": "3"},
                    {"text": {"tag": "plain_text", "content": "5% large"}, "value": "5"},
                    {"text": {"tag": "plain_text", "content": "8% significant"}, "value": "8"},
                    {"text": {"tag": "plain_text", "content": "10% major"}, "value": "10"}
                ]
            },
            {
                "tag": "input",
                "name": "notes",
                "input_type": "text",
                "placeholder": {"tag": "plain_text", "content": "Notes (optional)"},
                "label": {"tag": "plain_text", "content": "Notes"}
            }
        ])
        
        form_elements.append({
            "tag": "button",
            "text": {"tag": "plain_text", "content": "Confirm"},
            "type": "primary",
            "action_type": "form_submit",
            "value": {"action": "confirm_create_price_alert"}
        })
        form_elements.append({
            "tag": "button",
            "text": {"tag": "plain_text", "content": "Cancel"},
            "type": "default",
            "value": {"action": "cancel_add"}
        })
        
        # Wrap all form elements in a <form> tag
        form_container = {
            "tag": "form",
            "name": "price_alert_form",
            "elements": form_elements
        }
        
        # Build final card structure
        return {
            "schema": "2.0",
            "header": {
                "template": "blue",
                "title": {"tag": "plain_text", "content": "Price Monitor Config"}
            },
            "body": {
                "elements": [
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": "**Configure Price Monitor**\n\nSystem will auto-monitor and push alerts during trading hours"}
                    },
                    {"tag": "hr"},
                    form_container,  # Form container with all inputs and submit button
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": "Tip: System checks price every minute during trading hours and pushes alerts when threshold reached"}
                    }
                ]
            }
        }
    
    def create_price_alert_card(self) -> dict[str, Any]:
        """
        Create price alert setup card (Schema 2.0)
        
        IMPORTANT: All form inputs and submit button must be wrapped in a single <form> tag
        to ensure form_data is properly captured on button click.
        """
        # Build form elements (all inputs must have input_type="text")
        form_elements = [
            {
                "tag": "input",
                "name": "stock_code",
                "input_type": "text",
                "placeholder": {"tag": "plain_text", "content": "Stock code (e.g. 000001)"},
                "label": {"tag": "plain_text", "content": "Stock Code"}
            },
            {
                "tag": "input",
                "name": "target_price",
                "input_type": "text",
                "placeholder": {"tag": "plain_text", "content": "Target price (optional, e.g. 15.0)"},
                "label": {"tag": "plain_text", "content": "Target Price"}
            },
            {
                "tag": "div",
                "text": {"tag": "lark_md", "content": "**Change % Settings**"}
            },
            {
                "tag": "input",
                "name": "change_up_pct",
                "input_type": "text",
                "placeholder": {"tag": "plain_text", "content": "Up % (optional, e.g. 5.0)"},
                "label": {"tag": "plain_text", "content": "Up %"}
            },
            {
                "tag": "input",
                "name": "change_down_pct",
                "input_type": "text",
                "placeholder": {"tag": "plain_text", "content": "Down % (optional, e.g. 3.0)"},
                "label": {"tag": "plain_text", "content": "Down %"}
            },
            {
                "tag": "input",
                "name": "notes",
                "input_type": "text",
                "placeholder": {"tag": "plain_text", "content": "Notes (optional)"},
                "label": {"tag": "plain_text", "content": "Notes"}
            },
            {
                "tag": "button",
                "text": {"tag": "plain_text", "content": "Create Alert"},
                "type": "primary",
                "action_type": "form_submit",
                "value": {"action": "confirm_create_price_alert"}
            }
        ]
        
        # Wrap all form elements in a <form> tag
        form_container = {
            "tag": "form",
            "name": "price_alert_form",
            "elements": form_elements
        }
        
        return {
            "schema": "2.0",
            "header": {
                "template": "orange",
                "title": {"tag": "plain_text", "content": "Create Price Alert"}
            },
            "body": {
                "elements": [
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": "**Create Price Alert** - Monitor target price and change % (at least one required)"}
                    },
                    {"tag": "hr"},
                    form_container,  # Form container with all inputs and submit button
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": "Tip: Alert triggers when any condition met (target price, up %, down %)"}
                    }
                ]
            }
        }
    
    def create_price_query_card(self) -> dict[str, Any]:
        """
        Create price query card (Schema 2.0)

        Schema 2.0 规范：
        - form.elements 内直接放 input 和 button，禁止用 action/column_set 包裹
        - 提交按钮设置 action_type="form_submit"
        """
        form_elements = [
            {
                "tag": "input",
                "name": "stock_code",
                "input_type": "text",
                "placeholder": {"tag": "plain_text", "content": "Stock code or name"},
                "label": {"tag": "plain_text", "content": "Stock Code"}
            },
            {
                "tag": "button",
                "text": {"tag": "plain_text", "content": "Query Price"},
                "type": "primary",
                "action_type": "form_submit",
                "value": {"action": "query_price"}
            }
        ]
        
        return {
            "schema": "2.0",
            "header": {
                "template": "blue",
                "title": {"tag": "plain_text", "content": "Price Query"}
            },
            "body": {
                "elements": [
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": "Enter stock code to view current price and change %"}
                    },
                    {"tag": "hr"},
                    {
                        "tag": "form",
                        "name": "price_query_form",
                        "elements": form_elements
                    }
                ]
            }
        }
