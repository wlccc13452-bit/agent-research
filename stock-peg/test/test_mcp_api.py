"""MCP API 测试脚本"""
import httpx
import asyncio
from datetime import date
import json
import sys
import io

# 修复Windows控制台编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_URL = "http://localhost:8000/api/mcp"


async def test_mcp_apis():
    """测试所有MCP API接口"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        print("=" * 60)
        print("开始测试MCP API接口")
        print("=" * 60)
        
        # ========== Holdings Tests ==========
        print("\n【1. Holdings API测试】")
        
        # 1.1 添加板块
        print("\n1.1 添加板块 '测试板块'...")
        response = await client.post(
            f"{BASE_URL}/holdings/add-sector",
            json={"sector_name": "测试板块"}
        )
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        
        # 1.2 添加股票到板块
        print("\n1.2 添加股票 '平安银行' 到 '测试板块'...")
        response = await client.post(
            f"{BASE_URL}/holdings/add-stock",
            json={
                "sector": "测试板块",
                "stock_name": "平安银行",
                "stock_code": "000001.SZ"
            }
        )
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        
        # 1.3 列出持仓
        print("\n1.3 获取持仓列表...")
        response = await client.get(f"{BASE_URL}/holdings/list")
        print(f"   状态码: {response.status_code}")
        data = response.json()
        print(f"   响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        # 1.4 重命名板块
        print("\n1.4 重命名板块 '测试板块' -> '临时板块'...")
        response = await client.put(
            f"{BASE_URL}/holdings/rename-sector",
            json={
                "old_name": "测试板块",
                "new_name": "临时板块"
            }
        )
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        
        # 1.5 删除股票
        print("\n1.5 从 '临时板块' 删除股票 '平安银行'...")
        response = await client.post(
            f"{BASE_URL}/holdings/remove-stock",
            json={
                "sector": "临时板块",
                "stock_name": "平安银行"
            }
        )
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        
        # 1.6 删除板块
        print("\n1.6 删除板块 '临时板块'...")
        response = await client.delete(f"{BASE_URL}/holdings/remove-sector/临时板块")
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        
        # ========== Watchlist Tests ==========
        print("\n\n【2. Watchlist API测试】")
        
        today = date.today().isoformat()
        
        # 2.1 添加股票到关注列表
        print(f"\n2.1 添加股票 '招商银行' 到关注列表 ({today})...")
        response = await client.post(
            f"{BASE_URL}/watchlist/add-stock",
            json={
                "stock_name": "招商银行",
                "watch_date": today,
                "reason": "MCP测试添加",
                "target_price": 35.0,
                "stop_loss_price": 30.0,
                "notes": "测试MCP接口"
            }
        )
        print(f"   状态码: {response.status_code}")
        result = response.json()
        print(f"   响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        stock_id = result.get("stock_id")
        
        # 2.2 获取关注列表
        print("\n2.2 获取所有关注列表...")
        response = await client.get(f"{BASE_URL}/watchlist/list")
        print(f"   状态码: {response.status_code}")
        data = response.json()
        print(f"   响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        # 2.3 按日期获取关注列表
        print(f"\n2.3 获取 {today} 的关注列表...")
        response = await client.get(f"{BASE_URL}/watchlist/get-by-date/{today}")
        print(f"   状态码: {response.status_code}")
        data = response.json()
        print(f"   响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        if stock_id:
            # 2.4 归档股票
            print(f"\n2.4 归档股票 ID={stock_id}...")
            response = await client.post(
                f"{BASE_URL}/watchlist/archive",
                json={"stock_id": stock_id}
            )
            print(f"   状态码: {response.status_code}")
            print(f"   响应: {response.json()}")
            
            # 2.5 取消归档
            print(f"\n2.5 取消归档股票 ID={stock_id}...")
            response = await client.post(
                f"{BASE_URL}/watchlist/unarchive",
                json={"stock_id": stock_id}
            )
            print(f"   状态码: {response.status_code}")
            print(f"   响应: {response.json()}")
            
            # 2.6 删除股票
            print(f"\n2.6 删除关注股票 ID={stock_id}...")
            response = await client.post(
                f"{BASE_URL}/watchlist/remove-stock",
                json={"stock_id": stock_id}
            )
            print(f"   状态码: {response.status_code}")
            print(f"   响应: {response.json()}")
        
        # 2.7 按日期删除
        print(f"\n2.7 按日期删除关注列表 ({today})...")
        response = await client.post(
            f"{BASE_URL}/watchlist/remove-by-date",
            json={"watch_date": today}
        )
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.json()}")
        
        print("\n" + "=" * 60)
        print("✅ MCP API测试完成")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_mcp_apis())
