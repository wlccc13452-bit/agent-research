"""
简单测试脚本 - 测试导入和环境配置
"""
import sys
from pathlib import Path

# 设置UTF-8编码
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "backend"))

print("="*60)
print("环境配置测试")
print("="*60)

print(f"\n项目根目录: {project_root}")
print(f"Python 版本: {sys.version}")
print(f"Python 路径: {sys.path[0]}")

# 测试导入
print("\n测试导入模块...")
try:
    import asyncio
    print("[OK] asyncio")
    
    import json
    print("[OK] json")
    
    from datetime import datetime
    print("[OK] datetime")
    
    print("\n测试导入项目模块...")
    
    from config.settings import settings
    print(f"[OK] settings - tushare_token: {'已配置' if settings.tushare_token else '未配置'}")
    
    from services.stock_service import StockService
    print("[OK] StockService")
    
    from services.fundamental_analyzer import FundamentalAnalyzer
    print("[OK] FundamentalAnalyzer")
    
    from services.llm_service import LLMService
    print("[OK] LLMService")
    
    # 检查LLM配置
    llm = LLMService()
    print(f"[OK] LLM Service - 智谱AI Key: {'已配置' if llm.zhipu_api_key else '未配置'}")
    
    print("\n" + "="*60)
    print("[SUCCESS] 所有模块导入成功！")
    print("="*60)
    
except Exception as e:
    print(f"\n[ERROR] 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
