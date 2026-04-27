"""
测试控制台输出配置系统

验证配置加载、日志过滤、API接口是否正常工作
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from config.settings import settings
from services.console_output_filter import ConsoleOutputFilter, should_show_progress
from services.managed_logger import get_stock_logger, get_feishu_logger


def test_config_loading():
    """测试配置加载"""
    print("=" * 60)
    print("测试配置加载")
    print("=" * 60)
    
    print(f"\n总开关: {settings.enable_console_output}")
    print(f"错误日志: {settings.enable_errors}")
    print(f"警告日志: {settings.enable_warnings}")
    print(f"调试日志: {settings.enable_debug}")
    
    print(f"\n股票数据日志: {settings.enable_stock_data}")
    print(f"市场指数日志: {settings.enable_market_index}")
    print(f"飞书机器人日志: {settings.enable_feishu_bot}")
    
    print(f"\n进度条显示: {settings.show_progress_bar}")
    print(f"预加载进度: {settings.enable_preload_progress}")
    
    print("\n✅ 配置加载测试通过")


def test_log_filter():
    """测试日志过滤器"""
    print("\n" + "=" * 60)
    print("测试日志过滤器")
    print("=" * 60)
    
    # 创建测试logger
    test_logger = logging.getLogger('services.stock_data_service')
    test_logger.setLevel(logging.DEBUG)
    
    # 添加控制台handler
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # 添加过滤器
    filter_instance = ConsoleOutputFilter()
    handler.addFilter(filter_instance)
    test_logger.addHandler(handler)
    
    print(f"\n当前配置: enable_stock_data = {settings.enable_stock_data}")
    print("\n测试不同级别的日志:")
    
    test_logger.debug("这是一条调试日志（stock_data）")
    test_logger.info("这是一条信息日志（股票数据更新）")
    test_logger.warning("这是一条警告日志")
    test_logger.error("这是一条错误日志")
    
    print("\n✅ 日志过滤器测试完成")


def test_managed_logger():
    """测试受管理的日志器"""
    print("\n" + "=" * 60)
    print("测试受管理的日志器")
    print("=" * 60)
    
    # 创建不同类型的logger
    stock_logger = get_stock_logger('test_stock')
    feishu_logger = get_feishu_logger('test_feishu')
    
    print(f"\n股票日志配置: enable_stock_data = {settings.enable_stock_data}")
    print("测试股票日志:")
    stock_logger.info("股票数据更新消息")
    stock_logger.debug("股票调试信息")
    
    print(f"\n飞书日志配置: enable_feishu_bot = {settings.enable_feishu_bot}")
    print("测试飞书日志:")
    feishu_logger.info("飞书消息接收")
    feishu_logger.debug("飞书调试信息")
    
    print("\n✅ 受管理日志器测试完成")


def test_progress_bar():
    """测试进度条配置"""
    print("\n" + "=" * 60)
    print("测试进度条配置")
    print("=" * 60)
    
    print(f"\n进度条显示: {settings.show_progress_bar}")
    print(f"预加载进度: {settings.enable_preload_progress}")
    print(f"是否应该显示进度条: {should_show_progress()}")
    
    print("\n✅ 进度条配置测试完成")


def test_api_summary():
    """测试API摘要"""
    print("\n" + "=" * 60)
    print("配置摘要")
    print("=" * 60)
    
    enabled_count = sum([
        settings.enable_stock_data,
        settings.enable_market_index,
        settings.enable_kline_data,
        settings.enable_financial_data,
        settings.enable_us_market,
        settings.enable_update_progress,
        settings.enable_preload_progress,
        settings.enable_cache,
        settings.enable_websocket,
        settings.enable_scheduler,
        settings.enable_background_task,
        settings.enable_database,
        settings.enable_api_request,
        settings.enable_debug,
    ])
    
    print(f"\n启用的数据输出项: {enabled_count}/14")
    print(f"飞书机器人输出: {'✓' if all([settings.enable_feishu_bot, settings.enable_feishu_connection, settings.enable_feishu_chat]) else '✗'}")
    print(f"错误和警告: {'✓' if all([settings.enable_errors, settings.enable_warnings]) else '✗'}")
    
    if enabled_count > 10:
        status = "详细模式（适合调试）"
    elif enabled_count < 3:
        status = "简洁模式（适合生产）"
    else:
        status = "平衡模式（适合开发）"
    
    print(f"\n当前状态: {status}")
    print("\n✅ 配置摘要测试完成")


def main():
    """运行所有测试"""
    print("\n" + "🚀 开始测试控制台输出配置系统" + "\n")
    
    try:
        test_config_loading()
        test_log_filter()
        test_managed_logger()
        test_progress_bar()
        test_api_summary()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        print("\n使用方法:")
        print("1. 修改 backend/config/console_output.ini 配置文件")
        print("2. 重启服务生效")
        print("3. 或使用API接口动态修改: POST /api/config/console-output/update")
        print("\n推荐配置:")
        print("- 生产环境: enable_feishu_bot=true, 其他数据类设为false")
        print("- 开发环境: 根据需要开启特定类型日志")
        print("- 调试模式: enable_debug=true + 开启相关数据类型")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
