"""
Holdings Card Builder - 持仓卡片构建器

Contains card builders for holdings management.
Business data passed via parameters, no direct service dependencies.

Refactored to include all holdings-related card creation methods:
- Holdings menu card
- Add stock to holdings card
- Holdings display card
- Empty holdings card
"""

from typing import Any, override
from datetime import datetime
import json
from services.feishu_bot.cards.feishu_bot_card_base import BaseCardBuilder


class HoldingsCardBuilder(BaseCardBuilder):
    """
    Builder for holdings-related cards.
    Business data passed via build() parameters.
    """
    
    @override
    def build(
        self,
        card_type: str = "menu",
        **kwargs
    ) -> dict[str, Any]:
        """
        Build holdings card based on type.
        
        Args:
            card_type: Type of card ("menu", "display", "add", "empty")
            **kwargs: Additional parameters for specific card types
            
        Returns:
            dict[str, Any]: Holdings card JSON structure
        """
        if card_type == "menu":
            return self.create_holdings_menu_card()
        elif card_type == "display":
            return self.create_holdings_display_card(
                holdings=kwargs.get("holdings", {})
            )
        elif card_type == "add":
            return self.create_add_stock_to_holdings_card(
                existing_sectors=kwargs.get("existing_sectors"),
                watchlist_stocks=kwargs.get("watchlist_stocks")
            )
        elif card_type == "empty":
            return self.create_empty_holdings_card()
        else:
            return self.create_holdings_menu_card()
    
    def create_holdings_menu_card(self) -> dict[str, Any]:
        """Create holdings management menu card"""
        card = self._create_card_base("💼 持仓管理", "blue")
        
        self._add_elements(card,
            self._create_div("管理您的自持股票和板块"),
            self._create_hr()
        )
        
        # First row: view, add stock, add sector
        row1_buttons = [
            self._create_button("[CHART] 查看持仓", {"action": "view_holdings"}, "primary"),
            self._create_button("➕ 添加股票", {"action": "add_stock_to_holdings"}, "default"),
            self._create_button("➕ 添加板块", {"action": "add_sector_to_holdings"}, "default"),
        ]
        self._add_elements(card, self._create_button_row(row1_buttons))
        
        # Second row: remove stock, remove sector
        row2_buttons = [
            self._create_button("➖ 删除股票", {"action": "remove_stock_from_holdings"}, "default"),
            self._create_button("➖ 删除板块", {"action": "remove_sector_from_holdings"}, "default"),
        ]
        self._add_elements(card, self._create_button_row(row2_buttons))
        
        return card
    
    def create_add_stock_to_holdings_card(
        self,
        existing_sectors: list[str] = None,
        watchlist_stocks: list[dict] = None
    ) -> dict[str, Any]:
        """Create add stock to holdings card (Schema 2.0)"""
        # Build sector options
        sector_options = []
        if existing_sectors:
            for sector in existing_sectors:
                sector_options.append({
                    "text": {"tag": "plain_text", "content": sector},
                    "value": sector
                })
        
        # Build watchlist stock options
        stock_options = []
        if watchlist_stocks:
            stock_options.append({
                "text": {"tag": "plain_text", "content": "── 从关注列表选择 ──"},
                "value": "divider_watchlist"
            })
            for stock in watchlist_stocks[:10]:
                stock_name = stock.get('name', '')
                stock_code = stock.get('code', '')
                stock_options.append({
                    "text": {"tag": "plain_text", "content": f"{stock_name} ({stock_code})"},
                    "value": f"{stock_code}|{stock_name}"
                })
        
        elements = [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "**添加股票到持仓列表**\n\n可以从关注列表选择，或手动输入新股票"
                }
            },
            {"tag": "hr"}
        ]
        
        # If has watchlist stocks, add selector
        if stock_options:
            elements.extend([
                {
                    "tag": "select_static",
                    "name": "selected_stock_from_watchlist",
                    "placeholder": {"tag": "plain_text", "content": "从关注列表选择股票..."},
                    "options": stock_options
                },
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": "或手动输入新股票："}
                }
            ])
        
        # Stock input
        elements.extend([
            {
                "tag": "input",
                "name": "stock_name",
                "action_type": "request",
                "placeholder": {"tag": "plain_text", "content": "股票名称或代码"},
                "label": {"tag": "plain_text", "content": "股票名称"}
                # Schema 2.0: validate not supported, validation in backend
            }
        ])
        
        # Sector selector or input
        if sector_options:
            elements.append({
                "tag": "select_static",
                "name": "sector_name",
                "placeholder": {"tag": "plain_text", "content": "选择板块..."},
                "options": sector_options + [
                    {"text": {"tag": "plain_text", "content": "-- [NEW] --"}, "value": "new_sector"}
                ]
            })
            elements.append({
                "tag": "input",
                "name": "new_sector_name",
                "action_type": "request",
                "placeholder": {"tag": "plain_text", "content": "Input new sector name"},
                "label": {"tag": "plain_text", "content": "New Sector Name"}
            })
        else:
            elements.append({
                "tag": "input",
                "name": "sector_name",
                "action_type": "request",
                "placeholder": {"tag": "plain_text", "content": "Sector Name"},
                "label": {"tag": "plain_text", "content": "Sector"}
            })
        
        # Buttons
        elements.extend([
            {
                "tag": "button",
                "name": "confirm_btn",
                "text": {"tag": "plain_text", "content": "确认添加"},
                "type": "primary",
                "value": {"action": "confirm_add_stock_holdings"}
            },
            {
                "tag": "button",
                "name": "cancel_btn",
                "text": {"tag": "plain_text", "content": "取消"},
                "type": "default",
                "value": {"action": "cancel_add"}
            }
        ])
        
        return {
            "schema": "2.0",
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "blue",
                "title": {"tag": "plain_text", "content": "添加股票到持仓"}
            },
            "body": {"elements": elements}
        }
    
    def create_holdings_display_card(self, holdings: dict[str, Any]) -> dict[str, Any]:
        """Create holdings display card with Schema 2.0"""
        from config.settings import settings
        
        # Load stock name to code mapping
        stock_name_mapping = {}
        mapping_file = settings.data_dir / "stock_name_mapping.json"
        if mapping_file.exists():
            try:
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        if 'mapping' in data:
                            stock_name_mapping = data.get('mapping', {})
                        else:
                            stock_name_mapping = data
            except Exception:
                pass
        
        # Build elements for each sector
        collapse_elements = []
        total_stocks = 0
        
        for sector in holdings.get("sectors", []):
            stocks = sector.get("stocks", [])
            if stocks:
                # Add sector title
                collapse_elements.append({
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**{sector['name']}** ({len(stocks)}只)"
                    }
                })
                
                # Build buttons for each stock
                stock_buttons = []
                for stock in stocks:
                    if isinstance(stock, dict):
                        stock_name = str(stock.get("name", "")).strip()
                        stock_code = str(stock.get("code", "")).strip()
                    elif hasattr(stock, "name"):
                        stock_name = str(getattr(stock, "name", "")).strip()
                        stock_code = str(getattr(stock, "code", "") or "").strip()
                    else:
                        stock_name = str(stock).strip()
                        stock_code = stock_name_mapping.get(stock_name, "")
                    
                    if not stock_code and stock_name:
                        stock_code = stock_name_mapping.get(stock_name, "")
                    
                    # Add button for this stock
                    stock_buttons.append({
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": stock_name},
                        "type": "default",
                        "size": "medium",
                        "value": {
                            "action": "show_stock_actions",
                            "stock_code": stock_code,
                            "stock_name": stock_name,
                            "sector_name": sector['name']
                        }
                    })
                    total_stocks += 1
                
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
                    
                    collapse_elements.append({
                        "tag": "column_set",
                        "flex_mode": "stretch",
                        "columns": columns
                    })
        
        # If no stocks, show empty message
        if not collapse_elements:
            collapse_elements = [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "**暂无持仓股票**"
                    }
                }
            ]
        
        # Build Schema 2.0 card
        card = {
            "schema": "2.0",
            "body": {
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**持仓概览** ({total_stocks}只)"
                        }
                    },
                    {"tag": "hr"},
                    *collapse_elements,
                    {"tag": "hr"},
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"🕐 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n💡 点击操作按钮查看行情、详情、技术分析"
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
                                        "text": {"tag": "plain_text", "content": "添加股票"},
                                        "type": "primary",
                                        "size": "medium",
                                        "value": {"action": "add_stock_to_holdings"}
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
                                        "text": {"tag": "plain_text", "content": "主菜单"},
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
    
    def create_empty_holdings_card(self) -> dict[str, Any]:
        """Create empty holdings card with guidance"""
        card = {
            "schema": "2.0",
            "header": {
                "template": "grey",
                "title": {"tag": "plain_text", "content": "[CHART] 持仓列表为空"}
            },
            "body": {
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": "您可以通过以下方式添加持仓:\n\n• 点击下方按钮「➕ 添加股票」\n• 编辑 `backend/data/自持股票.md` 文件"
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
                                        "text": {"tag": "plain_text", "content": "➕ 添加股票"},
                                        "type": "primary",
                                        "size": "medium",
                                        "value": {"action": "add_stock_to_holdings"}
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
