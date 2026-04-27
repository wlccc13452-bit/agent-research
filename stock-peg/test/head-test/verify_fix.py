"""
验证修复是否成功
"""
import sys
import asyncio
from pathlib import Path

# 添加 backend 到 Python 路径
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

print("=" * 80)
print("验证修复结果")
print("=" * 80)
print()

all_passed = True

# ==================== 验证问题1修复 ====================
print("【验证1】technical_cache 导入")
print("-" * 80)

try:
    from services.extended_cache import technical_cache
    print("[OK] technical_cache 导入成功")
    print(f"    类型: {type(technical_cache)}")
except ImportError as e:
    print(f"[X] 导入失败: {e}")
    all_passed = False

print()

# ==================== 验证问题2修复 ====================
print("【验证2】PredictionResult key_factors 格式")
print("-" * 80)

try:
    from models.prediction import PredictionResult
    from datetime import datetime
    
    # 测试正确的格式
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
    print("[OK] PredictionResult key_factors 格式正确")
    print(f"    key_factors: {result.key_factors}")
except Exception as e:
    print(f"[X] 验证失败: {e}")
    all_passed = False

print()

# ==================== 验证 stock_service.py 中的修复 ====================
print("【验证3】stock_service.py 中的导入语句")
print("-" * 80)

stock_service_file = backend_path / "services" / "stock_service.py"

if stock_service_file.exists():
    with open(stock_service_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否还有错误的导入
    if "technical_indicators_cache" in content:
        print("[X] stock_service.py 中仍然存在 technical_indicators_cache")
        all_passed = False
    else:
        print("[OK] stock_service.py 中已修复导入语句")
    
    if "from services.extended_cache import technical_cache" in content:
        print("[OK] stock_service.py 中已使用正确的导入")
    else:
        print("[X] stock_service.py 中未找到正确的导入语句")
        all_passed = False
else:
    print(f"[X] 文件不存在: {stock_service_file}")
    all_passed = False

print()

# ==================== 验证 prediction_engine.py 中的修复 ====================
print("【验证4】prediction_engine.py 中的 key_factors 格式")
print("-" * 80)

prediction_engine_file = backend_path / "services" / "prediction_engine.py"

if prediction_engine_file.exists():
    with open(prediction_engine_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否还有错误的格式
    if "{'factor': '技术面', 'weight': 35.0}" in content:
        print("[X] prediction_engine.py 中仍然存在错误的 key_factors 格式")
        all_passed = False
    else:
        print("[OK] prediction_engine.py 中已修复 key_factors 格式")
    
    if "{'技术面': 35.0}" in content:
        print("[OK] prediction_engine.py 中已使用正确的 key_factors 格式")
    else:
        print("[X] prediction_engine.py 中未找到正确的 key_factors 格式")
        all_passed = False
else:
    print(f"[X] 文件不存在: {prediction_engine_file}")
    all_passed = False

print()
print("=" * 80)

if all_passed:
    print("[OK] 所有验证通过！修复成功！")
else:
    print("[X] 部分验证失败，请检查修复脚本")

print("=" * 80)
