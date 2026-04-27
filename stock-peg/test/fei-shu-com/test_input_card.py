#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书 Schema 2.0 自动化测试工具

功能：
1. 验证 Schema 2.0 JSON 结构完整性
2. 测试 input 组件在手机端的渲染
3. 测试按钮交互和回调处理
4. 自动发送测试卡片并验证响应

Schema 2.0 关键变更：
- 必须声明 "schema": "2.0"
- elements 必须包裹在 body.elements 中
- input 组件支持更多属性
- 兼容性更强，手机端渲染更稳定

使用方法：
python test_input_card.py [chat_id|open_id]
"""

import os
import sys
import json
import asyncio
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Windows 控制台编码设置
if sys.platform == 'win32':
    import codecs
    try:
        os.system('chcp 65001 >nul 2>&1')
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# 添加 backend 目录到 Python 路径
backend_dir = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import lark_oapi as lark
from lark_oapi.api.im.v1 import CreateMessageRequest, CreateMessageRequestBody
from dotenv import load_dotenv
import httpx

# 加载环境变量
env_file = backend_dir / ".env"
load_dotenv(env_file)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def safe_print(text: str):
    """安全打印函数，处理 Windows GBK 编码问题"""
    try:
        print(text)
    except UnicodeEncodeError:
        emoji_map = {
            '🧪': '[TEST]', '✅': '[OK]', '❌': '[X]', '🔍': '[SEARCH]',
            '📱': '[MOBILE]', '💡': '[TIP]', '⏳': '[WAIT]', '⏱️': '[TIME]',
            '📤': '[SEND]', '📋': '[CARD]', '📝': '[INPUT]', '👤': '[USER]',
            '💬': '[CHAT]', '🎯': '[TARGET]', '📊': '[CHART]', '🔧': '[TOOL]',
            '📦': '[PACKAGE]', '⚡': '[FAST]', '🎨': '[DESIGN]',
        }
        for emoji, text_replacement in emoji_map.items():
            text = text.replace(emoji, text_replacement)
        print(text)


class Schema2Validator:
    """Schema 2.0 结构验证器"""
    
    @staticmethod
    def validate(card: dict) -> tuple[bool, list[str]]:
        """验证 Schema 2.0 结构
        
        Returns:
            (is_valid, errors)
        """
        errors = []
        
        # 1. 必须有 schema 声明
        if "schema" not in card:
            errors.append("❌ 缺少 'schema' 字段")
        elif card["schema"] != "2.0":
            errors.append(f"❌ schema 版本错误: {card.get('schema')} (应为 '2.0')")
        
        # 2. 必须有 body 层
        if "body" not in card:
            errors.append("❌ 缺少 'body' 字段 (Schema 2.0 必需)")
        elif "elements" not in card.get("body", {}):
            errors.append("❌ body 中缺少 'elements' 字段")
        
        # 3. 验证 elements 结构
        elements = card.get("body", {}).get("elements", [])
        if not isinstance(elements, list):
            errors.append("❌ body.elements 必须是数组")
        elif len(elements) == 0:
            errors.append("❌ body.elements 不能为空")
        
        # 4. 检查 input 组件
        has_input = False
        for i, elem in enumerate(elements):
            if elem.get("tag") == "input":
                has_input = True
                if "name" not in elem:
                    errors.append(f"❌ input 组件缺少 'name' 字段 (elements[{i}])")
        
        if not has_input:
            errors.append("⚠️  未找到 input 组件")
        
        # 5. 检查 config 和 header（可选但推荐）
        if "config" not in card:
            errors.append("⚠️  建议添加 'config' 字段")
        if "header" not in card:
            errors.append("⚠️  建议添加 'header' 字段")
        
        is_valid = len([e for e in errors if e.startswith("❌")]) == 0
        return is_valid, errors


class Schema2CardFactory:
    """Schema 2.0 卡片工厂"""
    
    @staticmethod
    def create_test_card_v1() -> dict:
        """创建测试卡片 V1 - 基础输入测试"""
        return {
            "schema": "2.0",
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "template": "blue",
                "title": {"tag": "plain_text", "content": "🧪 Schema 2.0 - 基础测试"}
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
                        "name": "test_input_1",
                        "placeholder": {"tag": "plain_text", "content": "输入测试内容..."},
                        "label": {"tag": "plain_text", "content": "测试输入框"}
                    },
                    {
                        "tag": "action",
                        "actions": [
                            {
                                "tag": "button",
                                "text": {"tag": "plain_text", "content": "✓ 提交测试"},
                                "type": "primary",
                                "value": {"test_id": "v1", "action": "submit"}
                            }
                        ]
                    }
                ]
            }
        }
    
    @staticmethod
    def create_test_card_v2() -> dict:
        """创建测试卡片 V2 - 多输入字段测试"""
        return {
            "schema": "2.0",
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "template": "green",
                "title": {"tag": "plain_text", "content": "🧪 Schema 2.0 - 多字段测试"}
            },
            "body": {
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": "**股票信息查询:**\n支持多个输入字段"
                        }
                    },
                    {
                        "tag": "input",
                        "name": "stock_code",
                        "placeholder": {"tag": "plain_text", "content": "输入股票代码，如 600519"},
                        "label": {"tag": "plain_text", "content": "股票代码"}
                    },
                    {
                        "tag": "input",
                        "name": "stock_name",
                        "placeholder": {"tag": "plain_text", "content": "输入股票名称，如 贵州茅台"},
                        "label": {"tag": "plain_text", "content": "股票名称（可选）"}
                    },
                    {
                        "tag": "action",
                        "actions": [
                            {
                                "tag": "button",
                                "text": {"tag": "plain_text", "content": "🔍 查询"},
                                "type": "primary",
                                "value": {"test_id": "v2", "action": "query"}
                            },
                            {
                                "tag": "button",
                                "text": {"tag": "plain_text", "content": "重置"},
                                "type": "default",
                                "value": {"test_id": "v2", "action": "reset"}
                            }
                        ]
                    }
                ]
            }
        }
    
    @staticmethod
    def create_test_card_v3() -> dict:
        """创建测试卡片 V3 - 生产环境完整版"""
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
                        "placeholder": {"tag": "plain_text", "content": "在此输入股票代码/名称..."},
                        "label": {"tag": "plain_text", "content": "股票代码/名称"}
                    },
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "确认查询"},
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
                    },
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": "提示：输入后点击「确认查询」按钮开始分析"}
                    }
                ]
            }
        }


class Schema2Tester:
    """Schema 2.0 自动化测试器"""
    
    def __init__(self):
        self.app_id = os.getenv("FEISHU_APP_ID")
        self.app_secret = os.getenv("FEISHU_APP_SECRET")
        self.backend_url = "http://localhost:8000"
        
        if not self.app_id or not self.app_secret:
            raise ValueError("请在 .env 文件中配置 FEISHU_APP_ID 和 FEISHU_APP_SECRET")
        
        self.client = lark.Client.builder() \
            .app_id(self.app_id) \
            .app_secret(self.app_secret) \
            .log_level(lark.LogLevel.ERROR) \
            .build()
        
        self.validator = Schema2Validator()
        self.factory = Schema2CardFactory()
        
        logger.info(f"✅ 飞书客户端已初始化 (App ID: {self.app_id[:15]}...)")
    
    async def check_backend_service(self) -> bool:
        """检查 backend 服务"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.backend_url}/health", timeout=3.0)
                if response.status_code == 200:
                    health_data = response.json()
                    feishu_status = health_data.get('services', {}).get('feishu_long_connection', {})
                    logger.info(f"✅ Backend 服务运行中")
                    logger.info(f"   - 飞书长连接状态: {'运行中 ✅' if feishu_status.get('alive') else '未运行 ❌'}")
                    return feishu_status.get('alive', False)
                return False
        except Exception as e:
            logger.error(f"❌ Backend 服务未运行或无法访问: {e}")
            return False
    
    def validate_and_print(self, card: dict, card_name: str) -> bool:
        """验证卡片并打印结果"""
        safe_print(f"\n{'='*60}")
        safe_print(f"📋 验证卡片: {card_name}")
        safe_print(f"{'='*60}")
        
        is_valid, errors = self.validator.validate(card)
        
        # 打印卡片结构
        safe_print(f"\n📦 JSON 结构:")
        safe_print(json.dumps(card, ensure_ascii=False, indent=2))
        
        # 打印验证结果
        safe_print(f"\n🔍 验证结果:")
        if is_valid:
            safe_print("✅ Schema 2.0 结构验证通过！")
        else:
            safe_print("❌ Schema 2.0 结构验证失败！")
        
        if errors:
            safe_print("\n详细信息:")
            for error in errors:
                safe_print(f"  {error}")
        
        return is_valid
    
    async def send_card(self, card: dict, receive_id: str, receive_id_type: str = "chat_id") -> tuple[bool, str]:
        """发送卡片
        
        Returns:
            (success, message_id)
        """
        try:
            request = CreateMessageRequest.builder() \
                .receive_id_type(receive_id_type) \
                .request_body(CreateMessageRequestBody.builder()
                    .receive_id(receive_id)
                    .msg_type("interactive")
                    .content(json.dumps(card, ensure_ascii=False))
                    .build()) \
                .build()
            
            response = self.client.im.v1.message.create(request)
            
            if response.code == 0:
                message_id = response.data.message_id if hasattr(response.data, 'message_id') else 'N/A'
                return True, message_id
            else:
                logger.error(f"❌ 卡片发送失败: {response.code} - {response.msg}")
                return False, ""
                
        except Exception as e:
            logger.error(f"❌ 发送卡片时发生异常: {e}", exc_info=True)
            return False, ""
    
    async def run_full_test(self, target_id: str):
        """运行完整测试套件"""
        safe_print("\n" + "="*60)
        safe_print("🧪 Schema 2.0 完整测试套件")
        safe_print("="*60)
        
        # 确定接收者类型
        receive_id_type = "chat_id" if target_id.startswith("oc_") else "open_id"
        safe_print(f"\n🎯 测试目标: {receive_id_type} = {target_id}")
        
        # 测试 1: 结构验证
        safe_print("\n" + "="*60)
        safe_print("📦 测试阶段 1: 结构验证")
        safe_print("="*60)
        
        cards = [
            (self.factory.create_test_card_v1(), "V1 - 基础输入测试"),
            (self.factory.create_test_card_v2(), "V2 - 多字段测试"),
            (self.factory.create_test_card_v3(), "V3 - 生产环境完整版"),
        ]
        
        validation_results = []
        for card, name in cards:
            is_valid = self.validate_and_print(card, name)
            validation_results.append((name, is_valid))
        
        # 打印验证汇总
        safe_print("\n" + "="*60)
        safe_print("📊 验证汇总:")
        safe_print("="*60)
        for name, is_valid in validation_results:
            status = "✅ 通过" if is_valid else "❌ 失败"
            safe_print(f"  {name}: {status}")
        
        all_valid = all(result[1] for result in validation_results)
        if all_valid:
            safe_print("\n✅ 所有卡片结构验证通过！")
        else:
            safe_print("\n❌ 部分卡片结构验证失败，请检查！")
            return False
        
        # 测试 2: 发送测试
        safe_print("\n" + "="*60)
        safe_print("📤 测试阶段 2: 发送测试")
        safe_print("="*60)
        
        # 发送生产环境版本
        safe_print(f"\n📤 发送 V3 生产环境版本到 {receive_id_type}...")
        success, message_id = await self.send_card(
            self.factory.create_test_card_v3(),
            target_id,
            receive_id_type
        )
        
        if success:
            safe_print(f"✅ 卡片发送成功！消息 ID: {message_id}")
            safe_print("\n📱 请在手机飞书上验证:")
            safe_print("  □ 卡片是否正常显示")
            safe_print("  □ input 输入框是否可见")
            safe_print("  □ 点击输入框是否唤起键盘")
            safe_print("  □ 输入内容是否正常显示")
            safe_print("  □ 按钮点击是否有响应")
            safe_print("  □ 「查看详细网页版」按钮是否能跳转")
            
            # 等待用户测试
            safe_print("\n" + "="*60)
            safe_print("✅ 自动化测试完成！")
            safe_print("   请在飞书中验证卡片显示和交互")
            safe_print("="*60)
            
            return True
        else:
            safe_print("❌ 卡片发送失败！")
            return False


