"""
性能分析和压力测试脚本
检查是否有卡顿、慢查询等问题
"""
import asyncio
import httpx
import time
import sys
import os
from datetime import datetime
from typing import List, Dict
import statistics

# 设置控制台编码
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8')

API_BASE_URL = "http://localhost:8000"
TIMEOUT = 60.0

class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=TIMEOUT)
        self.metrics: Dict[str, List[float]] = {}
    
    async def close(self):
        await self.client.aclose()
    
    async def measure(self, name: str, url: str, method: str = "GET", json_data=None) -> float:
        """测量API响应时间"""
        start = time.time()
        try:
            if method == "GET":
                response = await self.client.get(url)
            else:
                response = await self.client.post(url, json=json_data)
            
            duration = (time.time() - start) * 1000
            
            if name not in self.metrics:
                self.metrics[name] = []
            self.metrics[name].append(duration)
            
            return duration
        except Exception as e:
            print(f"  错误 [{name}]: {e}")
            return -1
    
    def get_stats(self, name: str) -> Dict:
        """获取统计信息"""
        if name not in self.metrics or not self.metrics[name]:
            return {}
        
        times = self.metrics[name]
        return {
            "count": len(times),
            "avg": round(statistics.mean(times), 2),
            "min": round(min(times), 2),
            "max": round(max(times), 2),
            "p95": round(sorted(times)[int(len(times) * 0.95)] if len(times) > 1 else times[0], 2),
            "stddev": round(statistics.stdev(times), 2) if len(times) > 1 else 0
        }


async def analyze_slow_apis():
    """分析慢API"""
    print("\n" + "=" * 60)
    print("🔍 慢API分析")
    print("=" * 60)
    
    analyzer = PerformanceAnalyzer()
    
    try:
        # 分析get_cn_indices
        print("\n📍 分析 get_cn_indices...")
        for i in range(5):
            duration = await analyzer.measure("get_cn_indices", f"{API_BASE_URL}/api/stocks/cn-indices")
            print(f"  请求 {i+1}: {duration:.2f}ms")
        
        stats = analyzer.get_stats("get_cn_indices")
        print(f"  统计: {stats}")
        
        # 分析data_update_status
        print("\n📍 分析 data_update_status...")
        for i in range(5):
            duration = await analyzer.measure("data_update_status", f"{API_BASE_URL}/api/data/status-all")
            print(f"  请求 {i+1}: {duration:.2f}ms")
        
        stats = analyzer.get_stats("data_update_status")
        print(f"  统计: {stats}")
        
        # 分析get_us_indices
        print("\n📍 分析 get_us_indices...")
        for i in range(5):
            duration = await analyzer.measure("get_us_indices", f"{API_BASE_URL}/api/us-market/indices")
            print(f"  请求 {i+1}: {duration:.2f}ms")
        
        stats = analyzer.get_stats("get_us_indices")
        print(f"  统计: {stats}")
        
    finally:
        await analyzer.close()


async def stress_test_concurrent():
    """并发压力测试"""
    print("\n" + "=" * 60)
    print("🔥 并发压力测试")
    print("=" * 60)
    
    analyzer = PerformanceAnalyzer()
    
    try:
        # 10个并发请求
        print("\n📍 10个并发请求测试...")
        tasks = [
            analyzer.measure("concurrent_holdings", f"{API_BASE_URL}/api/holdings/")
            for _ in range(10)
        ]
        results = await asyncio.gather(*tasks)
        print(f"  完成: {results}")
        print(f"  统计: {analyzer.get_stats('concurrent_holdings')}")
        
        # 20个并发请求
        print("\n📍 20个并发请求测试...")
        analyzer.metrics["concurrent_holdings"] = []  # 重置
        tasks = [
            analyzer.measure("concurrent_holdings", f"{API_BASE_URL}/api/holdings/")
            for _ in range(20)
        ]
        results = await asyncio.gather(*tasks)
        print(f"  完成: {[round(r, 2) for r in results]}")
        print(f"  统计: {analyzer.get_stats('concurrent_holdings')}")
        
        # 混合并发测试
        print("\n📍 混合API并发测试 (10个每种)...")
        tasks = []
        for _ in range(10):
            tasks.append(analyzer.measure("mixed_holdings", f"{API_BASE_URL}/api/holdings/"))
            tasks.append(analyzer.measure("mixed_indices", f"{API_BASE_URL}/api/stocks/cn-indices"))
        
        results = await asyncio.gather(*tasks)
        print(f"  holdings统计: {analyzer.get_stats('mixed_holdings')}")
        print(f"  indices统计: {analyzer.get_stats('mixed_indices')}")
        
    finally:
        await analyzer.close()


