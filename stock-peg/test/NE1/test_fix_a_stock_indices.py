"""
测试修复方案：A股指数获取
测试目标：
1. 验证代码格式转换
2. 验证Akshare数据获取
3. 验证数据库查询
"""
import asyncio
import sys
import os
import logging
from datetime import datetime

# Windows控制台编码设置
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def normalize_index_code(code: str) -> dict:
    """
    标准化指数代码格式
    
    支持的输入格式:
    - "000001.SH" (带后缀，前端传递格式)
    - "sh000001" (带前缀)
    - "000001" (纯代码)
    
    返回: {
        'pure_code': '000001',      # 纯代码
        'market': 'sh',              # 市场（sh/sz）
        'akshare_code': 'sh000001', # Akshare格式
        'tencent_code': 'sh000001', # 腾讯API格式
        'original': '000001.SH'     # 原始代码
    }
    """
    result = {
        'pure_code': None,
        'market': None,
        'akshare_code': None,
        'tencent_code': None,
        'original': code
    }
    
    if '.' in code:
        # 格式: 000001.SH
        pure_code, suffix = code.split('.')
        market = suffix.lower()
    elif code.startswith(('sh', 'sz')):
        # 格式: sh000001
        market = code[:2]
        pure_code = code[2:]
    else:
        # 纯代码: 000001
        pure_code = code
        # 根据代码判断市场
        # 000xxx, 510xxx, 688xxx -> sh
        # 399xxx -> sz
        if code.startswith(('0', '5', '6')):
            market = 'sh'
        else:
            market = 'sz'
    
    result['pure_code'] = pure_code
    result['market'] = market
    result['akshare_code'] = f"{market}{pure_code}"
    result['tencent_code'] = f"{market}{pure_code}"
    
    return result


async def test_code_conversion():
    """测试1: 代码格式转换"""
    print("\n" + "=" * 80)
    print("测试1: 指数代码格式转换")
    print("=" * 80)
    
    test_cases = [
        ('000001.SH', '上证指数'),
        ('399001.SZ', '深证成指'),
        ('000016.SH', '上证50'),
        ('399006.SZ', '创业板指'),
        ('000905.SH', '中证500'),
        ('sh000001', '上证指数(前缀)'),
        ('000001', '上证指数(纯代码)'),
    ]
    
    print("\n转换结果:")
    for code, name in test_cases:
        result = normalize_index_code(code)
        print(f"\n  {name} ({code}):")
        print(f"    纯代码: {result['pure_code']}")
        print(f"    市场: {result['market']}")
        print(f"    Akshare格式: {result['akshare_code']}")
        print(f"    腾讯API格式: {result['tencent_code']}")


