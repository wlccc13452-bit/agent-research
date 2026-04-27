"""
Server-Client Debug Test Script
测试server和client加载是否正常，检查是否有卡顿问题
"""
import asyncio
import httpx
import time
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional

# 设置控制台编码
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8')

# 配置
API_BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0  # 请求超时时间

class TestResult:
    """测试结果"""
    def __init__(self, name: str):
        self.name = name
        self.success = False
        self.duration_ms = 0
        self.error = None
        self.data = None
        self.response_size = 0
    
    def to_dict(self):
        return {
            "name": self.name,
            "success": self.success,
            "duration_ms": round(self.duration_ms, 2),
            "error": self.error,
            "response_size": self.response_size
        }

class ServerClientTest:
    """Server-Client测试类"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.client = httpx.AsyncClient(timeout=TIMEOUT)
        self.slow_threshold_ms = 3000  # 慢请求阈值（毫秒）
        self.very_slow_threshold_ms = 10000  # 非常慢阈值
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()
    
    async def test_health_check(self) -> TestResult:
        """测试健康检查"""
        result = TestResult("health_check")
        start_time = time.time()
        
        try:
            response = await self.client.get(f"{API_BASE_URL}/health")
            result.duration_ms = (time.time() - start_time) * 1000
            result.success = response.status_code == 200
            result.data = response.json()
            result.response_size = len(response.content)
        except Exception as e:
            result.duration_ms = (time.time() - start_time) * 1000
            result.error = str(e)
        
        self.results.append(result)
        return result
    
    async def test_get_holdings(self) -> TestResult:
        """测试获取持仓数据"""
        result = TestResult("get_holdings")
        start_time = time.time()
        
        try:
            response = await self.client.get(f"{API_BASE_URL}/api/holdings/")
            result.duration_ms = (time.time() - start_time) * 1000
            result.success = response.status_code == 200
            result.data = response.json()
            result.response_size = len(response.content)
        except Exception as e:
            result.duration_ms = (time.time() - start_time) * 1000
            result.error = str(e)
        
        self.results.append(result)
        return result
    
    async def test_get_cn_indices(self) -> TestResult:
        """测试获取A股指数"""
        result = TestResult("get_cn_indices")
        start_time = time.time()
        
        try:
            response = await self.client.get(f"{API_BASE_URL}/api/stocks/cn-indices")
            result.duration_ms = (time.time() - start_time) * 1000
            result.success = response.status_code == 200
            result.data = response.json()
            result.response_size = len(response.content)
        except Exception as e:
            result.duration_ms = (time.time() - start_time) * 1000
            result.error = str(e)
        
        self.results.append(result)
        return result
    
    async def test_get_stock_quote(self, stock_code: str) -> TestResult:
        """测试获取股票行情"""
        result = TestResult(f"get_quote_{stock_code}")
        start_time = time.time()
        
        try:
            response = await self.client.get(f"{API_BASE_URL}/api/stocks/quote/{stock_code}")
            result.duration_ms = (time.time() - start_time) * 1000
            if response.status_code == 200:
                result.success = True
                result.data = response.json()
            elif response.status_code == 404:
                # 404是正常的，表示数据库没有数据但已触发后台更新
                result.success = True
                result.data = {"status": "not_found", "detail": response.json()}
            else:
                result.success = False
                result.error = f"Status: {response.status_code}"
            result.response_size = len(response.content)
        except Exception as e:
            result.duration_ms = (time.time() - start_time) * 1000
            result.error = str(e)
        
        self.results.append(result)
        return result
    
    async def test_get_kline_from_db(self, stock_code: str, count: int = 100) -> TestResult:
        """测试从数据库获取K线数据"""
        result = TestResult(f"get_kline_db_{stock_code}")
        start_time = time.time()
        
        try:
            response = await self.client.get(
                f"{API_BASE_URL}/api/stocks/kline-db/{stock_code}",
                params={"period": "day", "count": count}
            )
            result.duration_ms = (time.time() - start_time) * 1000
            if response.status_code == 200:
                result.success = True
                data = response.json()
                result.data = {
                    "data_count": len(data.get("data", [])),
                    "metadata": data.get("metadata", {})
                }
            else:
                result.success = False
                result.error = f"Status: {response.status_code}"
            result.response_size = len(response.content)
        except Exception as e:
            result.duration_ms = (time.time() - start_time) * 1000
            result.error = str(e)
        
        self.results.append(result)
        return result
    
    async def test_batch_quotes(self, stock_codes: List[str]) -> TestResult:
        """测试批量获取行情"""
        result = TestResult("batch_quotes")
        start_time = time.time()
        
        try:
            response = await self.client.post(
                f"{API_BASE_URL}/api/stocks/quotes",
                json=stock_codes
            )
            result.duration_ms = (time.time() - start_time) * 1000
            result.success = response.status_code == 200
            result.data = {
                "count": len(response.json()) if response.status_code == 200 else 0
            }
            result.response_size = len(response.content)
        except Exception as e:
            result.duration_ms = (time.time() - start_time) * 1000
            result.error = str(e)
        
        self.results.append(result)
        return result
    
    async def test_data_update_status(self) -> TestResult:
        """测试数据更新状态"""
        result = TestResult("data_update_status")
        start_time = time.time()
        
        try:
            response = await self.client.get(f"{API_BASE_URL}/api/data/status-all")
            result.duration_ms = (time.time() - start_time) * 1000
            result.success = response.status_code == 200
            result.data = response.json()
            result.response_size = len(response.content)
        except Exception as e:
            result.duration_ms = (time.time() - start_time) * 1000
            result.error = str(e)
        
        self.results.append(result)
        return result
    
    async def test_fundamental_annual_report(self, stock_code: str) -> TestResult:
        """测试获取年报数据"""
        result = TestResult(f"get_annual_report_{stock_code}")
        start_time = time.time()
        
        try:
            response = await self.client.get(
                f"{API_BASE_URL}/api/fundamental/{stock_code}/annual-report"
            )
            result.duration_ms = (time.time() - start_time) * 1000
            if response.status_code == 200:
                result.success = True
                result.data = response.json()
            elif response.status_code == 404:
                result.success = True  # 404是正常的
                result.data = {"status": "not_found"}
            else:
                result.success = False
                result.error = f"Status: {response.status_code}"
            result.response_size = len(response.content)
        except Exception as e:
            result.duration_ms = (time.time() - start_time) * 1000
            result.error = str(e)
        
        self.results.append(result)
        return result
    
    async def test_us_market_indices(self) -> TestResult:
        """测试获取美股指数"""
        result = TestResult("get_us_indices")
        start_time = time.time()
        
        try:
            response = await self.client.get(f"{API_BASE_URL}/api/us-market/indices")
            result.duration_ms = (time.time() - start_time) * 1000
            if response.status_code == 200:
                result.success = True
                result.data = response.json()
            else:
                result.success = False
                result.error = f"Status: {response.status_code}"
            result.response_size = len(response.content)
        except Exception as e:
            result.duration_ms = (time.time() - start_time) * 1000
            result.error = str(e)
        
        self.results.append(result)
        return result
    
    def print_result(self, result: TestResult):
        """打印单个测试结果"""
        status = "✅" if result.success else "❌"
        duration_status = ""
        
        if result.duration_ms > self.very_slow_threshold_ms:
            duration_status = " ⚠️ VERY SLOW"
        elif result.duration_ms > self.slow_threshold_ms:
            duration_status = " ⚠️ SLOW"
        
        print(f"  {status} {result.name}: {result.duration_ms:.2f}ms{duration_status}")
        if result.error:
            print(f"      Error: {result.error}")
    
    def print_summary(self):
        """打印测试摘要"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.success)
        failed = total - passed
        
        slow_count = sum(1 for r in self.results if r.duration_ms > self.slow_threshold_ms)
        very_slow_count = sum(1 for r in self.results if r.duration_ms > self.very_slow_threshold_ms)
        
        avg_duration = sum(r.duration_ms for r in self.results) / total if total > 0 else 0
        max_duration = max((r.duration_ms for r in self.results), default=0)
        
        print("\n" + "=" * 60)
        print("📊 测试摘要")
        print("=" * 60)
        print(f"  总测试数: {total}")
        print(f"  通过: {passed} ({passed/total*100:.1f}%)" if total > 0 else "  通过: 0")
        print(f"  失败: {failed}")
        print(f"  慢请求(>3s): {slow_count}")
        print(f"  极慢请求(>10s): {very_slow_count}")
        print(f"  平均响应时间: {avg_duration:.2f}ms")
        print(f"  最大响应时间: {max_duration:.2f}ms")
        print("=" * 60)
        
        if failed > 0:
            print("\n❌ 失败的测试:")
            for r in self.results:
                if not r.success:
                    print(f"  - {r.name}: {r.error}")
        
        if slow_count > 0:
            print("\n⚠️ 慢请求:")
            for r in self.results:
                if r.duration_ms > self.slow_threshold_ms:
                    print(f"  - {r.name}: {r.duration_ms:.2f}ms")


