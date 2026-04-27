
import httpx
import asyncio
import certifi

async def test_vix_direct():
    url = "https://push2.eastmoney.com/api/qt/stock/get"
    params = {
        "secid": "100.VIX",
        "fields": "f2,f3,f4,f5,f6,f12,f13,f14,f15,f16,f17,f18"
    }
    async with httpx.AsyncClient(verify=certifi.where()) as client:
        response = await client.get(url, params=params)
        print(f"100.VIX: {response.json()}")
        
        # Try 100.SPX too
        params["secid"] = "100.SPX"
        response = await client.get(url, params=params)
        print(f"100.SPX: {response.json()}")

if __name__ == "__main__":
    asyncio.run(test_vix_direct())
