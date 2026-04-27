"""快速测试API响应时间"""
import requests
import time

def test_api(url, name):
    try:
        start = time.time()
        r = requests.get(url, timeout=5)
        duration = time.time() - start
        print(f"{name}:")
        print(f"  Status: {r.status_code}")
        print(f"  Time: {duration:.2f}s")
        print(f"  Size: {len(r.content)} bytes")
        
        if r.status_code == 200:
            data = r.json()
            if 'sectors' in data:
                print(f"  Sectors: {len(data.get('sectors', []))}")
            elif 'dates' in data:
                print(f"  Dates: {len(data.get('dates', []))}")
        
        return duration
    except Exception as e:
        print(f"{name}: ERROR - {str(e)}")
        return 999

print("=" * 60)
print("API Response Time Test")
print("=" * 60)

print("\n1. Testing Holdings API...")
t1 = test_api("http://localhost:8000/api/holdings/", "Holdings")

print("\n2. Testing Watchlist Summary API...")
t2 = test_api("http://localhost:8000/api/daily-watchlist/summary?limit=10", "Watchlist")

print("\n3. Testing Indices Quotes API...")
t3 = test_api("http://localhost:8000/api/stocks/indices/quotes", "Indices")

print("\n" + "=" * 60)
print("Summary:")
print("=" * 60)
if t1 < 1.0 and t2 < 1.0 and t3 < 1.0:
    print("[OK] All APIs respond in < 1s")
else:
    print("[WARN] Some APIs are slow:")
    if t1 >= 1.0:
        print(f"  - Holdings: {t1:.2f}s")
    if t2 >= 1.0:
        print(f"  - Watchlist: {t2:.2f}s")
    if t3 >= 1.0:
        print(f"  - Indices: {t3:.2f}s")