async def test_akshare_fetch():
    """测试2: Akshare数据获取"""
    print("\n" + "=" * 80)
    print("测试2: Akshare数据获取")
    print("=" * 80)
    
    try:
        import akshare as ak
        
        print("\n【步骤1】获取所有A股指数实时行情...")
        
        # Akshare获取指数行情
        df = ak.stock_zh_index_spot_em()
        
        print(f"✓ 成功获取 {len(df)} 个指数")
        
        # 测试查找特定指数
        test_indices = [
            ('000001', '上证指数'),
            ('399001', '深证成指'),
            ('000016', '上证50'),
            ('399006', '创业板指'),
            ('000905', '中证500'),
        ]
        
        print("\n【步骤2】查找特定指数数据:")
        for code, name in test_indices:
            # 使用纯代码查找
            index_data = df[df['代码'] == code]
            
            if not index_data.empty:
                row = index_data.iloc[0]
                print(f"\n  ✓ {name} ({code}):")
                print(f"    名称: {row['名称']}")
                print(f"    最新价: {row['最新价']}")
                print(f"    涨跌幅: {row['涨跌幅']}%")
                print(f"    成交额: {row['成交额']}")
            else:
                print(f"\n  ✗ {name} ({code}): 未找到")
        
        print("\n【步骤3】测试指数K线获取...")
        
        # 测试获取上证指数K线
        print("\n  获取上证指数(000001)最近5天K线:")
        
        # 方式1: 使用纯代码
        try:
            df_kline = ak.stock_zh_index_daily(symbol="sh000001")
            if not df_kline.empty:
                latest = df_kline.tail(5)
                print(f"    ✓ 方式1成功，获取{len(latest)}条数据")
                for _, row in latest.iterrows():
                    print(f"      {row['date']}: 收盘={row['close']}")
        except Exception as e:
            print(f"    ✗ 方式1失败: {str(e)}")
        
        # 方式2: 使用带前缀的代码
        try:
            df_kline = ak.stock_zh_index_daily(symbol="sh000001")
            if not df_kline.empty:
                latest = df_kline.tail(5)
                print(f"    ✓ 方式2成功，获取{len(latest)}条数据")
        except Exception as e:
            print(f"    ✗ 方式2失败: {str(e)}")
            
    except ImportError:
        print("✗ Akshare未安装")
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_database_query():
    """测试3: 数据库查询A股指数"""
    print("\n" + "=" * 80)
    print("测试3: 数据库A股指数查询")
    print("=" * 80)
    
    from backend.database.session import async_session_maker
    from sqlalchemy import text
    
    async with async_session_maker() as session:
        # 检查stock_kline_data表是否有指数数据
        print("\n【步骤1】检查stock_kline_data表...")
        
        result = await session.execute(text(
            "SELECT COUNT(*) FROM stock_kline_data WHERE code IN ('000001', '399001', '000016', '399006', '000905')"
        ))
        count = result.scalar()
        print(f"  指数K线记录数: {count}")
        
        if count > 0:
            # 获取最新数据
            result = await session.execute(text(
                "SELECT code, date, close FROM stock_kline_data "
                "WHERE code IN ('000001', '399001', '000016', '399006', '000905') "
                "ORDER BY code, date DESC LIMIT 5"
            ))
            rows = result.fetchall()
            
            print("\n  最新数据:")
            for row in rows:
                print(f"    {row[0]}: {row[1]} 收盘={row[2]}")
        
        # 检查stock_realtime_quote表
        print("\n【步骤2】检查stock_realtime_quote表...")
        
        result = await session.execute(text(
            "SELECT COUNT(*) FROM stock_realtime_quote WHERE code IN ('000001', '399001', '000016', '399006', '000905')"
        ))
        count = result.scalar()
        print(f"  指数实时行情记录数: {count}")


async def test_integration():
    """测试4: 完整集成测试"""
    print("\n" + "=" * 80)
    print("测试4: 完整集成测试（模拟API调用）")
    print("=" * 80)
    
    # 模拟前端传递的代码列表
    frontend_codes = ['000001.SH', '399001.SZ', '000016.SH', '399006.SZ', '000905.SH']
    
    print(f"\n前端传递的代码: {frontend_codes}")
    
    # 步骤1: 转换代码格式
    print("\n【步骤1】转换代码格式...")
    
    converted_codes = []
    for code in frontend_codes:
        normalized = normalize_index_code(code)
        converted_codes.append(normalized)
        print(f"  {code} -> {normalized['akshare_code']} (Akshare)")
    
    # 步骤2: 从Akshare获取数据
    print("\n【步骤2】从Akshare获取实时数据...")
    
    try:
        import akshare as ak
        
        # 获取所有指数行情
        df = ak.stock_zh_index_spot_em()
        
        results = []
        for item in converted_codes:
            pure_code = item['pure_code']
            
            # 查找对应指数
            index_data = df[df['代码'] == pure_code]
            
            if not index_data.empty:
                row = index_data.iloc[0]
                results.append({
                    'code': item['original'],
                    'pure_code': pure_code,
                    'name': row['名称'],
                    'price': float(row['最新价']),
                    'change_pct': float(row['涨跌幅']),
                    'volume': int(row['成交量']),
                    'amount': float(row['成交额'])
                })
                print(f"  ✓ {row['名称']}: {row['最新价']} ({row['涨跌幅']}%)")
            else:
                print(f"  ✗ {item['original']}: 未找到")
        
        print(f"\n✓ 成功获取 {len(results)}/{len(frontend_codes)} 个指数")
        
        # 步骤3: 模拟返回给前端的数据格式
        print("\n【步骤3】模拟返回数据...")
        
        response_data = {
            'success': True,
            'data': results,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"  返回数据条数: {len(results)}")
        print(f"  时间戳: {response_data['timestamp']}")
        
    except Exception as e:
        print(f"  ✗ 失败: {str(e)}")


async def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("A股指数获取修复方案测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    try:
        # 测试1: 代码格式转换
        await test_code_conversion()
        
        # 测试2: Akshare数据获取
        await test_akshare_fetch()
        
        # 测试3: 数据库查询
        await test_database_query()
        
        # 测试4: 完整集成
        await test_integration()
        
        print("\n" + "=" * 80)
        print("✓ 所有测试完成")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
