"""
测试日志行数限制功能
验证 LineLimitedFileHandler 是否正常工作
"""
import sys
import os
from pathlib import Path
import logging
import time

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.logging_config import setup_logging


def test_line_limit():
    """测试日志行数限制功能"""
    print("=" * 60)
    print("测试日志行数限制功能")
    print("=" * 60)
    
    # 设置日志
    log_dir = project_root / "logs"
    setup_logging(str(log_dir), log_level="INFO")
    
    # 创建测试日志器
    logger = logging.getLogger("test_line_limit")
    
    # 获取日志文件路径
    app_log_path = log_dir / "app.log"
    
    # 读取当前行数
    with open(app_log_path, 'r', encoding='utf-8') as f:
        initial_lines = len(f.readlines())
    
    print(f"\n初始行数: {initial_lines}")
    
    # 写入150行日志（超过100行限制）
    print("\n写入150行测试日志...")
    for i in range(150):
        logger.info(f"测试日志行 {i+1}/150 - 这是一条测试消息")
    
    # 等待日志刷新
    time.sleep(0.5)
    
    # 检查裁剪后的行数
    with open(app_log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        final_lines = len(lines)
    
    print(f"裁剪后行数: {final_lines}")
    
    # 验证
    if final_lines <= 100:
        print("\n[PASS] 测试通过！日志文件已自动裁剪到100行以内")
    else:
        print(f"\n[FAIL] 测试失败！日志文件行数为 {final_lines}，超过100行")
    
    # 显示最后几行日志
    print("\n最后5行日志:")
    for line in lines[-5:]:
        # 过滤掉无法编码的字符
        safe_line = line.rstrip().encode('gbk', errors='ignore').decode('gbk')
        print(f"  {safe_line}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_line_limit()
