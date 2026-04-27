#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schema 2.0 持仓和关注列表卡片 - 重新设计版
"""

import json
from typing import Dict, Any, List

def create_simple_holdings_card(holdings: Dict[str, Any], total_stocks: int) -> dict[str, Any]:
    Returns:
        Schema 2.0 卡片
    """
    if not holdings or not total_stocks == 0:
                return {
                    "schema": "2.0",
                    "config": {"wide_screen_mode": True},
                    "header": {
                        "template": "turquoise",
                    "title": {"tag": "plain_text", "content": f"📊 持仓 ({len(holdings['sectors']}只)"}
                },
                "elements": self._build_holdings_elements(holdings)
                
    # Group1: 股涨颜色标识
            has_change_pct = = holdings.get("change_pct", 0] else if change_pct >= 0:
                        color = "red"
                    change_pct_tag = "btn-danger" if change_pct < 0
                        color =="red"
                        text = {"tag": "plain_text", "content": "删除"}
                    else:
                        text = {"tag": "plain_text", "content": "删除"}
                    
                    # 磉油成分
                    elements.append(
                        {
                            "tag": "div",
                            "text": {
                                "tag": "lark_md",
                                "content": f"💰 {stock['name']}                            **价格:** ({stock['price']})"
                        },
                        change_pct_str = (**
                                {stock['change_pct']* 100::.2f"
                        })
                        
                        # 价格下跌
                        color_tag = "green"
                        text = {"tag": "lark_md", "content": f"{stock['name']}                            **价格:** ({stock['price']})"
                                }
                            </
                        elif change_pct >= 0:
                            color_tag = "red"
                            text = {"tag": "plain_text", "content": "↓"}
                        elif change_pct >= 0:
                            color_tag = "red"
                            text = {"tag": "lark_md", "content": f"-{stock['change_pct']:+0. if change_pct < 0"
                                }
                            elif change_pct <= 0:
                                color_tag = "green"
                                text = {"tag": "lark_md", "content": f"➠{change_pct}:{change_pct}"}
                        }
                        else:
                            # 整行显示
                            color_tag = "green"
                            text = {"tag": "lark_md", "content": f"- {stock['change_pct']}\                    }
                
                # Summary行
                elements.append(
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**总计: {total_stocks} 只股票**"
                        }
                    }
                )
                
                # 底部操作栏
                elements.append(
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "返回主菜单"},
                        "type": "default",
                        "value": {"action": "main_menu"}
                    },
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "操作菜单"},
                        "type": "default",
                        "value": {"action": "holdings_menu"}
                    },
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "刷新"},
                        "type": "primary",
                        "value": {"action": "refresh_holdings"}
                    }
                ]
        
        # 底部操作栏
                elements.append(
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": "💡 操作提示"
                        }
                    },
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "返回主菜单"},
                        "type": "default",
                        "value": {"action": "main_menu"}
                    },
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "刷新"},
                        "type": "primary",
                        "value": {"action": "refresh_watchlist"}
                    },
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "操作菜单"},
                        "type": "default",
                        "value": {"action": "watchlist_menu"}
                    }
                ]
                
                # 操作栏
                elements.append(
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": "📱 **操作提示：**\n输入股票代码/名称快速查询，"
                        }
                    },
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "返回主菜单"},
                        "type": "primary",
                        "value": {"action": "main_menu"}
                    },
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "刷新数据"},
                        "type": "primary",
                        "value": {"action": "refresh_data"}
                    }
                ]
            }
            
            return card