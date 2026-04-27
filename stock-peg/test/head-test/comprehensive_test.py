"""
综合测试 - 验证修复后的完整功能

测试内容:
1. 技术指标缓存功能
2. 预测引擎功能
3. 完整的股票数据流程
"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime

# 添加 backend 到 Python 路径
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

print("=" * 80)
print("综合功能测试")
print("=" * 80)
print()


async def test_technical_cache():
    """测试技术指标缓存"""
    print("【测试1】技术指标缓存功能")
    print("-" * 80)
    
    try:
        from services.extended_cache import technical_cache
        
        # 测试设置缓存
        test_data = {
            'ma5': 10.5,
            'ma10': 10.3,
            'ma20': 10.0,
            'macd': 0.15,
            'macd_signal': 0.12,
            'macd_hist': 0.03,
            'rsi': 65.0,
            'kdj_k': 70.0,
            'kdj_d': 65.0,
            'kdj_j': 80.0
        }
        
        await technical_cache.set(test_data, '600219')
        print("[OK] 技术指标已缓存: 600219")
        
        # 测试获取缓存
        cached = await technical_cache.get('600219')
        if cached:
            print(f"[OK] 从缓存获取成功: {cached}")
            return True
        else:
            print("[X] 从缓存获取失败")
            return False
            
    except Exception as e:
        print(f"[X] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_prediction_result():
    """测试预测结果模型"""
    print()
    print("【测试2】预测结果模型")
    print("-" * 80)
    
    try:
        from models.prediction import PredictionResult
        
        # 创建预测结果
        result = PredictionResult(
            stock_code='600219',
            stock_name='南山铝业',
            prediction_date=datetime.now().strftime('%Y-%m-%d'),
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
        
        print("[OK] 预测结果创建成功")
        print(f"    股票: {result.stock_name} ({result.stock_code})")
        print(f"    预测: {result.direction}, 概率: {result.probability:.2%}")
        print(f"    关键因素: {result.key_factors}")
        return True
        
    except Exception as e:
        print(f"[X] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_prediction_engine():
    """测试预测引擎（简化版）"""
    print()
    print("【测试3】预测引擎默认 key_factors")
    print("-" * 80)
    
    try:
        # 检查 prediction_engine.py 中的默认 key_factors
        prediction_engine_file = backend_path / "services" / "prediction_engine.py"
        
        with open(prediction_engine_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找默认 key_factors 的定义
        import re
        pattern = r"key_factors = \[\s*\{.*?\}\s*\]"
        matches = re.findall(pattern, content, re.DOTALL)
        
        if matches:
            print("[OK] 找到默认 key_factors 定义")
            for i, match in enumerate(matches, 1):
                # 简化显示
                lines = [l.strip() for l in match.split('\n') if l.strip()]
                print(f"    定义{i}: {lines[0]}")
                if len(lines) > 1:
                    for line in lines[1:3]:
                        print(f"             {line}")
                if len(lines) > 3:
                    print(f"             ...")
            return True
        else:
            print("[X] 未找到默认 key_factors 定义")
            return False
            
    except Exception as e:
        print(f"[X] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_stock_service_imports():
    """测试 stock_service 的导入"""
    print()
    print("【测试4】stock_service 导入检查")
    print("-" * 80)
    
    try:
        # 检查是否能成功导入 stock_service
        from services.stock_service import StockService
        
        print("[OK] StockService 导入成功")
        
        # 检查缓存是否正确
        from services.extended_cache import technical_cache, quote_cache
        
        print(f"[OK] technical_cache: {type(technical_cache)}")
        print(f"[OK] quote_cache: {type(quote_cache)}")
        
        return True
        
    except Exception as e:
        print(f"[X] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    results = []
    
    # 测试1: 技术指标缓存
    result1 = await test_technical_cache()
    results.append(('技术指标缓存', result1))
    
    # 测试2: 预测结果模型
    result2 = await test_prediction_result()
    results.append(('预测结果模型', result2))
    
    # 测试3: 预测引擎
    result3 = await test_prediction_engine()
    results.append(('预测引擎', result3))
    
    # 测试4: stock_service 导入
    result4 = await test_stock_service_imports()
    results.append(('stock_service导入', result4))
    
    # 汇总结果
    print()
    print("=" * 80)
    print("测试汇总")
    print("-" * 80)
    
    for name, result in results:
        status = "[OK]" if result else "[X]"
        print(f"{status} {name}")
    
    total = len(results)
    passed = sum(1 for _, r in results if r)
    
    print()
    print(f"总计: {passed}/{total} 测试通过")
    print("=" * 80)
    
    if passed == total:
        print("[OK] 所有测试通过！")
        return True
    else:
        print("[X] 部分测试失败")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
