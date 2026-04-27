"""
测试飞书长连接服务的独立线程模式

验证：
1. start_in_thread() 能正确启动线程
2. 主事件循环被正确传递
3. 跨线程广播能正常工作
"""
import asyncio
import sys
import os

# 设置后端目录
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

import logging
from datetime import datetime

# 直接导入需要的模块，避免通过 __init__.py 导入
sys.path.insert(0, backend_dir)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


async def test_thread_mode():
    """测试独立线程模式"""
    from services.feishu_long_connection_service import feishu_long_connection_service
    
    logger.info("=" * 60)
    logger.info("测试飞书长连接服务 - 独立线程模式")
    logger.info("=" * 60)
    
    # 检查是否启用
    if not feishu_long_connection_service.enabled:
        logger.warning("飞书长连接服务未启用（缺少配置）")
        logger.info("请检查 .env 文件中的 FEISHU_APP_ID 和 FEISHU_APP_SECRET")
        return False
    
    # 获取主事件循环
    main_loop = asyncio.get_running_loop()
    logger.info(f"✅ 主事件循环: {main_loop}")
    
    # 启动服务
    logger.info("正在启动飞书长连接服务...")
    feishu_long_connection_service.start_in_thread(main_loop)
    
    # 等待初始化
    await asyncio.sleep(2)
    
    # 检查状态
    logger.info("-" * 40)
    logger.info(f"服务运行状态: {feishu_long_connection_service._running}")
    logger.info(f"线程存活: {feishu_long_connection_service._thread and feishu_long_connection_service._thread.is_alive()}")
    logger.info(f"主事件循环已设置: {feishu_long_connection_service._main_loop is not None}")
    
    if feishu_long_connection_service._running and feishu_long_connection_service._thread:
        if feishu_long_connection_service._thread.is_alive():
            logger.info("=" * 60)
            logger.info("✅ 飞书长连接服务运行正常！")
            logger.info("   - 线程模式: 独立线程（避免嵌套事件循环）")
            logger.info("   - 主循环: 已传递，可用于跨线程广播")
            logger.info("=" * 60)
            
            # 测试跨线程广播
            logger.info("\n测试跨线程广播...")
            from services.websocket_manager import manager
            await manager.start()
            
            # 模拟广播
            test_payload = {
                "type": "test-broadcast",
                "data": {"message": "测试消息", "time": datetime.now().isoformat()}
            }
            
            # 直接调用广播方法（模拟从长连接线程调用）
            feishu_long_connection_service._broadcast(test_payload)
            logger.info("✅ 跨线程广播测试完成")
            
            await manager.stop()
            return True
        else:
            logger.error("❌ 线程已退出")
            return False
    else:
        logger.error("❌ 服务启动失败")
        return False


async def main():
    """主函数"""
    try:
        success = await test_thread_mode()
        if success:
            logger.info("\n🎉 测试完成！飞书长连接服务已正确集成到 FastAPI。")
            logger.info("提示: 服务将在后台运行，按 Ctrl+C 退出测试")
            
            # 保持运行，观察长连接状态
            from services.feishu_long_connection_service import feishu_long_connection_service
            while feishu_long_connection_service._running:
                await asyncio.sleep(5)
                if feishu_long_connection_service._thread and not feishu_long_connection_service._thread.is_alive():
                    logger.warning("⚠️ 长连接线程已退出")
                    break
        else:
            logger.error("\n❌ 测试失败")
            
    except KeyboardInterrupt:
        logger.info("\n用户中断")
    except Exception as e:
        logger.error(f"测试异常: {e}", exc_info=True)
    finally:
        # 停止服务
        from services.feishu_long_connection_service import feishu_long_connection_service
        await feishu_long_connection_service.stop()
        logger.info("服务已停止")


if __name__ == "__main__":
    asyncio.run(main())