async def analyze_kline_performance():
    """分析K线获取性能"""
    print("\n" + "=" * 60)
    print("📊 K线数据获取性能分析")
    print("=" * 60)
    
    analyzer = PerformanceAnalyzer()
    
    try:
        # 获取持仓中的股票代码
        response = await analyzer.client.get(f"{API_BASE_URL}/api/holdings/")
        holdings = response.json()
        stock_codes = []
        for sector in holdings.get("sectors", []):
            for stock in sector.get("stocks", []):
                code = stock.get("code")
                if code and not code.startswith("UNKNOWN"):
                    stock_codes.append(code)
        
        print(f"\n  找到 {len(stock_codes)} 只股票")
        
        # 测试每只股票的K线获取
        print("\n📍 逐个获取K线数据...")
        for i, code in enumerate(stock_codes[:5]):  # 只测试前5只
            duration = await analyzer.measure(f"kline_{code}", 
                f"{API_BASE_URL}/api/stocks/kline-db/{code}?period=day&count=100")
            print(f"  {code}: {duration:.2f}ms")
        
        # 批量并发获取
        print("\n📍 并发获取K线数据...")
        tasks = []
        for code in stock_codes[:5]:
            tasks.append(analyzer.measure("batch_kline",
                f"{API_BASE_URL}/api/stocks/kline-db/{code}?period=day&count=100"))
        
        results = await asyncio.gather(*tasks)
        print(f"  结果: {[round(r, 2) for r in results]}")
        print(f"  统计: {analyzer.get_stats('batch_kline')}")
        
    finally:
        await analyzer.close()


async def check_blocking_operations():
    """检查是否有阻塞操作"""
    print("\n" + "=" * 60)
    print("⏱️ 阻塞操作检查")
    print("=" * 60)
    
    analyzer = PerformanceAnalyzer()
    
    try:
        # 连续请求，观察是否有阻塞
        print("\n📍 连续请求测试 (检查是否有阻塞)...")
        durations = []
        
        for i in range(20):
            start = time.time()
            response = await analyzer.client.get(f"{API_BASE_URL}/api/holdings/")
            duration = (time.time() - start) * 1000
            durations.append(duration)
            
            # 如果某个请求特别慢，可能是阻塞
            if duration > 1000:
                print(f"  ⚠️ 请求 {i+1} 较慢: {duration:.2f}ms")
        
        avg = statistics.mean(durations)
        stddev = statistics.stdev(durations) if len(durations) > 1 else 0
        
        print(f"\n  平均: {avg:.2f}ms, 标准差: {stddev:.2f}ms")
        
        if stddev > avg * 0.5:
            print("  ⚠️ 响应时间波动较大，可能存在阻塞操作")
        else:
            print("  ✅ 响应时间稳定")
        
    finally:
        await analyzer.close()


async def analyze_database_queries():
    """分析数据库查询"""
    print("\n" + "=" * 60)
    print("💾 数据库查询分析")
    print("=" * 60)
    
    analyzer = PerformanceAnalyzer()
    
    try:
        # 检查数据库状态
        print("\n📍 检查数据更新状态API...")
        start = time.time()
        response = await analyzer.client.get(f"{API_BASE_URL}/api/data/status-all")
        duration = (time.time() - start) * 1000
        
        if response.status_code == 200:
            data = response.json()
            stocks_needing_update = sum(1 for s in data.get("stocks", []) if s.get("needs_update"))
            total_stocks = len(data.get("stocks", []))
            
            print(f"  响应时间: {duration:.2f}ms")
            print(f"  总股票数: {total_stocks}")
            print(f"  需要更新: {stocks_needing_update}")
            
            if duration > 1500:
                print("  ⚠️ 数据库查询较慢，建议检查索引")
            else:
                print("  ✅ 数据库查询正常")
        
    finally:
        await analyzer.close()


async def main():
    print("\n" + "=" * 60)
    print("📊 性能分析和压力测试")
    print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 检查服务器是否运行
    async with httpx.AsyncClient(timeout=5) as client:
        try:
            response = await client.get(f"{API_BASE_URL}/health")
            if response.status_code != 200:
                print("❌ 服务器健康检查失败")
                return
        except:
            print("❌ 无法连接到服务器")
            return
    
    print("✅ 服务器运行中")
    
    # 运行各项分析
    await analyze_slow_apis()
    await stress_test_concurrent()
    await analyze_kline_performance()
    await check_blocking_operations()
    await analyze_database_queries()
    
    print("\n" + "=" * 60)
    print("✅ 性能分析完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