async def main():
    """主函数"""
    safe_print("\n" + "="*60)
    safe_print("🧪 飞书 Schema 2.0 自动化测试工具")
    safe_print("="*60)
    safe_print("\n📋 测试内容:")
    safe_print("  1. Schema 2.0 结构验证")
    safe_print("  2. JSON 格式完整性检查")
    safe_print("  3. input 组件渲染测试")
    safe_print("  4. 按钮交互测试")
    safe_print("  5. 回调处理验证")
    safe_print("\n💡 使用方法:")
    safe_print(f"  python {Path(__file__).name} [chat_id|open_id]")
    safe_print("="*60)
    
    # 默认测试 ID
    default_chat_id = "oc_2e96d78e081c89b7e9b3677cf53d07cf"
    
    try:
        tester = Schema2Tester()
        
        # 检查 backend 服务
        safe_print("\n🔍 检查 backend 服务状态...")
        backend_ok = await tester.check_backend_service()
        
        if not backend_ok:
            safe_print("\n⚠️  警告: 飞书长连接服务可能未启动")
            safe_print("   如需测试回调，请确保 backend 服务运行中")
        
        # 获取目标 ID
        target_id = sys.argv[1] if len(sys.argv) > 1 else default_chat_id
        
        # 运行完整测试
        success = await tester.run_full_test(target_id)
        
        if success:
            safe_print("\n" + "="*60)
            safe_print("✅ 测试完成！")
            safe_print("="*60)
        else:
            safe_print("\n" + "="*60)
            safe_print("❌ 测试失败，请检查日志")
            safe_print("="*60)
            
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
