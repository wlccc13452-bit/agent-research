import asyncio
import httpx
import certifi

async def test_eastmoney_indices():
    symbol_map = {
        '^GSPC': '100.SPX',    # 标普500 (注意：是SPX不是GSPC)
        '^IXIC': '100.NDX',    # 纳斯达克
        '^DJI': '100.DJIA',    # 道琼斯 (注意：是DJIA不是DJI)
        '^VIX': '100.VIX'      # VIX恐慌指数
    }
    
    client = httpx.AsyncClient(timeout=15.0, verify=certifi.where())
    
    for symbol, secid in symbol_map.items():
        print(f"Testing {symbol} ({secid})...")
        url = "https://push2.eastmoney.com/api/qt/ulist.np/get"
        params = {
            "fltt": 2,
            "invt": 2,
            "fields": "f2,f3,f4,f5,f6,f12,f13,f14,f15,f16,f17,f18",
            "secids": secid
        }
        
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            print(f"Response for {symbol}: {data}")
            
            if data and data.get('data') and data['data'].get('diff'):
                diff = data['data']['diff']
                if diff and len(diff) > 0:
                    item = diff[0]
                    print(f"Success! {symbol} price: {item.get('f2')}, change_pct: {item.get('f3')}")
                else:
                    print(f"Failed! No diff for {symbol}")
            else:
                print(f"Failed! No data for {symbol}")
        except Exception as e:
            print(f"Error for {symbol}: {e}")
            
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(test_eastmoney_indices())
