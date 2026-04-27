#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书 Input 框独立测试脚本

功能：
1. 创建包含 Input 组件的测试卡片（Schema 2.0）
2. 发送到飞书聊天
3. 等待用户输入回调
4. 显示接收到的输入内容

使用方法：
python test_input_standalone.py [chat_id]

测试流程：
1. 发送带有 Input 框的卡片
2. 在飞书中点击输入框，输入测试内容
3. 点击提交按钮
4. 查看控制台输出的回调数据
"""

import os
import sys
import json
import asyncio
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Windows 控制台编码设置
if sys.platform == 'win32':
    try:
        os.system('chcp 65001 >nul 2>&1')
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# 添加 backend 到路径
backend_dir = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv

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
    """安全打印"""
    try:
        print(text)
    except UnicodeEncodeError:
        # 移除 emoji
        emoji_map = {
            '🧪': '[TEST]', '✅': '[OK]', '❌': '[X]', '🔍': '[SEARCH]',
            '📱': '[MOBILE]', '💡': '[TIP]', '⏳': '[WAIT]', '📝': '[INPUT]',
            '📤': '[SEND]', '📋': '[CARD]', '🎯': '[TARGET]', '📊': '[CHART]',
        }
        for emoji, replacement in emoji_map.items():
            text = text.replace(emoji, replacement)
        print(text)


class InputCardTester:
    """Input 卡片独立测试器"""
    
    def __init__(self):
        self.app_id = os.getenv("FEISHU_APP_ID")
        self.app_secret = os.getenv("FEISHU_APP_SECRET")
        self.backend_url = "http://localhost:8000"
        
        if not self.app_id or not self.app_secret:
            raise ValueError("请在 .env 文件中配置 FEISHU_APP_ID 和 FEISHU_APP_SECRET")
        
        # 延迟导入 lark_oapi
        try:
            import lark_oapi as lark
            from lark_oapi.api.im.v1 import CreateMessageRequest, CreateMessageRequestBody
            
            self.lark = lark
            self.CreateMessageRequest = CreateMessageRequest
            self.CreateMessageRequestBody = CreateMessageRequestBody
            
            # 创建飞书客户端
            self.client = lark.Client.builder() \
                .app_id(self.app_id) \
                .app_secret(self.app_secret) \
                .log_level(lark.LogLevel.ERROR) \
                .build()
            
            logger.info(f"✅ 飞书客户端已初始化 (App ID: {self.app_id[:15]}...)")
        except ImportError:
            logger.error("❌ 无法导入 lark_oapi，请安装: pip install lark-oapi")
            raise
    
    def create_input_test_card(self) -> Dict[str, Any]:
        """创建 Input 测试卡片（Schema 2.0）"""
        return {
            "schema": "2.0",
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "template": "blue",
                "title": {"tag": "plain_text", "content": "🧪 Input 框功能测试"}
            },
            "body": {
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": "**测试说明：**\n"
                                       "✅ Schema 2.0 结构\n"
                                       "✅ Input 组件渲染\n"
                                       "✅ 按钮交互测试\n\n"
                                       "请在下方输入框中输入内容，然后点击提交按钮。"
                        }
                    },
                    {
                        "tag": "input",
                        "name": "test_input_value",
                        "placeholder": {"tag": "plain_text", "content": "在此输入测试内容..."},
                        "label": {"tag": "plain_text", "content": "测试输入"}
                    },
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "✓ 提交测试"},
                        "type": "primary",
                        "value": {"action": "test_input_submit"}
                    },
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "取消"},
                        "type": "default",
                        "value": {"action": "test_cancel"}
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n输入内容将显示在 backend 控制台"
                        }
                    }
                ]
            }
        }
    
    def send_card_to_chat(self, chat_id: str) -> bool:
        """发送测试卡片到聊天"""
        try:
            card = self.create_input_test_card()
            
            safe_print("\n" + "="*60)
            safe_print("📋 测试卡片 JSON 结构:")
            safe_print("="*60)
            safe_print(json.dumps(card, ensure_ascii=False, indent=2))
            
            safe_print("\n" + "="*60)
            safe_print(f"📤 发送测试卡片到聊天: {chat_id}")
            safe_print("="*60)
            
            request = self.CreateMessageRequest.builder() \
                .receive_id_type("chat_id") \
                .request_body(self.CreateMessageRequestBody.builder()
                    .receive_id(chat_id)
                    .msg_type("interactive")
                    .content(json.dumps(card, ensure_ascii=False))
                    .build()) \
                .build()
            
            response = self.client.im.v1.message.create(request)
            
            if response.code == 0:
                message_id = response.data.message_id if hasattr(response.data, 'message_id') else 'N/A'
                safe_print(f"\n✅ 卡片发送成功！")
                safe_print(f"   消息 ID: {message_id}")
                safe_print(f"   Schema 版本: 2.0")
                safe_print(f"   Input 组件: ✅ 已包含")
                return True
            else:
                safe_print(f"\n❌ 卡片发送失败: {response.code} - {response.msg}")
                return False
                
        except Exception as e:
            safe_print(f"\n❌ 发送卡片时发生异常: {e}")
            logger.error("发送卡片异常", exc_info=True)
            return False
    
    async def check_backend_status(self) -> bool:
        """检查 backend 服务状态"""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.backend_url}/health", timeout=3.0)
                if response.status_code == 200:
                    health_data = response.json()
                    feishu_status = health_data.get('services', {}).get('feishu_long_connection', {})
                    is_alive = feishu_status.get('alive', False)
                    
                    safe_print("\n" + "="*60)
                    safe_print("🔍 Backend 服务状态:")
                    safe_print("="*60)
                    safe_print(f"   服务状态: {'✅ 运行中' if is_alive else '❌ 未运行'}")
                    safe_print(f"   飞书长连接: {'✅ 已连接' if is_alive else '❌ 未连接'}")
                    
                    return is_alive
                return False
        except Exception as e:
            safe_print(f"\n❌ Backend 服务未运行或无法访问: {e}")
            return False


async def main():
    """主函数"""
    safe_print("\n" + "="*60)
    safe_print("🧪 飞书 Input 框独立测试")
    safe_print("="*60)
    safe_print("\n测试内容:")
    safe_print("  1. 发送包含 Input 组件的卡片（Schema 2.0）")
    safe_print("  2. 验证 Input 框在手机端是否可见")
    safe_print("  3. 测试用户输入和提交功能")
    safe_print("  4. 验证回调数据接收")
    
    # 默认测试 chat_id
    default_chat_id = "oc_2e96d78e081c89b7e9b3677cf53d07cf"
    
    try:
        tester = InputCardTester()
        
        # 检查 backend 服务
        backend_ok = await tester.check_backend_status()
        
        if not backend_ok:
            safe_print("\n⚠️  警告: 飞书长连接服务未启动")
            safe_print("   如需测试回调，请先启动 backend 服务:")
            safe_print("   python backend/main.py")
            safe_print("\n继续发送测试卡片...")
        
        # 获取目标 chat_id
        chat_id = sys.argv[1] if len(sys.argv) > 1 else default_chat_id
        
        # 发送测试卡片
        success = tester.send_card_to_chat(chat_id)
        
        if success:
            safe_print("\n" + "="*60)
            safe_print("✅ 测试卡片已发送")
            safe_print("="*60)
            safe_print("\n📱 测试步骤:")
            safe_print("  1. 在飞书中打开卡片")
            safe_print("  2. 点击输入框，验证键盘是否唤起")
            safe_print("  3. 输入测试内容")
            safe_print("  4. 点击「提交测试」按钮")
            safe_print("  5. 查看 backend 控制台输出的回调数据")
            
            safe_print("\n💡 提示:")
            safe_print("  - Input 框应该正常显示")
            safe_print("  - 点击输入框应该能唤起键盘")
            safe_print("  - 输入内容会通过回调发送到 backend")
            safe_print("  - 在 backend 控制台查看: 🧪[TEST_INPUT] 用户输入内容")
            
            if backend_ok:
                safe_print("\n⏳ 等待用户输入（5分钟）...")
                await asyncio.sleep(300)
        else:
            safe_print("\n❌ 测试卡片发送失败")
            safe_print("   请检查:")
            safe_print("   1. App ID 和 App Secret 是否正确")
            safe_print("   2. Chat ID 是否存在")
            safe_print("   3. 机器人是否有发送消息的权限")
            
    except ValueError as e:
        safe_print(f"\n❌ 配置错误: {e}")
    except ImportError as e:
        safe_print(f"\n❌ 依赖缺失: {e}")
        safe_print("   请安装: pip install lark-oapi httpx python-dotenv")
    except Exception as e:
        safe_print(f"\n❌ 测试过程中发生错误: {e}")
        logger.error("测试异常", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