async def run_basic_tests():
    """运行基础测试"""
    print("=" * 60)
    print("🚀 开始 Server-Client 基础测试")
    print(f"   API地址: {API_BASE_URL}")
    print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tester = ServerClientTest()
    
    try:
        # 阶段1: 健康检查
        print("\n📍 阶段1: 健康检查")
        result = await tester.test_health_check()
        tester.print_result(result)
        
        if not result.success:
            print("\n❌ 服务器未启动或无法访问，停止测试")
            return tester
        
        # 阶段2: 核心数据加载测试
        print("\n📍 阶段2: 核心数据加载测试")
        
        # 并行测试多个核心API
        tasks = [
            tester.test_get_holdings(),
            tester.test_get_cn_indices(),
            tester.test_data_update_status(),
            tester.test_us_market_indices()
        ]
        results = await asyncio.gather(*tasks)
        for r in results:
            tester.print_result(r)
        
        # 获取持仓中的股票代码
        holdings_result = results[0]
        stock_codes = []
        if holdings_result.success and holdings_result.data:
            for sector in holdings_result.data.get("sectors", []):
                for stock in sector.get("stocks", []):
                    code = stock.get("code")
                    if code and not code.startswith("UNKNOWN"):
                        stock_codes.append(code)
        
        # 阶段3: 股票数据测试
        print("\n📍 阶段3: 股票数据测试")
        
        if stock_codes:
            # 取前3个股票进行测试
            test_codes = stock_codes[:3]
            
            # 并行测试行情和K线
            tasks = []
            for code in test_codes:
                tasks.append(tester.test_get_stock_quote(code))
                tasks.append(tester.test_get_kline_from_db(code))
                tasks.append(tester.test_fundamental_annual_report(code))
            
            results = await asyncio.gather(*tasks)
            for r in results:
                tester.print_result(r)
            
            # 批量行情测试
            print("\n  批量行情测试:")
            result = await tester.test_batch_quotes(test_codes)
            tester.print_result(result)
        else:
            print("  ⚠️ 未找到自持股票，跳过股票数据测试")
        
    finally:
        await tester.close()
    
    # 打印摘要
    tester.print_summary()
    
    return tester


