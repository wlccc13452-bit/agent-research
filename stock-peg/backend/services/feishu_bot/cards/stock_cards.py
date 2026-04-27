"""
Stock Card Builder - 股票卡片构建器

Contains card builders for stock query and analysis.
Business data passed via parameters, no direct service dependencies.

Refactored to include all stock-related card creation methods:
- Stock query card
- Quote result card
- Technical analysis card
- Fundamental analysis card
- Loading card
- Research start card
"""

from typing import Any, Optional, override
from datetime import datetime
from services.feishu_bot.cards.feishu_bot_card_base import BaseCardBuilder


class StockCardBuilder(BaseCardBuilder):
    """
    Builder for stock-related cards.
    Business data passed via build() parameters.
    """
    
    @override
    def build(
        self,
        card_type: str = "query",
        **kwargs
    ) -> dict[str, Any]:
        """
        Build stock card based on type.
        
        Args:
            card_type: Type of card ("query", "quote", "technical", "fundamental", "loading", "research_start")
            **kwargs: Additional parameters for specific card types
            
        Returns:
            dict[str, Any]: Stock card JSON structure
        """
        if card_type == "query":
            return self.create_stock_query_card(
                holdings_stocks=kwargs.get("holdings_stocks"),
                watchlist_stocks=kwargs.get("watchlist_stocks")
            )
        elif card_type == "quote":
            return self.create_quote_result_card(
                stock_code=kwargs.get("stock_code", ""),
                quote=kwargs.get("quote", {})
            )
        elif card_type == "technical":
            return self.create_technical_result_card(
                stock_code=kwargs.get("stock_code", ""),
                indicators=kwargs.get("indicators", {})
            )
        elif card_type == "fundamental":
            return self.create_fundamental_result_card(
                stock_code=kwargs.get("stock_code", ""),
                fundamentals=kwargs.get("fundamentals", {})
            )
        elif card_type == "loading":
            return self.create_loading_card(
                stock_code=kwargs.get("stock_code", ""),
                analysis_type=kwargs.get("analysis_type", "query")
            )
        elif card_type == "research_start":
            return self.create_stock_research_start_card()
        elif card_type == "comprehensive":
            return self.create_comprehensive_analysis_card(
                stock_code=kwargs.get("stock_code", ""),
                stock_name=kwargs.get("stock_name", ""),
                quote=kwargs.get("quote", {}),
                indicators=kwargs.get("indicators", {}),
                fundamentals=kwargs.get("fundamentals", {}),
                is_holdings=kwargs.get("is_holdings", False),
                sector_name=kwargs.get("sector_name", ""),
                watch_date=kwargs.get("watch_date", "")
            )
        else:
            return self.create_stock_query_card()
    
    def create_stock_query_card(
        self,
        holdings_stocks: list[dict] = None,
        watchlist_stocks: list[dict] = None
    ) -> dict[str, Any]:
        """Create stock query card with select dropdown (Schema 2.0)"""
        
        # Build dropdown options
        options = []
        
        # Add holdings stocks
        if holdings_stocks:
            options.append({
                "text": {"tag": "plain_text", "content": "── 持仓股票 ──"},
                "value": "divider_holdings"
            })
            for stock in holdings_stocks[:10]:
                stock_name = stock.get('name', '')
                stock_code = stock.get('code', '')
                options.append({
                    "text": {"tag": "plain_text", "content": f"{stock_name} ({stock_code})"},
                    "value": f"{stock_code}|{stock_name}"
                })
        
        # Add watchlist stocks
        if watchlist_stocks:
            options.append({
                "text": {"tag": "plain_text", "content": "── 热点关注 ──"},
                "value": "divider_watchlist"
            })
            for stock in watchlist_stocks[:10]:
                stock_name = stock.get('name', '')
                stock_code = stock.get('code', '')
                options.append({
                    "text": {"tag": "plain_text", "content": f"{stock_name} ({stock_code})"},
                    "value": f"{stock_code}|{stock_name}"
                })
        
        # Add empty placeholder if no stocks
        if not options:
            options.append({
                "text": {"tag": "plain_text", "content": "暂无可选股票"},
                "value": "empty"
            })
        
        # Build Schema 2.0 card structure
        card = {
            "schema": "2.0",
            "header": {
                "template": "blue",
                "title": {"tag": "plain_text", "content": "个股深度研究"}
            },
            "body": {
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": "**请选择您想研究的股票：**\n\n下拉列表包含您的持仓股票和热点关注股票"
                        }
                    },
                    {
                        "tag": "form",
                        "name": "stock_select_form",
                        "elements": [
                            {
                                "tag": "select_static",
                                "name": "selected_stock",
                                "placeholder": {"tag": "plain_text", "content": "点击选择股票..."},
                                "options": options
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
                                            "text": {"tag": "plain_text", "content": "确认查询"},
                                            "type": "primary",
                                            "name": "btn_query_stock_from_select",
                                            "action_type": "form_submit",
                                            "value": {"action": "query_stock_from_select"}
                                        }]
                                    },
                                    {
                                        "tag": "column",
                                        "width": "weighted",
                                        "weight": 1,
                                        "elements": [{
                                            "tag": "button",
                                            "text": {"tag": "plain_text", "content": "取消"},
                                            "type": "default",
                                            "name": "btn_cancel_query",
                                            "value": {"action": "cancel_query"}
                                        }]
                                    }
                                ]
                            }
                        ]
                    },
                    {"tag": "hr"},
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "查看详细网页版"},
                        "type": "default",
                        "multi_url": {
                            "url": "http://172.16.105.145:5173/feishu",
                            "android_url": "http://172.16.105.145:5173/feishu",
                            "ios_url": "http://172.16.105.145:5173/feishu",
                            "pc_url": "http://172.16.105.145:5173/feishu"
                        }
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": "提示：选择股票后点击「确认查询」按钮开始分析"
                        }
                    }
                ]
            }
        }
        
        return card
    
    def create_quote_result_card(self, stock_code: str, quote: dict[str, Any]) -> dict[str, Any]:
        """Create real-time quote result card with target price info"""
        if "error" in quote:
            return self._create_error_card(quote["error"])
        
        # Determine trend emoji
        change_pct = quote.get("change_pct", 0) or 0
        if change_pct > 0:
            trend_emoji = "📈"
            status_emoji = "🔴"
        elif change_pct < 0:
            trend_emoji = "📉"
            status_emoji = "🟢"
        else:
            trend_emoji = "➡️"
            status_emoji = "⚪"
        
        # Safely get values with default 0
        price = quote.get("price", 0) or 0
        volume = quote.get("volume", 0) or 0
        amount = quote.get("amount", 0) or 0
        open_price = quote.get("open", 0) or 0
        high_price = quote.get("high", 0) or 0
        low_price = quote.get("low", 0) or 0
        prev_close = quote.get("prev_close", 0) or 0
        
        # Build elements list
        elements = [
            # Header with basic quote info
            {
                "tag": "column_set",
                "columns": [
                    {
                        "tag": "column",
                        "width": "weighted",
                        "weight": 1,
                        "elements": [
                            {
                                "tag": "div",
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**最新价**\n💰 {price:.2f}"
                                }
                            }
                        ]
                    },
                    {
                        "tag": "column",
                        "width": "weighted",
                        "weight": 1,
                        "elements": [
                            {
                                "tag": "div",
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**涨跌幅**\n{trend_emoji} {change_pct:+.2f}%"
                                }
                            }
                        ]
                    }
                ]
            },
            {
                "tag": "column_set",
                "columns": [
                    {
                        "tag": "column",
                        "width": "weighted",
                        "weight": 1,
                        "elements": [
                            {
                                "tag": "div",
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**成交量**\n📦 {volume:,.0f}"
                                }
                            }
                        ]
                    },
                    {
                        "tag": "column",
                        "width": "weighted",
                        "weight": 1,
                        "elements": [
                            {
                                "tag": "div",
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**成交额**\n💵 {amount:,.2f}"
                                }
                            }
                        ]
                    }
                ]
            },
            {"tag": "hr"},
            {
                "tag": "column_set",
                "columns": [
                    {
                        "tag": "column",
                        "width": "weighted",
                        "weight": 1,
                        "elements": [
                            {
                                "tag": "div",
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**今开**\n{open_price:.2f}"
                                }
                            }
                        ]
                    },
                    {
                        "tag": "column",
                        "width": "weighted",
                        "weight": 1,
                        "elements": [
                            {
                                "tag": "div",
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**昨收**\n{prev_close:.2f}"
                                }
                            }
                        ]
                    }
                ]
            },
            {
                "tag": "column_set",
                "columns": [
                    {
                        "tag": "column",
                        "width": "weighted",
                        "weight": 1,
                        "elements": [
                            {
                                "tag": "div",
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**最高**\n{high_price:.2f}"
                                }
                            }
                        ]
                    },
                    {
                        "tag": "column",
                        "width": "weighted",
                        "weight": 1,
                        "elements": [
                            {
                                "tag": "div",
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**最低**\n{low_price:.2f}"
                                }
                            }
                        ]
                    }
                ]
            }
        ]
        
        # Add target price info if available
        target_price_data = quote.get("target_price_data")
        if target_price_data and target_price_data.get("target_price"):
            target_price = target_price_data["target_price"]
            change_up_pct = target_price_data.get("change_up_pct") or 0
            change_down_pct = target_price_data.get("change_down_pct") or 0
            stop_loss_price = target_price_data.get("stop_loss_price")
            notes = target_price_data.get("notes", "")
            
            # Calculate control range
            upper = target_price * (1 + change_up_pct / 100)
            lower = target_price * (1 - change_down_pct / 100)
            
            # Calculate change percentage relative to target price
            change_to_target = ((price - target_price) / target_price) * 100 if target_price > 0 else 0
            
            # Determine price status
            price_status = "in_range"
            if price > upper:
                price_status = "above_upper"
            elif price < lower:
                price_status = "below_lower"
            
            # Build status text and color
            if price_status == "above_upper":
                status_text = "⚠️ 超出上限"
                status_color = "🔴"
            elif price_status == "below_lower":
                status_text = "⚠️ 跌破下限"
                status_color = "🟢"
            else:
                status_text = "✓ 正常"
                status_color = "🔵"
            
            # Add separator
            elements.append({"tag": "hr"})
            
            # Add target price section
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"🎯 **基准价信息**"
                }
            })
            
            # Target price and control range
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**基准价**: {target_price:.2f}  |  **控制区间**: {lower:.2f} ~ {upper:.2f}"
                }
            })
            
            # Change percentage and control percentages
            change_to_target_text = f"{change_to_target:+.2f}%" if change_to_target != 0 else "0.00%"
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**涨跌比例**: {change_to_target_text}  |  **控制比例**: +{change_up_pct:.1f}% / -{change_down_pct:.1f}%"
                }
            })
            
            # Current status
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**当前状态**: {status_color} {status_text}"
                }
            })
            
            # Stop loss price (if set)
            if stop_loss_price:
                elements.append({
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**硬止损**: {stop_loss_price:.2f}"
                    }
                })
            
            # Notes (if available)
            if notes:
                elements.append({
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"📝 **备注**: {notes}"
                    }
                })
        
        # Add timestamp
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"🕐 更新时间: {quote.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}"
            }
        })
        
        card = {
            "schema": "2.0",
            "header": {
                "template": "blue",
                "title": {
                    "tag": "plain_text",
                    "content": f"{status_emoji} {quote.get('stock_name', stock_code)} ({stock_code})"
                }
            },
            "body": {
                "elements": elements
            }
        }
        return card
    
    def create_technical_result_card(self, stock_code: str, indicators: dict[str, Any]) -> dict[str, Any]:
        """Create technical indicators result card"""
        if "error" in indicators:
            return self._create_error_card(indicators["error"])
        
        # Build technical indicator content
        ma_data = indicators.get("ma", {})
        macd_data = indicators.get("macd", {})
        rsi_data = indicators.get("rsi", {})
        kdj_data = indicators.get("kdj", {})
        
        card = {
            "schema": "2.0",
            "header": {
                "template": "purple",
                "title": {
                    "tag": "plain_text",
                    "content": f"[CHART] {indicators.get('stock_name', stock_code)} ({stock_code}) - 技术指标分析"
                }
            },
            "body": {
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**均线系统 (MA)**\nMA5: {ma_data.get('ma5', 0):.2f} | MA10: {ma_data.get('ma10', 0):.2f} | MA20: {ma_data.get('ma20', 0):.2f} | MA60: {ma_data.get('ma60', 0):.2f}"
                        }
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**MACD指标**\nDIF: {macd_data.get('dif', 0):.4f} | DEA: {macd_data.get('dea', 0):.4f} | MACD: {macd_data.get('macd', 0):.4f}"
                        }
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**RSI指标**\nRSI(14): {rsi_data.get('rsi_14', 0):.2f}"
                        }
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**KDJ指标**\nK: {kdj_data.get('k', 0):.2f} | D: {kdj_data.get('d', 0):.2f} | J: {kdj_data.get('j', 0):.2f}"
                        }
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"🕐 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        }
                    }
                ]
            }
        }
        return card
    
    def create_fundamental_result_card(self, stock_code: str, fundamentals: dict[str, Any]) -> dict[str, Any]:
        """Create fundamental analysis result card"""
        if "error" in fundamentals:
            return self._create_error_card(fundamentals["error"])
        
        # Safely get values with default 0
        pe_ttm = fundamentals.get('pe_ttm', 0) or 0
        pb = fundamentals.get('pb', 0) or 0
        ps = fundamentals.get('ps', 0) or 0
        peg = fundamentals.get('peg', 0) or 0
        roe = fundamentals.get('roe', 0) or 0
        roa = fundamentals.get('roa', 0) or 0
        market_cap = fundamentals.get('market_cap', 0) or 0
        score = fundamentals.get('score', 0) or 0
        
        card = {
            "schema": "2.0",
            "header": {
                "template": "green",
                "title": {
                    "tag": "plain_text",
                    "content": f"💰 {fundamentals.get('stock_name', stock_code)} ({stock_code}) - 基本面分析"
                }
            },
            "body": {
                "elements": [
                {
                    "tag": "column_set",
                    "columns": [
                        {
                            "tag": "column",
                            "width": "weighted",
                            "weight": 1,
                            "elements": [
                                {
                                    "tag": "div",
                                    "text": {
                                        "tag": "lark_md",
                                        "content": f"**PE(TTM)**\n{pe_ttm:.2f}"
                                    }
                                }
                            ]
                        },
                        {
                            "tag": "column",
                            "width": "weighted",
                            "weight": 1,
                            "elements": [
                                {
                                    "tag": "div",
                                    "text": {
                                        "tag": "lark_md",
                                        "content": f"**PB**\n{pb:.2f}"
                                    }
                                }
                            ]
                        }
                    ]
                },
                {
                    "tag": "column_set",
                    "columns": [
                        {
                            "tag": "column",
                            "width": "weighted",
                            "weight": 1,
                            "elements": [
                                {
                                    "tag": "div",
                                    "text": {
                                        "tag": "lark_md",
                                        "content": f"**PS**\n{ps:.2f}"
                                    }
                                }
                            ]
                        },
                        {
                            "tag": "column",
                            "width": "weighted",
                            "weight": 1,
                            "elements": [
                                {
                                    "tag": "div",
                                    "text": {
                                        "tag": "lark_md",
                                        "content": f"**PEG**\n{peg:.2f}"
                                    }
                                }
                            ]
                        }
                    ]
                },
                {
                    "tag": "column_set",
                    "columns": [
                        {
                            "tag": "column",
                            "width": "weighted",
                            "weight": 1,
                            "elements": [
                                {
                                    "tag": "div",
                                    "text": {
                                        "tag": "lark_md",
                                        "content": f"**ROE**\n{roe:.2f}%"
                                    }
                                }
                            ]
                        },
                        {
                            "tag": "column",
                            "width": "weighted",
                            "weight": 1,
                            "elements": [
                                {
                                    "tag": "div",
                                    "text": {
                                        "tag": "lark_md",
                                        "content": f"**ROA**\n{roa:.2f}%"
                                    }
                                }
                            ]
                        }
                    ]
                },
                {
                    "tag": "column_set",
                    "columns": [
                        {
                            "tag": "column",
                            "width": "weighted",
                            "weight": 1,
                            "elements": [
                                {
                                    "tag": "div",
                                    "text": {
                                        "tag": "lark_md",
                                        "content": f"**市值**\n{market_cap:.2f}亿"
                                    }
                                }
                            ]
                        },
                        {
                            "tag": "column",
                            "width": "weighted",
                            "weight": 1,
                            "elements": [
                                {
                                    "tag": "div",
                                    "text": {
                                        "tag": "lark_md",
                                        "content": f"**评分**\n{score}/100"
                                    }
                                }
                            ]
                        }
                    ]
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"🕐 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                }
            ]
        }
        }
        return card
    
    def create_loading_card(self, stock_code: str, analysis_type: str = "query") -> dict[str, Any]:
        """
        Create minimal loading card with title only.
        
        Args:
            stock_code: Stock code being analyzed
            analysis_type: Type of analysis (for title only)
            
        Returns:
            Minimal loading card with only header
        """
        type_names = {
            "query": "行情查询",
            "query_stock": "行情查询",
            "technical_analysis": "技术分析",
            "fundamental_analysis": "基本面分析",
            "comprehensive_analysis": "综合分析"
        }
        analysis_name = type_names.get(analysis_type, "分析")
        
        # 标题中包含股票代号
        title = f"⏳ {analysis_name}中... ({stock_code})" if stock_code else f"⏳ {analysis_name}中..."
        
        return {
            "schema": "2.0",
            "header": {
                "template": "blue",
                "title": {
                    "tag": "plain_text",
                    "content": title
                }
            }
        }
    
    def create_stock_research_start_card(self) -> dict[str, Any]:
        """Create the navigation hub card for mobile menu"""
        from config.constants import BOT_NAME, BOT_VERSION
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        card = {
            "schema": "2.0",
            "header": {
                "template": "blue",
                "title": {"tag": "plain_text", "content": f"[START] {BOT_NAME} 投研中心"}
            },
            "body": {
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**欢迎使用 PegBot 移动端助手**\n📅 {now}\n请选择您需要执行的操作："
                        }
                    },
                    {"tag": "hr"},
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": "🔍 **快速查询**"
                        }
                    },
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
                                        "text": {"tag": "plain_text", "content": "个股研究"},
                                        "type": "primary",
                                        "size": "medium",
                                        "value": {"action": "stock_query_menu"}
                                    }
                                ]
                            }
                        ]
                    },
                    {"tag": "hr"},
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": "[CHART] **查看列表**"
                        }
                    },
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
                                        "text": {"tag": "plain_text", "content": "查看持仓"},
                                        "type": "primary",
                                        "size": "medium",
                                        "value": {"action": "view_holdings"}
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
                                        "text": {"tag": "plain_text", "content": "查看关注"},
                                        "type": "default",
                                        "size": "medium",
                                        "value": {"action": "view_watchlist"}
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
    
    def create_comprehensive_analysis_card(
        self,
        stock_code: str,
        stock_name: str,
        quote: dict[str, Any],
        indicators: dict[str, Any],
        fundamentals: dict[str, Any],
        is_holdings: bool = False,
        sector_name: str = "",
        watch_date: str = ""
    ) -> dict[str, Any]:
        """
        Create comprehensive analysis card with all three analysis results.
        
        Combines:
        - Real-time quote
        - Technical indicators
        - Fundamental analysis
        
        Args:
            stock_code: Stock code
            stock_name: Stock name
            quote: Quote data dict
            indicators: Technical indicators dict
            fundamentals: Fundamental analysis dict
            is_holdings: Whether from holdings (vs watchlist)
            sector_name: Sector name (for holdings)
            watch_date: Watch date (for watchlist)
            
        Returns:
            Comprehensive analysis card
        """
        elements = []
        
        # ===== Section 1: Real-time Quote =====
        if "error" not in quote:
            change_pct = quote.get("change_pct", 0) or 0
            if change_pct > 0:
                trend_emoji = "📈"
                status_emoji = "🔴"
            elif change_pct < 0:
                trend_emoji = "📉"
                status_emoji = "🟢"
            else:
                trend_emoji = "➡️"
                status_emoji = "⚪"
            
            price = quote.get("price", 0) or 0
            volume = quote.get("volume", 0) or 0
            amount = quote.get("amount", 0) or 0
            
            elements.extend([
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "📊 **实时行情**"
                    }
                },
                {
                    "tag": "column_set",
                    "columns": [
                        {
                            "tag": "column",
                            "width": "weighted",
                            "weight": 1,
                            "elements": [{
                                "tag": "div",
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**最新价**\n💰 {price:.2f}"
                                }
                            }]
                        },
                        {
                            "tag": "column",
                            "width": "weighted",
                            "weight": 1,
                            "elements": [{
                                "tag": "div",
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**涨跌幅**\n{trend_emoji} {change_pct:+.2f}%"
                                }
                            }]
                        }
                    ]
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**成交量**: {volume:,.0f} | **成交额**: {amount:,.2f}"
                    }
                },
                {"tag": "hr"}
            ])
        else:
            elements.extend([
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"⚠️ **行情数据**: {quote.get('error', '获取失败')}"
                    }
                },
                {"tag": "hr"}
            ])
        
        # ===== Section 2: Technical Indicators =====
        if "error" not in indicators:
            ma_data = indicators.get("ma", {})
            macd_data = indicators.get("macd", {})
            rsi_data = indicators.get("rsi", {})
            kdj_data = indicators.get("kdj", {})
            
            elements.extend([
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "📈 **技术指标**"
                    }
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**均线**: MA5 {ma_data.get('ma5', 0):.2f} | MA10 {ma_data.get('ma10', 0):.2f} | MA20 {ma_data.get('ma20', 0):.2f}"
                    }
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**MACD**: DIF {macd_data.get('dif', 0):.4f} | DEA {macd_data.get('dea', 0):.4f}"
                    }
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**RSI(14)**: {rsi_data.get('rsi_14', 0):.2f} | **KDJ**: K {kdj_data.get('k', 0):.2f} D {kdj_data.get('d', 0):.2f} J {kdj_data.get('j', 0):.2f}"
                    }
                },
                {"tag": "hr"}
            ])
        else:
            elements.extend([
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"⚠️ **技术分析**: {indicators.get('error', '获取失败')}"
                    }
                },
                {"tag": "hr"}
            ])
        
        # ===== Section 3: Fundamental Analysis =====
        if "error" not in fundamentals:
            pe_ttm = fundamentals.get('pe_ttm', 0) or 0
            pb = fundamentals.get('pb', 0) or 0
            peg = fundamentals.get('peg', 0) or 0
            roe = fundamentals.get('roe', 0) or 0
            score = fundamentals.get('score', 0) or 0
            
            elements.extend([
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "💰 **基本面分析**"
                    }
                },
                {
                    "tag": "column_set",
                    "columns": [
                        {
                            "tag": "column",
                            "width": "weighted",
                            "weight": 1,
                            "elements": [{
                                "tag": "div",
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**PE(TTM)**\n{pe_ttm:.2f}"
                                }
                            }]
                        },
                        {
                            "tag": "column",
                            "width": "weighted",
                            "weight": 1,
                            "elements": [{
                                "tag": "div",
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**PB**\n{pb:.2f}"
                                }
                            }]
                        },
                        {
                            "tag": "column",
                            "width": "weighted",
                            "weight": 1,
                            "elements": [{
                                "tag": "div",
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**PEG**\n{peg:.2f}"
                                }
                            }]
                        }
                    ]
                },
                {
                    "tag": "column_set",
                    "columns": [
                        {
                            "tag": "column",
                            "width": "weighted",
                            "weight": 1,
                            "elements": [{
                                "tag": "div",
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**ROE**\n{roe:.2f}%"
                                }
                            }]
                        },
                        {
                            "tag": "column",
                            "width": "weighted",
                            "weight": 1,
                            "elements": [{
                                "tag": "div",
                                "text": {
                                    "tag": "lark_md",
                                    "content": f"**综合评分**\n{score}/100"
                                }
                            }]
                        }
                    ]
                },
                {"tag": "hr"}
            ])
        else:
            elements.extend([
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"⚠️ **基本面分析**: {fundamentals.get('error', '获取失败')}"
                    }
                },
                {"tag": "hr"}
            ])
        
        # ===== Action Buttons =====
        delete_action = "delete_stock_from_holdings" if is_holdings else "delete_stock_from_watchlist"
        back_action = "view_holdings" if is_holdings else "view_watchlist"
        delete_text = "删除持仓" if is_holdings else "删除关注"
        
        action_buttons = [
            {
                "tag": "button",
                "text": {"tag": "plain_text", "content": "返回列表"},
                "type": "default",
                "size": "medium",
                "value": {"action": back_action}
            },
            {
                "tag": "button",
                "text": {"tag": "plain_text", "content": delete_text},
                "type": "danger",
                "size": "medium",
                "value": {
                    "action": delete_action,
                    "stock_code": stock_code,
                    "stock_name": stock_name
                }
            }
        ]
        
        elements.append(self._create_button_row(action_buttons))
        
        # ===== Timestamp =====
        elements.append({
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": f"🕐 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
        })
        
        card = {
            "schema": "2.0",
            "header": {
                "template": "blue",
                "title": {
                    "tag": "plain_text",
                    "content": f"📊 {stock_name} ({stock_code}) - 综合分析"
                }
            },
            "body": {
                "elements": elements
            }
        }
        
        return card

