
import httpx
import asyncio
import certifi

async def list_us_indices():
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": 1,
        "pz": 50,
        "po": 1,
        "np": 1,
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": 2,
        "invt": 2,
        "fid": "f3",
        "fs": "m:100",
        "fields": "f1,f2,f3,f4,f12,f13,f14"
    }
    async with httpx.AsyncClient(verify=certifi.where()) as client:
        response = await client.get(url, params=params)
        data = response.json()
        if data and data.get('data') and data['data'].get('diff'):
            for item in data['data']['diff']:
                print(f"Code: {item.get('f12')}, Name: {item.get('f14')}, ID: {item.get('f13')}.{item.get('f12')}")

if __name__ == "__main__":
    asyncio.run(list_us_indices())
