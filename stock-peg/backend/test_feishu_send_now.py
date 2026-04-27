"""Test Feishu Bot message sending"""
import asyncio
import sys
sys.path.insert(0, '.')

async def test():
    from services.feishu_bot import FeishuBotService
    from feishu_sdk.config.config import FeishuConfig
    from feishu_sdk.core.client import FeishuClient
    from config import settings
    
    # Create service and inject SDK client
    service = FeishuBotService()
    
    config = FeishuConfig(
        app_id=settings.feishu_app_id or '',
        app_secret=settings.feishu_app_secret or ''
    )
    client = FeishuClient(config)
    service.set_sdk_client(client)
    
    print(f'SDK client injected: {service._sdk_client is not None}')
    
    # Test send message
    chat_id = 'oc_2e96d78e081c89b7e9b3677cf53d07cf'
    result = await service.send_message(chat_id, '测试消息: Backend已重启成功!')
    print(f'Send result: {result}')

if __name__ == '__main__':
    asyncio.run(test())
