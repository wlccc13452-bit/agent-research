"""
测试腾讯K线API对板块代码（BK开头）的支持情况
诊断 "param error" 问题
"""
import asyncio
import aiohttp
import json
from datetime import datetime

async def test_tencent_kline_api():
    """测试不同的参数格式"""
    
    # 测试的板块代码
    test_codes = ["BK0727", "BK0428", "BK0477", "BK0493", "BK0451"]
    
    # 测试用例
    test_cases = [
        # (描述, 代码格式, 是否加qfq)
        ("小写bk，不加qfq", "bk0727", False),
        ("小写bk，加qfq", "bk0727", True),
        ("大写BK，不加qfq", "BK0727", False),
        ("大写BK，加qfq", "BK0727", True),
        ("纯数字，不加qfq", "0727", False),
        ("前缀mk，不加qfq", "mk0727", False),
    ]
    
    url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
    
    async with aiohttp.ClientSession() as session:
        for desc, code, use_qfq in test_cases:
            print(f"\n{'='*60}")
            print(f"测试: {desc}")
            print(f"代码: {code}, qfq: {use_qfq}")
            
            # 构造参数
            api_param = f"{code},day,,,50"
            if use_qfq:
                api_param += ",qfq"
            
            var_name = f"kline_day"
            if use_qfq:
                var_name += "qfq"
            
            params = {
                "_var": var_name,
                "param": api_param,
                "r": int(datetime.now().timestamp() * 1000)
            }
            
            print(f"请求参数: {params}")
            
            try:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    text = await response.text()
                    
                    # 解析JSON
                    if '=' in text:
                        json_str = text.split('=', 1)[1]
                        data = json.loads(json_str)
                    else:
                        data = json.loads(text)
                    
                    print(f"\n响应状态码: {response.status}")
                    print(f"响应数据: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
                    
                    # 检查是否成功
                    if data.get('data'):
                        print(f"✅ 成功获取数据!")
                        if isinstance(data['data'], dict):
                            print(f"数据键: {list(data['data'].keys())}")
                    else:
                        print(f"❌ 获取失败: code={data.get('code')}, msg={data.get('msg')}")
                        
            except Exception as e:
                print(f"❌ 请求异常: {str(e)}")
            
            # 延迟避免请求过快
            await asyncio.sleep(0.5)
    
    # 测试股票代码作为对比
    print(f"\n{'='*60}")
    print("测试普通股票代码（作为对比）")
    print(f"{'='*60}")
    
    stock_cases = [
        ("小写sh600000，加qfq", "sh600000", True),
        ("小写sz000001，加qfq", "sz000001", True),
    ]
    
    for desc, code, use_qfq in stock_cases:
        print(f"\n测试: {desc}")
        
        api_param = f"{code},day,,,50"
        if use_qfq:
            api_param += ",qfq"
        
        params = {
            "_var": "kline_dayqfq" if use_qfq else "kline_day",
            "param": api_param,
            "r": int(datetime.now().timestamp() * 1000)
        }
        
        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                text = await response.text()
                
                if '=' in text:
                    json_str = text.split('=', 1)[1]
                    data = json.loads(json_str)
                else:
                    data = json.loads(text)
                
                if data.get('data'):
                    print(f"✅ 成功获取股票数据!")
                    if isinstance(data['data'], dict):
                        print(f"数据键: {list(data['data'].keys())}")
                else:
                    print(f"❌ 获取失败: {data.get('msg')}")
                    
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")
        
        await asyncio.sleep(0.5)


async def test_tencent_quote_api():
    """测试腾讯行情API对板块代码的支持"""
    print(f"\n{'='*60}")
    print("测试腾讯行情API（不是K线API）")
    print(f"{'='*60}")
    
    # 行情API可能有不同的端点
    test_codes = ["BK0727", "bk0727", "sh600000"]
    
    url = "https://web.sqt.gtimg.cn/q="  # 行情API
    
    async with aiohttp.ClientSession() as session:
        for code in test_codes:
            print(f"\n测试代码: {code}")
            
            # 腾讯行情API格式
            full_code = code.lower()
            params_str = f"{full_code}"
            
            try:
                async with session.get(url + params_str, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    text = await response.text()
                    print(f"响应: {text[:200]}")
            except Exception as e:
                print(f"异常: {str(e)}")
            
            await asyncio.sleep(0.5)


if __name__ == "__main__":
    print("开始测试腾讯K线API对板块代码的支持...")
    asyncio.run(test_tencent_kline_api())
    # asyncio.run(test_tencent_quote_api())
