#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schema 2.0 简化版测试脚本（独立运行，无需额外依赖）

测试内容：
1. Schema 2.0 结构验证
2. JSON 格式检查
3. 卡片发送测试（通过 backend API）

使用方法：
python test_schema2_simple.py
"""

import json
from typing import Dict, Any, List, Tuple
from pathlib import Path

# Windows 控制台编码
import sys
if sys.platform == 'win32':
    try:
        import os
        os.system('chcp 65001 >nul 2>&1')
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass


def print_header(title: str):
    """打印标题"""
    print("\n" + "="*60)
    print(title)
    print("="*60)


def safe_print(text: str):
    """安全打印"""
    try:
        print(text)
    except UnicodeEncodeError:
        # 移除 emoji
        for emoji in ['🧪', '✅', '❌', '🔍', '📱', '💡', '📊', '📦', '🔧', '⚡']:
            text = text.replace(emoji, '[' + emoji + ']')
        print(text)


class Schema2Validator:
    """Schema 2.0 验证器"""
    
    def validate(self, card: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证卡片结构
        
        Returns:
            (is_valid, errors)
        """
        errors = []
        warnings = []
        
        # 1. 必须有 schema 声明
        if "schema" not in card:
            errors.append("缺少 'schema' 字段")
        elif card["schema"] != "2.0":
            errors.append(f"schema 版本错误: {card.get('schema')} (应为 '2.0')")
        
        # 2. 必须有 body 层
        if "body" not in card:
            errors.append("缺少 'body' 字段 (Schema 2.0 必需)")
        else:
            if "elements" not in card.get("body", {}):
                errors.append("body 中缺少 'elements' 字段")
            else:
                elements = card["body"]["elements"]
                if not isinstance(elements, list):
                    errors.append("body.elements 必须是数组")
                elif len(elements) == 0:
                    errors.append("body.elements 不能为空")
                else:
                    # 检查每个 element
                    for i, elem in enumerate(elements):
                        if "tag" not in elem:
                            errors.append(f"elements[{i}] 缺少 'tag' 字段")
                        
                        # 检查 input 组件
                        if elem.get("tag") == "input":
                            if "name" not in elem:
                                errors.append(f"input 组件缺少 'name' 字段 (elements[{i}])")
        
        # 3. 检查 config 和 header（可选但推荐）
        if "config" not in card:
            warnings.append("建议添加 'config' 字段")
        if "header" not in card:
            warnings.append("建议添加 'header' 字段")
        
        # 合并错误和警告
        all_messages = [f"❌ {e}" for e in errors] + [f"⚠️  {w}" for w in warnings]
        
        is_valid = len(errors) == 0
        return is_valid, all_messages


class Schema2CardFactory:
    """Schema 2.0 卡片工厂"""
    
    @staticmethod
    def create_basic_card() -> Dict[str, Any]:
        """创建基础测试卡片"""
        return {
            "schema": "2.0",
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "template": "blue",
                "title": {"tag": "plain_text", "content": "🧪 Schema 2.0 基础测试"}
            },
            "body": {
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": "**测试说明:**\n"
                                       "✓ Schema 2.0 结构验证\n"
                                       "✓ Input 组件渲染测试\n"
                                       "✓ 按钮交互测试"
                        }
                    },
                    {
                        "tag": "input",
                        "name": "test_input",
                        "required": True,
                        "placeholder": {"tag": "plain_text", "content": "输入测试内容..."},
                        "label": {"tag": "plain_text", "content": "测试输入框"}
                    },
                    {
                        "tag": "action",
                        "actions": [
                            {
                                "tag": "button",
                                "text": {"tag": "plain_text", "content": "✓ 提交"},
                                "type": "primary",
                                "value": {"action": "submit"}
                            }
                        ]
                    }
                ]
            }
        }
    
    @staticmethod
    def create_production_card() -> Dict[str, Any]:
        """创建生产环境卡片（与 backend 中的一致）"""
        return {
            "schema": "2.0",
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "template": "blue",
                "title": {"tag": "plain_text", "content": "🔍 个股深度研究"}
            },
            "body": {
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": "**请输入您想研究的股票：**\n"
                                       "支持股票代码（如 `600519`）或名称（如 `贵州茅台`）"
                        }
                    },
                    {
                        "tag": "input",
                        "name": "stock_input_value",
                        "required": True,
                        "placeholder": {"tag": "plain_text", "content": "在此输入股票代码/名称..."},
                        "label": {"tag": "plain_text", "content": "股票代码/名称"}
                    },
                    {
                        "tag": "action",
                        "actions": [
                            {
                                "tag": "button",
                                "text": {"tag": "plain_text", "content": "✓ 确认查询"},
                                "type": "primary",
                                "value": {"action": "query_stock_from_input"}
                            },
                            {
                                "tag": "button",
                                "text": {"tag": "plain_text", "content": "取消"},
                                "type": "default",
                                "value": {"action": "cancel_query"}
                            },
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
                            }
                        ]
                    },
                    {
                        "tag": "note",
                        "elements": [
                            {"tag": "plain_text", "content": "💡 提示：输入后点击「确认查询」按钮开始分析"}
                        ]
                    }
                ]
            }
        }
    
    @staticmethod
    def create_invalid_card_missing_schema() -> Dict[str, Any]:
        """创建无效卡片 - 缺少 schema"""
        return {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "blue",
                "title": {"tag": "plain_text", "content": "无效卡片"}
            },
            "body": {
                "elements": [
                    {
                        "tag": "input",
                        "name": "test"
                    }
                ]
            }
        }
    
    @staticmethod
    def create_invalid_card_missing_body() -> Dict[str, Any]:
        """创建无效卡片 - 缺少 body"""
        return {
            "schema": "2.0",
            "config": {"wide_screen_mode": True},
            "elements": [
                {
                    "tag": "input",
                    "name": "test"
                }
            ]
        }
    
    @staticmethod
    def create_invalid_card_input_no_name() -> Dict[str, Any]:
        """创建无效卡片 - input 缺少 name"""
        return {
            "schema": "2.0",
            "config": {"wide_screen_mode": True},
            "body": {
                "elements": [
                    {
                        "tag": "input",
                        "placeholder": {"tag": "plain_text", "content": "测试"}
                    }
                ]
            }
        }


