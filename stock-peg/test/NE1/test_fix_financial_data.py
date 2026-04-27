"""
测试修复方案：股票财务数据获取
测试目标：
1. 验证财务数据数据库查询
2. 验证Tushare数据获取
3. 验证Akshare数据获取（备用）
4. 验证财务数据完整性
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

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# 创建数据库引擎
DATABASE_URL = "sqlite+aiosqlite:///d:/play-ground/股票研究/stock-peg/backend/data/stock_peg.db"
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_financial_database():
    """测试1: 验证财务数据数据库查询"""
    print("\n" + "=" * 80)
    print("测试1: 财务数据数据库查询验证")
    print("=" * 80)
    
    async with async_session_maker() as session:
        # 检查表是否存在
        print("\n【步骤1】检查财务数据表...")
        
        result = await session.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name IN ('fundamental_metrics', 'financial_history')"
        ))
        tables = [row[0] for row in result.fetchall()]
        
        print(f"✓ 找到表: {', '.join(tables)}")
        
        # 检查数据量
        print("\n【步骤2】检查数据量...")
        
        result = await session.execute(text(
            "SELECT COUNT(*) FROM fundamental_metrics"
        ))
        count = result.scalar()
        print(f"✓ fundamental_metrics 记录数: {count}")
        
        result = await session.execute(text(
            "SELECT COUNT(*) FROM financial_history"
        ))
        count = result.scalar()
        print(f"✓ financial_history 记录数: {count}")
        
        # 测试查询特定股票的财务数据
        print("\n【步骤3】查询测试股票财务数据...")
        
        test_stocks = ['600519', '000001', '601318']  # 茅台、平安、平安银行
        
        for stock_code in test_stocks:
            print(f"\n  --- {stock_code} ---")
            
            # 查询fundamental_metrics表
            result = await session.execute(text(
                "SELECT stock_code, valuation, growth, financial_health, "
                "overall_score, updated_at "
                "FROM fundamental_metrics "
                "WHERE stock_code = :code "
                "ORDER BY updated_at DESC LIMIT 1"
            ), {"code": stock_code})
            
            row = result.fetchone()
            
            if row:
                print(f"    ✓ 找到数据:")
                print(f"      股票代码: {row[0]}")
                print(f"      估值指标: {row[1]}")
                print(f"      成长指标: {row[2]}")
                print(f"      财务健康: {row[3]}")
                print(f"      综合评分: {row[4]}")
                print(f"      更新时间: {row[5]}")
            else:
                print(f"    ✗ 未找到数据")
        
        # 检查财务历史数据
        print("\n【步骤4】检查财务历史数据...")
        
        result = await session.execute(text(
            "SELECT stock_code, report_date, revenue, net_profit, "
            "basic_eps, roe, pe_ratio "
            "FROM financial_history "
            "WHERE stock_code = '600519' "
            "ORDER BY report_date DESC LIMIT 3"
        ))
        
        rows = result.fetchall()
        
        if rows:
            print(f"  ✓ 茅台(600519)最近3期财务数据:")
            for row in rows:
                print(f"    {row[1]}: 营收={row[2]}, 净利润={row[3]}, PE={row[6]}")
        else:
            print(f"  ✗ 未找到历史数据")


async def test_tushare_fetch():
    """测试2: 验证Tushare数据获取"""
    print("\n" + "=" * 80)
    print("测试2: Tushare数据获取验证")
    print("=" * 80)
    
    try:
        import tushare as ts
        
        # 读取配置
        print("\n【步骤1】检查Tushare配置...")
        
        import os
        from pathlib import Path
        
        env_path = Path(__file__).parent.parent.parent / "backend" / ".env"
        tushare_token = None
        
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    if line.startswith('TUSHARE_TOKEN='):
                        tushare_token = line.strip().split('=')[1]
                        break
        
        if tushare_token:
            print(f"✓ Tushare Token: {tushare_token[:10]}...")
            
            # 初始化Tushare
            pro = ts.pro_api(tushare_token)
            
            # 测试获取财务数据
            print("\n【步骤2】测试获取财务指标...")
            
            test_code = '600519.SH'  # 茅台
            
            try:
                # 获取每日基本面指标
                df = pro.daily_basic(ts_code=test_code, fields='ts_code,trade_date,pe,pb,roe')
                
                if not df.empty:
                    print(f"✓ 成功获取数据，共{len(df)}条")
                    print(f"  最新数据:")
                    latest = df.iloc[0]
                    print(f"    日期: {latest['trade_date']}")
                    print(f"    PE: {latest['pe']}")
                    print(f"    PB: {latest['pb']}")
                    print(f"    ROE: {latest['roe']}")
                else:
                    print(f"✗ 未获取到数据")
                    
            except Exception as e:
                error_msg = str(e)
                if "没有接口访问权限" in error_msg:
                    print(f"✗ Tushare接口无权限: {error_msg}")
                else:
                    print(f"✗ 获取失败: {error_msg}")
            
            # 测试获取财报数据
            print("\n【步骤3】测试获取财报数据...")
            
            try:
                df = pro.income(ts_code=test_code, fields='ts_code,ann_date,f_ann_date,revenue,n_income')
                
                if not df.empty:
                    print(f"✓ 成功获取利润表数据，共{len(df)}条")
                    print(f"  最新数据:")
                    latest = df.iloc[0]
                    print(f"    公告日期: {latest['ann_date']}")
                    print(f"    营收: {latest['revenue']}")
                    print(f"    净利润: {latest['n_income']}")
                else:
                    print(f"✗ 未获取到数据")
                    
            except Exception as e:
                error_msg = str(e)
                if "没有接口访问权限" in error_msg:
                    print(f"✗ Tushare接口无权限: {error_msg}")
                else:
                    print(f"✗ 获取失败: {error_msg}")
        else:
            print(f"✗ 未找到Tushare Token配置")
            
    except ImportError:
        print("✗ Tushare未安装")
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_akshare_fetch():
    """测试3: 验证Akshare财务数据获取"""
    print("\n" + "=" * 80)
    print("测试3: Akshare财务数据获取验证")
    print("=" * 80)
    
    try:
        import akshare as ak
        
        test_code = '600519'  # 茅台
        
        # 测试获取财务指标
        print("\n【步骤1】测试获取财务指标...")
        
        try:
            df = ak.stock_financial_analysis_indicator(symbol=test_code)
            
            if not df.empty:
                print(f"✓ 成功获取数据，共{len(df)}条")
                print(f"  最新数据:")
                latest = df.iloc[0]
                print(f"    列名: {list(df.columns)[:10]}")  # 显示前10列
                
                # 尝试获取PE、PB等指标
                for col in ['市盈率', 'PE(TTM)', 'pe_ttm', '市盈(TTM)']:
                    if col in latest.index:
                        print(f"    PE: {latest[col]}")
                        break
                
                for col in ['市净率', 'PB', 'pb']:
                    if col in latest.index:
                        print(f"    PB: {latest[col]}")
                        break
                        
                for col in ['净资产收益率', 'ROE', 'roe']:
                    if col in latest.index:
                        print(f"    ROE: {latest[col]}")
                        break
            else:
                print(f"✗ 未获取到数据")
                
        except Exception as e:
            print(f"✗ 获取失败: {str(e)}")
        
        # 测试获取资产负债表
        print("\n【步骤2】测试获取资产负债表...")
        
        try:
            df = ak.stock_balance_sheet_by_report_em(symbol=test_code)
            
            if not df.empty:
                print(f"✓ 成功获取数据，共{len(df)}条")
                print(f"  最新数据:")
                latest = df.iloc[0]
                
                # 尝试获取关键指标
                if '资产总计' in latest.index:
                    print(f"    总资产: {latest['资产总计']}")
                if '负债合计' in latest.index:
                    print(f"    总负债: {latest['负债合计']}")
                if '所有者权益合计' in latest.index:
                    print(f"    股东权益: {latest['所有者权益合计']}")
            else:
                print(f"✗ 未获取到数据")
                
        except Exception as e:
            print(f"✗ 获取失败: {str(e)}")
        
        # 测试获取利润表
        print("\n【步骤3】测试获取利润表...")
        
        try:
            df = ak.stock_profit_sheet_by_report_em(symbol=test_code)
            
            if not df.empty:
                print(f"✓ 成功获取数据，共{len(df)}条")
                print(f"  最新数据:")
                latest = df.iloc[0]
                
                # 尝试获取关键指标
                if '营业总收入' in latest.index:
                    print(f"    营业收入: {latest['营业总收入']}")
                if '净利润' in latest.index:
                    print(f"    净利润: {latest['净利润']}")
            else:
                print(f"✗ 未获取到数据")
                
        except Exception as e:
            print(f"✗ 获取失败: {str(e)}")
            
    except ImportError:
        print("✗ Akshare未安装")
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_financial_completeness():
    """测试4: 验证财务数据完整性"""
    print("\n" + "=" * 80)
    print("测试4: 财务数据完整性验证")
    print("=" * 80)
    
    async with async_session_maker() as session:
        # 统计有财务数据的股票数量
        print("\n【步骤1】统计财务数据覆盖情况...")
        
        result = await session.execute(text(
            "SELECT COUNT(DISTINCT stock_code) FROM fundamental_metrics"
        ))
        count = result.scalar()
        print(f"✓ 有财务指标数据的股票数: {count}")
        
        result = await session.execute(text(
            "SELECT COUNT(DISTINCT stock_code) FROM financial_history"
        ))
        count = result.scalar()
        print(f"✓ 有财务历史数据的股票数: {count}")
        
        # 检查数据的时效性
        print("\n【步骤2】检查数据时效性...")
        
        result = await session.execute(text(
            "SELECT MIN(updated_at) as oldest, MAX(updated_at) as newest "
            "FROM fundamental_metrics"
        ))
        row = result.fetchone()
        
        if row:
            print(f"  最早更新时间: {row[0]}")
            print(f"  最新更新时间: {row[1]}")
        
        # 检查数据质量
        print("\n【步骤3】检查数据质量...")
        
        # 统计有PE数据的股票数
        result = await session.execute(text(
            "SELECT COUNT(*) FROM fundamental_metrics "
            "WHERE valuation IS NOT NULL AND valuation != ''"
        ))
        count = result.scalar()
        print(f"  有估值指标的股票数: {count}")
        
        # 统计有成长指标的股票数
        result = await session.execute(text(
            "SELECT COUNT(*) FROM fundamental_metrics "
            "WHERE growth IS NOT NULL AND growth != ''"
        ))
        count = result.scalar()
        print(f"  有成长指标的股票数: {count}")
        
        # 统计有财务健康指标的股票数
        result = await session.execute(text(
            "SELECT COUNT(*) FROM fundamental_metrics "
            "WHERE financial_health IS NOT NULL AND financial_health != ''"
        ))
        count = result.scalar()
        print(f"  有财务健康指标的股票数: {count}")


async def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("股票财务数据获取修复方案测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    try:
        # 测试1: 数据库查询
        await test_financial_database()
        
        # 测试2: Tushare获取
        await test_tushare_fetch()
        
        # 测试3: Akshare获取
        await test_akshare_fetch()
        
        # 测试4: 数据完整性
        await test_financial_completeness()
        
        print("\n" + "=" * 80)
        print("✓ 所有测试完成")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