async def run_stress_test(requests_per_endpoint: int = 5):
    """运行压力测试"""
    print("\n" + "=" * 60)
    print("🔥 开始压力测试")
    print(f"   每个端点请求数: {requests_per_endpoint}")
    print("=" * 60)
    
    tester = ServerClientTest()
    
    try:
        # 并发测试健康检查
        print("\n📍 并发健康检查测试")
        tasks = [tester.test_health_check() for _ in range(requests_per_endpoint)]
        results = await asyncio.gather(*tasks)
        
        for r in results:
            tester.print_result(r)
        
        # 并发测试持仓API
        print("\n📍 并发持仓API测试")
        tasks = [tester.test_get_holdings() for _ in range(requests_per_endpoint)]
        results = await asyncio.gather(*tasks)
        
        for r in results:
            tester.print_result(r)
        
    finally:
        await tester.close()
    
    tester.print_summary()
    return tester


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("📊 Server-Client Debug 测试工具")
    print("=" * 60)
    
    # 检查命令行参数
    mode = sys.argv[1] if len(sys.argv) > 1 else "basic"
    
    if mode == "stress":
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        await run_stress_test(count)
    elif mode == "basic":
        await run_basic_tests()
    else:
        print(f"未知模式: {mode}")
        print("用法: python test_server_client.py [basic|stress] [请求数]")
        print("  basic - 基础功能测试")
        print("  stress [N] - 压力测试，N为每个端点请求数")


if __name__ == "__main__":
    asyncio.run(main())
