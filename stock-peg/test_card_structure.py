#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试股票查询卡片结构"""

import json
import sys
from pathlib import Path

# 添加 backend 到路径
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from services.feishu_card_service import FeishuCardService

# 创建服务实例（不传入 bot_service）
card_service = FeishuCardService(None)

# 创建卡片
card = card_service._create_stock_query_card()

# 打印卡片结构
print("="*60)
print("股票查询卡片结构 (Schema 2.0):")
print("="*60)
print(json.dumps(card, ensure_ascii=False, indent=2))

# 应用 _ensure_flat_action_values
print("\n" + "="*60)
print("应用 _ensure_flat_action_values:")
print("="*60)
card = card_service._ensure_flat_action_values(card)
print(json.dumps(card, ensure_ascii=False, indent=2))

# 应用 _ensure_button_names
print("\n" + "="*60)
print("应用 _ensure_button_names:")
print("="*60)
card = card_service._ensure_button_names(card)
print(json.dumps(card, ensure_ascii=False, indent=2))

# 验证 Schema 2.0
print("\n" + "="*60)
print("验证 Schema 2.0 结构:")
print("="*60)
has_schema = "schema" in card
has_body = "body" in card
has_elements = "body" in card and "elements" in card.get("body", {})

print(f"✓ 有 schema 声明: {has_schema} (值: {card.get('schema')})")
print(f"✓ 有 body 层: {has_body}")
print(f"✓ 有 body.elements: {has_elements}")

if has_elements:
    elements = card["body"]["elements"]
    print(f"✓ elements 数量: {len(elements)}")

    # 检查 input 组件
    has_input = any(elem.get("tag") == "input" for elem in elements)
    print(f"✓ 包含 input 组件: {has_input}")

    if has_input:
        input_elem = next(elem for elem in elements if elem.get("tag") == "input")
        print(f"✓ input name: {input_elem.get('name')}")
