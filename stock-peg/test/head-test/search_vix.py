
import httpx
import asyncio
import certifi

async def search_vix():
    url = "https://searchapi.eastmoney.com/api/suggest/get"
    params = {
        "input": "VIX",
        "type": "14", # 美股
        "count": "5"
    }
    async with httpx.AsyncClient(verify=certifi.where()) as client:
        response = await client.get(url, params=params)
        print(response.json())

if __name__ == "__main__":
    asyncio.run(search_vix())
