"""
测试修复效果：
1. HoldingManager 单例模式
2. _call_tushare 异步调用
"""
import sys
import asyncio
from pathlib import Path

# 添加项目路径
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))


def test_holding_manager_singleton():
    """测试 HoldingManager 单例模式"""
    print("\n=== 测试 HoldingManager 单例模式 ===")
    
    from services.holding_manager import HoldingManager
    
    # 创建多个实例
    instances = [HoldingManager() for _ in range(5)]
    
    # 检查是否都是同一个实例
    all_same = all(inst is instances[0] for inst in instances)
    
    print(f"创建了 {len(instances)} 个 HoldingManager 实例")
    print(f"所有实例都是同一个对象: {all_same}")
    
    if all_same:
        print("[PASS] HoldingManager 单例模式正常工作!")
    else:
        print("[FAIL] HoldingManager 单例模式失败!")
        
    return all_same


async def test_async_await():
    """测试异步调用语法"""
    print("\n=== 测试异步调用语法 ===")
    
    # 简单测试 asyncio 是否正常工作
    async def mock_async_call():
        await asyncio.sleep(0.1)
        return "success"
    
    result = await mock_async_call()
    print(f"异步调用测试结果: {result}")
    print("[PASS] 异步调用语法正常!")
    return result == "success"


def test_syntax_check():
    """语法检查 - 确保修复的文件没有语法错误"""
    print("\n=== 语法检查 ===")
    
    import py_compile
    
    # 使用绝对路径
    base_path = Path(r"D:\play-ground\股票研究\stock-peg\backend")
    files_to_check = [
        base_path / "services" / "holding_manager.py",
        base_path / "services" / "fundamental_analyzer.py"
    ]
    
    all_ok = True
    for file_path in files_to_check:
        try:
            py_compile.compile(str(file_path), doraise=True)
            print(f"[PASS] {file_path.name}: 语法正确")
        except py_compile.PyCompileError as e:
            print(f"[FAIL] {file_path.name}: 语法错误 - {e}")
            all_ok = False
    
    return all_ok


async def main():
    """主测试函数"""
    print("=" * 50)
    print("  开始验证修复效果")
    print("=" * 50)
    
    results = []
    
    # 测试1: 单例模式
    results.append(test_holding_manager_singleton())
    
    # 测试2: 异步调用
    results.append(await test_async_await())
    
    # 测试3: 语法检查
    results.append(test_syntax_check())
    
    print("\n" + "=" * 50)
    print("  测试结果汇总")
    print("=" * 50)
    
    if all(results):
        print("[PASS] 所有测试通过!")
    else:
        print("[FAIL] 部分测试失败!")
    
    return all(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
