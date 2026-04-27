"""
自动修复脚本 - 修复后端错误

问题1: technical_indicators_cache 导入错误
问题2: PredictionResult key_factors 验证错误
"""
import sys
from pathlib import Path

# 添加 backend 到 Python 路径
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

print("=" * 80)
print("自动修复脚本")
print("=" * 80)
print()

# ==================== 修复问题1: technical_indicators_cache 导入错误 ====================
print("【修复1】修复 technical_indicators_cache 导入错误")
print("-" * 80)

stock_service_file = backend_path / "services" / "stock_service.py"

if stock_service_file.exists():
    with open(stock_service_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份原文件
    backup_file = stock_service_file.with_suffix('.py.backup')
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"[i] 已备份原文件: {backup_file}")
    
    # 修复导入语句
    original_import = "from services.extended_cache import technical_indicators_cache"
    fixed_import = "from services.extended_cache import technical_cache"
    
    if original_import in content:
        content = content.replace(original_import, fixed_import)
        print("[OK] 已修复导入语句")
    else:
        print("[!] 未找到需要修复的导入语句")
    
    # 修复使用语句
    original_use1 = "technical_indicators_cache.get(stock_code)"
    fixed_use1 = "technical_cache.get(stock_code)"
    
    if original_use1 in content:
        content = content.replace(original_use1, fixed_use1)
        print("[OK] 已修复使用语句1")
    
    original_use2 = "technical_indicators_cache.set(result.dict(), stock_code)"
    fixed_use2 = "technical_cache.set(result.dict(), stock_code)"
    
    if original_use2 in content:
        content = content.replace(original_use2, fixed_use2)
        print("[OK] 已修复使用语句2")
    
    # 写回文件
    with open(stock_service_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"[OK] 已更新文件: {stock_service_file}")
else:
    print(f"[X] 文件不存在: {stock_service_file}")

print()

# ==================== 修复问题2: PredictionResult key_factors 验证错误 ====================
print("【修复2】修复 PredictionResult key_factors 验证错误")
print("-" * 80)

prediction_engine_file = backend_path / "services" / "prediction_engine.py"

if prediction_engine_file.exists():
    with open(prediction_engine_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份原文件
    backup_file = prediction_engine_file.with_suffix('.py.backup')
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"[i] 已备份原文件: {backup_file}")
    
    # 修复 key_factors 格式
    original_factors = """            else:
                # 如果没有特征重要性，使用默认值
                key_factors = [
                    {'factor': '技术面', 'weight': 35.0},
                    {'factor': '基本面', 'weight': 25.0},
                    {'factor': '板块轮动', 'weight': 25.0},
                    {'factor': '国际市场', 'weight': 15.0}
                ]"""
    
    fixed_factors = """            else:
                # 如果没有特征重要性，使用默认值
                # 注意：key_factors 的格式是 List[Dict[str, float]]
                # 每个字典的键是特征名，值是对应的权重
                key_factors = [
                    {'技术面': 35.0},
                    {'基本面': 25.0},
                    {'板块轮动': 25.0},
                    {'国际市场': 15.0}
                ]"""
    
    if original_factors in content:
        content = content.replace(original_factors, fixed_factors)
        print("[OK] 已修复 key_factors 默认值格式")
    else:
        print("[!] 未找到需要修复的 key_factors 默认值")
    
    # 写回文件
    with open(prediction_engine_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"[OK] 已更新文件: {prediction_engine_file}")
else:
    print(f"[X] 文件不存在: {prediction_engine_file}")

print()
print("=" * 80)
print("修复完成！")
print()
print("【验证修复】")
print("-" * 80)
print("请运行验证脚本: python verify_fix.py")
print("=" * 80)
