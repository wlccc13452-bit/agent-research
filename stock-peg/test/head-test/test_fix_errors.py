"""
测试并修复后端错误

问题1: technical_indicators_cache 导入错误
问题2: PredictionResult key_factors 验证错误
"""
import sys
import asyncio
from pathlib import Path

# 添加 backend 到 Python 路径
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

print("=" * 80)
print("错误修复测试")
print("=" * 80)
print()

# ==================== 问题1: 检查导入错误 ====================
print("【问题1】检查 technical_indicators_cache 导入错误")
print("-" * 80)

try:
    from services.extended_cache import technical_indicators_cache
    print("[OK] technical_indicators_cache 导入成功")
except ImportError as e:
    print(f"[X] 导入失败: {e}")
    print("[!] 原因: extended_cache.py 中定义的是 technical_cache")
    print()
    
    # 检查 extended_cache.py 中实际定义的缓存
    try:
        from services.extended_cache import technical_cache
        print("[OK] technical_cache 存在且导入成功")
        print(f"[i] technical_cache 类型: {type(technical_cache)}")
        print("[i] 建议: 修改 stock_service.py 中的导入语句")
        print("    from services.extended_cache import technical_cache  # 改为 technical_cache")
    except ImportError as e2:
        print(f"[X] technical_cache 也无法导入: {e2}")

print()

# ==================== 问题2: 检查 PredictionResult 验证错误 ====================
print("【问题2】检查 PredictionResult key_factors 验证错误")
print("-" * 80)

try:
    from models.prediction import PredictionResult
    from datetime import datetime
    
    # 测试错误的格式（字符串类型的 factor）
    print("[i] 测试错误格式（字符串 factor）:")
    try:
        result = PredictionResult(
            stock_code='600219',
            stock_name='南山铝业',
            prediction_date='2026-03-09',
            direction='上涨',
            probability=0.65,
            target_price_range=[10.0, 12.0],
            confidence='中',
            risk_level='低',
            key_factors=[
                {'factor': '技术面', 'weight': 35.0},
                {'factor': '基本面', 'weight': 25.0},
            ],
            timestamp=datetime.now()
        )
        print("[OK] 字符串 factor 格式验证通过（不应该通过）")
    except Exception as e:
        print(f"[X] 验证失败（预期）: {str(e)[:100]}...")
    
    print()
    
    # 测试正确的格式（数字类型的 factor）
    print("[i] 测试正确格式（特征名作为键）:")
    try:
        result = PredictionResult(
            stock_code='600219',
            stock_name='南山铝业',
            prediction_date='2026-03-09',
            direction='上涨',
            probability=0.65,
            target_price_range=[10.0, 12.0],
            confidence='中',
            risk_level='低',
            key_factors=[
                {'技术面': 35.0},
                {'基本面': 25.0},
                {'板块轮动': 25.0},
                {'国际市场': 15.0}
            ],
            timestamp=datetime.now()
        )
        print("[OK] 数字 factor 格式验证通过")
        print(f"[i] key_factors: {result.key_factors}")
    except Exception as e:
        print(f"[X] 验证失败: {str(e)[:100]}...")
    
    print()
    
    # 测试另一个可能的正确格式（修改模型定义）
    print("[i] 测试格式3（factor 和 weight 都是字符串键）:")
    try:
        result = PredictionResult(
            stock_code='600219',
            stock_name='南山铝业',
            prediction_date='2026-03-09',
            direction='上涨',
            probability=0.65,
            target_price_range=[10.0, 12.0],
            confidence='中',
            risk_level='低',
            key_factors=[
                {'factor': '技术面', 'weight': '35.0'},  # weight 也改为字符串
            ],
            timestamp=datetime.now()
        )
        print("[OK] 字符串 weight 格式验证通过（不应该通过）")
    except Exception as e:
        print(f"[X] 验证失败（预期）: {str(e)[:100]}...")
    
except Exception as e:
    print(f"[X] 导入 PredictionResult 失败: {e}")

print()
print("=" * 80)

# ==================== 查看模型定义 ====================
print("【查看】PredictionResult 模型定义")
print("-" * 80)

try:
    import inspect
    from models.prediction import PredictionResult
    
    source = inspect.getsource(PredictionResult)
    print(source)
except Exception as e:
    print(f"[X] 获取源码失败: {e}")

print()
print("=" * 80)

# ==================== 建议 ====================
print("【修复建议】")
print("-" * 80)
print()
print("问题1: technical_indicators_cache 导入错误")
print("  文件: backend/services/stock_service.py")
print("  修复: 第468行")
print("    原代码: from services.extended_cache import technical_indicators_cache")
print("    改为:   from services.extended_cache import technical_cache")
print("  同时修改: 第470行和第530行")
print("    原代码: technical_indicators_cache.get(stock_code)")
print("    改为:   technical_cache.get(stock_code)")
print()
print("问题2: PredictionResult key_factors 验证错误")
print("  文件: backend/services/prediction_engine.py")
print("  修复: 第479-484行，修改默认 key_factors 格式")
print("    原代码:")
print("      key_factors = [")
print("          {'factor': '技术面', 'weight': 35.0},")
print("          {'factor': '基本面', 'weight': 25.0},")
print("          {'factor': '板块轮动', 'weight': 25.0},")
print("          {'factor': '国际市场', 'weight': 15.0}")
print("      ]")
print("    改为:")
print("      key_factors = [")
print("          {'技术面': 35.0},")
print("          {'基本面': 25.0},")
print("          {'板块轮动': 25.0},")
print("          {'国际市场': 15.0}")
print("      ]")
print()
print("=" * 80)