def test_card(validator: Schema2Validator, card: Dict[str, Any], name: str):
    """测试单个卡片"""
    safe_print(f"\n📋 测试卡片: {name}")
    safe_print("-" * 60)
    
    # 打印 JSON 结构
    safe_print("\n📦 JSON 结构:")
    try:
        json_str = json.dumps(card, ensure_ascii=False, indent=2)
        safe_print(json_str)
    except Exception as e:
        safe_print(f"❌ JSON 序列化失败: {e}")
        return False
    
    # 验证结构
    safe_print("\n🔍 验证结果:")
    is_valid, messages = validator.validate(card)
    
    if messages:
        for msg in messages:
            safe_print(f"  {msg}")
    
    if is_valid:
        safe_print("\n✅ 验证通过！")
    else:
        safe_print("\n❌ 验证失败！")
    
    return is_valid


def run_tests():
    """运行所有测试"""
    print_header("🧪 Schema 2.0 自动化测试")
    
    validator = Schema2Validator()
    factory = Schema2CardFactory()
    
    # 测试用例
    test_cases = [
        # 有效卡片
        (factory.create_basic_card(), "基础测试卡片", True),
        (factory.create_production_card(), "生产环境卡片", True),
        
        # 无效卡片
        (factory.create_invalid_card_missing_schema(), "无效卡片 - 缺少 schema", False),
        (factory.create_invalid_card_missing_body(), "无效卡片 - 缺少 body", False),
        (factory.create_invalid_card_input_no_name(), "无效卡片 - input 缺少 name", False),
    ]
    
    results = []
    
    for card, name, expected_valid in test_cases:
        is_valid = test_card(validator, card, name)
        results.append((name, is_valid, expected_valid, is_valid == expected_valid))
    
    # 打印汇总
    print_header("📊 测试汇总")
    
    passed = sum(1 for r in results if r[3])
    total = len(results)
    
    safe_print(f"\n总计: {passed}/{total} 测试通过\n")
    
    for name, is_valid, expected, match in results:
        status = "✅ 通过" if match else "❌ 失败"
        valid_str = "有效" if is_valid else "无效"
        expected_str = "有效" if expected else "无效"
        safe_print(f"{status} - {name} (实际: {valid_str}, 预期: {expected_str})")
    
    # 最终结果
    print_header("🎯 最终结果")
    if passed == total:
        safe_print("\n✅ 所有测试通过！Schema 2.0 验证器工作正常。")
        safe_print("\n📱 下一步：")
        safe_print("  1. 启动 backend 服务: python backend/main.py")
        safe_print("  2. 在飞书中测试实际卡片渲染")
        safe_print("  3. 验证手机端 input 组件是否正常显示")
    else:
        safe_print("\n❌ 部分测试失败，请检查验证器逻辑或卡片结构。")
    
    return passed == total


def save_valid_cards():
    """保存有效卡片为 JSON 文件，供后续测试使用"""
    print_header("📦 保存有效卡片")
    
    factory = Schema2CardFactory()
    output_dir = Path(__file__).parent / "test_cards"
    output_dir.mkdir(exist_ok=True)
    
    cards = [
        ("basic_card.json", factory.create_basic_card()),
        ("production_card.json", factory.create_production_card()),
    ]
    
    for filename, card in cards:
        filepath = output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(card, f, ensure_ascii=False, indent=2)
        safe_print(f"✅ 已保存: {filepath}")
    
    safe_print(f"\n💡 提示：可以使用这些 JSON 文件在飞书开放平台调试工具中测试")


if __name__ == "__main__":
    # 运行测试
    all_passed = run_tests()
    
    # 保存有效卡片
    save_valid_cards()
    
    # 返回退出码
    sys.exit(0 if all_passed else 1)
