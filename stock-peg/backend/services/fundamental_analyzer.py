"""基本面财务分析服务"""
import logging
import asyncio
import random
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from types import SimpleNamespace
import numpy as np
import pandas as pd

from database.session import async_session_maker
from datasource import get_datasource, DataSourceType
from services.markdown_profile_loader import get_profile_loader
from database.operations import (
    save_fundamental_metrics,
    save_financial_history,
    get_fundamental_metrics as ops_get_fundamental_metrics,
    get_latest_financial_report,
    get_financial_history,
)

logger = logging.getLogger(__name__)


class FundamentalAnalyzer:
    """基本面财务分析器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FundamentalAnalyzer, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # 通过 datasource 获取数据源
        manager = get_datasource()
        tushare_source = manager.get_source(DataSourceType.TUSHARE)
        akshare_source = manager.get_source(DataSourceType.AKSHARE)
        
        self.ts_pro = tushare_source if tushare_source else None
        self.akshare_source = akshare_source if akshare_source else None
        
        if not self.ts_pro:
            if self.akshare_source:
                logger.info("未配置 Tushare Token,已启用 Akshare 作为备用数据源")
            else:
                logger.warning("未配置 Tushare Token,部分财务数据将无法获取")
        
        # 初始化 Markdown Profile Loader
        self.profile_loader = get_profile_loader()
        logger.info("Markdown Profile Loader 已初始化")
        
        # 记录无权限的 Tushare 接口,避免重复请求
        self._unauthorized_apis = set()
        
        self._initialized = True

    async def _call_tushare(self, api_name: str, **kwargs) -> pd.DataFrame:
        """调用 Tushare API（通过 datasource 层）"""
        if not self.ts_pro:
            return pd.DataFrame()
        
        if api_name in self._unauthorized_apis:
            return pd.DataFrame()
        
        try:
            # 使用 TushareDataSource 的 call_tushare_api 方法
            df = self.ts_pro.call_tushare_api(api_name, **kwargs)
            return df
        except Exception as e:
            error_msg = str(e)
            if "没有接口访问权限" in error_msg:
                if api_name not in self._unauthorized_apis:
                    logger.warning(f"Tushare 接口 [{api_name}] 无权限，后续将自动跳过此接口请求。权限详情: {error_msg}")
                    self._unauthorized_apis.add(api_name)
                return pd.DataFrame()
            
            logger.error(f"调用 Tushare 接口 [{api_name}] 失败: {error_msg}")
            raise e
    
    async def analyze_fundamental(self, stock_code: str) -> Optional[Dict]:
        """
        综合基本面分析（带缓存优化）
        
        Args:
            stock_code: 股票代码
            
        Returns:
            基本面分析结果
        """
        try:
            # [START] 性能优化：优先从缓存获取
            from services.extended_cache import financial_analysis_cache
            
            cached_analysis = await financial_analysis_cache.get(stock_code)
            if cached_analysis:
                logger.info(f"⚡ 从缓存获取财务分析: {stock_code}")
                return cached_analysis
            
            # 缓存未命中，执行分析
            logger.info(f"[CHART] 执行财务分析: {stock_code}")
            
            # 1. 估值指标分析
            valuation = await self.analyze_valuation(stock_code)
            
            # 2. 成长性分析
            growth = await self.analyze_growth(stock_code)
            
            # 3. 财务健康度分析
            financial_health = await self.analyze_financial_health(stock_code)
            
            # 4. 市场趋势分析
            market_trend = await self.analyze_market_trend(stock_code)
            
            # 5. 计算综合评分
            overall_score = self._calculate_overall_score(
                valuation, growth, financial_health, market_trend
            )
            
            # 6. 生成投资建议
            recommendation = self._generate_recommendation(
                valuation, growth, financial_health, market_trend, overall_score
            )
            
            # 7. 保存到数据库
            await self._save_metrics(
                stock_code, valuation, growth, 
                financial_health, market_trend, overall_score
            )
            
            result = {
                'stock_code': stock_code,
                'valuation': valuation,
                'growth': growth,
                'financial_health': financial_health,
                'market_trend': market_trend,
                'overall_score': overall_score,
                'recommendation': recommendation,
                'timestamp': datetime.now()
            }
            
            # [START] 存入缓存
            await financial_analysis_cache.set(result, stock_code)
            logger.info(f"[OK] 财务分析已缓存: {stock_code}")
            
            return result
            
        except Exception as e:
            logger.error(f"基本面分析失败 {stock_code}: {str(e)}")
            return None
    
    async def analyze_valuation(self, stock_code: str) -> Dict:
        """估值指标分析"""
        try:
            # 优先尝试新浪财经接口(最可靠)
            if self.akshare_source:
                logger.info(f"使用新浪财经接口获取估值数据: {stock_code}")
                sina_income = await self.akshare_source.get_financial_report_sina(stock_code, '利润表')
                
                if sina_income and sina_income.get('data') is not None and not sina_income['data'].empty:
                    df = sina_income['data']
                    # 取最新一期数据
                    latest = df.iloc[0]
                    
                    # 尝试从利润表提取估值指标（虽然有限，但至少有营收和利润数据）
                    revenue = float(latest.get('营业总收入', 0)) if latest.get('营业总收入') else None
                    net_profit = float(latest.get('净利润', 0)) if latest.get('净利润') else None
                    
                    # 尝试获取个股信息（包含市值等）
                    try:
                        info_df = await self.akshare_source._call_akshare(
                            self.akshare_source._get_ak_module().stock_individual_info_em, symbol=stock_code
                        )
                        if not info_df.empty:
                            info_dict = dict(zip(info_df['item'], info_df['value']))
                            market_cap = info_dict.get('总市值')
                            circulation_market_cap = info_dict.get('流通市值')
                        else:
                            market_cap = None
                            circulation_market_cap = None
                    except:
                        market_cap = None
                        circulation_market_cap = None
                    
                    # 由于新浪接口没有PE、PB，我们从市值和净利润估算PE
                    pe_ttm = None
                    if market_cap and net_profit and net_profit > 0:
                        # 简化估算: PE = 总市值 / 年化净利润
                        # 注意：这里的数据是季度数据，需要年化
                        pe_ttm = market_cap / (net_profit * 4) if net_profit else None
                    
                    # 尝试获取 PB 和 PS
                    pb = None
                    ps_ttm = None
                    peg = None
                    
                    # 获取资产负债表
                    sina_balance = await self.akshare_source.get_financial_report_sina(stock_code, '资产负债表')
                    if sina_balance and sina_balance.get('data') is not None and not sina_balance['data'].empty:
                        balance_latest = sina_balance['data'].iloc[0]
                        total_equity = None
                        for col in ['所有者权益合计', '所有者权益(或股东权益)合计', '股东权益合计']:
                            if col in balance_latest.index and pd.notna(balance_latest.get(col)):
                                total_equity = float(balance_latest.get(col))
                                break
                        
                        if market_cap and total_equity and total_equity > 0:
                            pb = market_cap / total_equity
                    
                    # 计算 PS
                    if market_cap and revenue and revenue > 0:
                        # 营收也需要年化（这里是单季或累计，简化处理为 * 4 估算）
                        ps_ttm = market_cap / (revenue * 4)
                    
                    # 计算 PEG
                    if pe_ttm:
                        # 避免递归调用，我们单独尝试计算增长率
                        # 这里先尝试简单的，如果不成就保持 None
                        try:
                            growth_data = await self.analyze_growth(stock_code)
                            # analyze_growth 返回的是小数 (例如 0.15 表示 15%)
                            if growth_data and growth_data.get('profit_cagr_3y'):
                                growth_rate_pct = growth_data['profit_cagr_3y'] * 100
                                if growth_rate_pct > 0:
                                    peg = pe_ttm / growth_rate_pct
                        except:
                            pass

                    logger.info(f"股票 {stock_code} 从新浪财经获取到数据: 营收={revenue}, 净利润={net_profit}, 市值={market_cap}, PB={pb}, PS={ps_ttm}, PEG={peg}")
                    
                    return {
                        'pe_ttm': pe_ttm,
                        'pe_lyr': pe_ttm,
                        'pe_ratio': pe_ttm,  # 兼容前端字段名
                        'pb': pb,
                        'pb_ratio': pb,      # 兼容前端字段名
                        'ps_ttm': ps_ttm,
                        'ps_ratio': ps_ttm,  # 兼容前端字段名
                        'peg': peg,
                        'peg_ratio': peg,    # 兼容前端字段名
                        'market_cap': market_cap,
                        'circulation_market_cap': circulation_market_cap,
                        'valuation_level': self._evaluate_valuation(pe_ttm, pb, peg),
                        'score': self._score_valuation(pe_ttm, pb, peg)
                    }
            
            if not self.ts_pro:
                logger.warning(f"股票 {stock_code} 无法获取估值数据：Tushare 和 Akshare 均不可用")
                return {}
            
            # 构建股票代码
            ts_code = f"{stock_code}.SH" if stock_code.startswith('6') else f"{stock_code}.SZ"
            logger.info(f"正在获取股票 {stock_code} 的估值数据，ts_code={ts_code}")
            
            # 获取估值数据 (Tushare每日指标) - 获取最近一天的数据
            df = await self._call_tushare(
                'daily_basic',
                ts_code=ts_code,
                fields='trade_date,pe_ttm,pe,pb,ps_ttm,total_mv,circ_mv'
            )
            
            logger.info(f"Tushare daily_basic 返回数据行数: {len(df) if not df.empty else 0}")
            
            if df.empty:
                logger.warning(f"股票 {stock_code} 未找到估值数据，尝试 Akshare 备用方案")
                # 尝试 Akshare 备用方案
                if self.akshare_source is not None:
                    ak_data = await self.akshare_source.get_financial_indicator(stock_code)
                    if ak_data:
                        logger.info(f"从 Akshare 获取到估值数据: {ak_data}")
                        return {
                            'pe_ttm': ak_data.get('pe_ttm'),
                            'pe_lyr': ak_data.get('pe_ttm'),
                            'pe_ratio': ak_data.get('pe_ttm'),
                            'pb': ak_data.get('pb'),
                            'pb_ratio': ak_data.get('pb'),
                            'ps_ttm': None,
                            'ps_ratio': None,
                            'peg': None,
                            'peg_ratio': None,
                            'market_cap': None,
                            'circulation_market_cap': None,
                            'valuation_level': self._evaluate_valuation(ak_data.get('pe_ttm'), ak_data.get('pb'), None),
                            'score': self._score_valuation(ak_data.get('pe_ttm'), ak_data.get('pb'), None)
                        }
                return {}
            
            # 按交易日期排序，取最新的数据
            df = df.sort_values('trade_date', ascending=False)
            latest = df.iloc[0]
            logger.info(f"股票 {stock_code} 最新估值数据: PE={latest['pe_ttm']}, PB={latest['pb']}")
            
            # 计算PEG (需要盈利增长率)
            pe_ttm = float(latest['pe_ttm']) if pd.notna(latest['pe_ttm']) else None
            peg = None
            if pe_ttm:
                # 获取过去3年净利润增长率
                growth_rate = await self._get_profit_growth_rate(stock_code, 3)
                if growth_rate and growth_rate > 0:
                    peg = pe_ttm / (growth_rate * 100)
            
            # 估值评估
            valuation_level = self._evaluate_valuation(pe_ttm, latest['pb'], peg)
            
            result = {
                'pe_ttm': pe_ttm,
                'pe_lyr': float(latest['pe']) if pd.notna(latest['pe']) else None,
                'pe_ratio': pe_ttm,
                'pb': float(latest['pb']) if pd.notna(latest['pb']) else None,
                'pb_ratio': float(latest['pb']) if pd.notna(latest['pb']) else None,
                'ps_ttm': float(latest['ps_ttm']) if pd.notna(latest['ps_ttm']) else None,
                'ps_ratio': float(latest['ps_ttm']) if pd.notna(latest['ps_ttm']) else None,
                'peg': peg,
                'peg_ratio': peg,
                'market_cap': float(latest['total_mv']) if pd.notna(latest['total_mv']) else None,
                'circulation_market_cap': float(latest['circ_mv']) if pd.notna(latest['circ_mv']) else None,
                'valuation_level': valuation_level,  # 低估/合理/高估
                'score': self._score_valuation(pe_ttm, latest['pb'], peg)
            }
            
            logger.info(f"股票 {stock_code} 估值分析完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"估值分析失败 {stock_code}: {str(e)}", exc_info=True)
            # 尝试 Akshare 备用方案
            if self.akshare_source is not None:
                try:
                    ak_data = await self.akshare_source.get_financial_indicator(stock_code)
                    if ak_data:
                        return {
                            'pe_ttm': ak_data.get('pe_ttm'),
                            'pe_lyr': ak_data.get('pe_ttm'),
                            'pe_ratio': ak_data.get('pe_ttm'),
                            'pb': ak_data.get('pb'),
                            'pb_ratio': ak_data.get('pb'),
                            'ps_ttm': None,
                            'ps_ratio': None,
                            'peg': None,
                            'peg_ratio': None,
                            'market_cap': None,
                            'circulation_market_cap': None,
                            'valuation_level': self._evaluate_valuation(ak_data.get('pe_ttm'), ak_data.get('pb'), None),
                            'score': self._score_valuation(ak_data.get('pe_ttm'), ak_data.get('pb'), None)
                        }
                except Exception as ak_err:
                    logger.error(f"Akshare 备用方案也失败: {str(ak_err)}")
            return {}
    
    async def analyze_growth(self, stock_code: str) -> Dict:
        """成长性分析"""
        try:
            # 优先尝试新浪财经接口（最可靠）
            if self.akshare_source is not None:
                logger.info(f"使用新浪财经接口获取成长数据: {stock_code}")
                sina_income = await self.akshare_source.get_financial_report_sina(stock_code, '利润表')
                
                if sina_income and sina_income.get('data') is not None and not sina_income['data'].empty:
                    df = sina_income['data']
                    
                    # 获取最近几年的年度数据
                    annual_data = df[df['报告日'].astype(str).str.endswith('1231')]
                    
                    if len(annual_data) >= 3:
                        # 计算营收和利润增长率
                        revenues = []
                        profits = []
                        
                        for _, row in annual_data.head(5).iterrows():
                            rev = float(row.get('营业总收入', 0)) if row.get('营业总收入') else 0
                            profit = float(row.get('净利润', 0)) if row.get('净利润') else 0
                            revenues.append(rev)
                            profits.append(profit)
                        
                        # 计算CAGR
                        revenue_cagr_3y = self._calculate_cagr(revenues[:3]) if len(revenues) >= 3 else None
                        profit_cagr_3y = self._calculate_cagr(profits[:3]) if len(profits) >= 3 else None
                        
                        # 从最新数据计算毛利率和净利率
                        latest = annual_data.iloc[0]
                        revenue = float(latest.get('营业总收入', 0)) if latest.get('营业总收入') else 0
                        net_profit = float(latest.get('净利润', 0)) if latest.get('净利润') else 0
                        operating_cost = float(latest.get('营业成本', 0)) if latest.get('营业成本') else 0
                        
                        gross_margin = ((revenue - operating_cost) / revenue) if revenue > 0 else None
                        net_margin = (net_profit / revenue) if revenue > 0 else None
                        
                        # ROE和ROA需要资产负债表数据
                        sina_balance = await self.akshare_source.get_financial_report_sina(stock_code, '资产负债表')
                        roe = None
                        roa = None
                        
                        if sina_balance and sina_balance.get('data') is not None and not sina_balance['data'].empty:
                            balance_df = sina_balance['data']
                            balance_latest = balance_df.iloc[0]
                            
                            total_equity = None
                            for col in ['所有者权益合计', '所有者权益(或股东权益)合计', '股东权益合计']:
                                if col in balance_latest.index and pd.notna(balance_latest.get(col)):
                                    total_equity = float(balance_latest.get(col))
                                    break
                            
                            total_assets = float(balance_latest.get('资产总计', 0)) if balance_latest.get('资产总计') else 0
                            
                            roe = (net_profit / total_equity) if total_equity and total_equity > 0 and net_profit else None
                            roa = (net_profit / total_assets) if total_assets > 0 and net_profit else None
                        
                        result = {
                            'revenue_cagr_3y': revenue_cagr_3y,
                            'revenue_growth': revenue_cagr_3y, # 兼容前端
                            'revenue_cagr_5y': None,
                            'profit_cagr_3y': profit_cagr_3y,
                            'profit_growth': profit_cagr_3y,   # 兼容前端
                            'profit_cagr_5y': None,
                            'roe': roe,
                            'roa': roa,
                            'gross_margin': gross_margin,
                            'net_margin': net_margin,
                            'growth_level': self._evaluate_growth(revenue_cagr_3y, 
                                                                 profit_cagr_3y, 
                                                                 roe),
                            'score': self._score_growth(revenue_cagr_3y, 
                                                       profit_cagr_3y, 
                                                       roe)
                        }
                        
                        logger.info(f"股票 {stock_code} 成长性分析完成: {result}")
                        return result
            
            if not self.ts_pro:
                logger.warning(f"股票 {stock_code} 无法获取成长数据：Tushare 和 Akshare 均不可用")
                return {}
            
            # 构建股票代码
            ts_code = f"{stock_code}.SH" if stock_code.startswith('6') else f"{stock_code}.SZ"
            logger.info(f"正在获取股票 {stock_code} 的成长数据，ts_code={ts_code}")
            
            # 获取财务数据
            df = await self._call_tushare(
                'income',
                ts_code=ts_code,
                fields='ann_date,f_ann_date,end_date,revenue,n_income,grossprofit_margin,netprofit_margin'
            )
            
            logger.info(f"Tushare income 返回数据行数: {len(df) if not df.empty else 0}")
            
            if df.empty or len(df) < 3:
                logger.warning(f"股票 {stock_code} 财务数据不足，尝试 Akshare 备用方案")
                if self.akshare_source is not None:
                    ak_data = await self.akshare_source.get_financial_indicator(stock_code)
                    if ak_data:
                        roe = ak_data.get('roe') # akshare_service now returns ratio
                        return {
                            'revenue_cagr_3y': None,
                            'revenue_growth': None,
                            'revenue_cagr_5y': None,
                            'profit_cagr_3y': None,
                            'profit_growth': None,
                            'profit_cagr_5y': None,
                            'roe': roe,
                            'roa': ak_data.get('roa'), # akshare_service now returns ratio
                            'gross_margin': ak_data.get('gross_margin'), # akshare_service now returns ratio
                            'net_margin': ak_data.get('net_margin'), # akshare_service now returns ratio
                            'growth_level': self._evaluate_growth(None, None, roe),
                            'score': self._score_growth(None, None, roe)
                        }
                return {}
            
            # 按日期排序
            df = df.sort_values('end_date')
            
            # 提取年度数据
            annual_data = df[df['end_date'].str.endswith('1231')].tail(5)
            
            logger.info(f"股票 {stock_code} 年度财务数据行数: {len(annual_data)}")
            
            if len(annual_data) < 3:
                logger.warning(f"股票 {stock_code} 年度财务数据不足")
                return {}
            
            # 计算营收CAGR
            revenues = annual_data['revenue'].values
            revenue_cagr_3y = self._calculate_cagr(revenues[-3:])
            revenue_cagr_5y = self._calculate_cagr(revenues) if len(revenues) >= 5 else None
            
            # 计算净利润CAGR
            profits = annual_data['n_income'].values
            profit_cagr_3y = self._calculate_cagr(profits[-3:])
            profit_cagr_5y = self._calculate_cagr(profits) if len(profits) >= 5 else None
            
            # 获取ROE和ROA
            df_roe = await self._call_tushare(
                'fina_indicator',
                ts_code=ts_code,
                fields='end_date,roe,roa,grossprofit_margin,netprofit_margin'
            )
            
            roe = None
            roa = None
            gross_margin = None
            net_margin = None
            if not df_roe.empty:
                latest_roe = df_roe.iloc[0]
                roe = float(latest_roe['roe']) / 100 if pd.notna(latest_roe['roe']) else None
                roa = float(latest_roe['roa']) / 100 if pd.notna(latest_roe['roa']) else None
                gross_margin = float(latest_roe['grossprofit_margin']) / 100 if pd.notna(latest_roe['grossprofit_margin']) else None
                net_margin = float(latest_roe['netprofit_margin']) / 100 if pd.notna(latest_roe['netprofit_margin']) else None
            
            result = {
                'revenue_cagr_3y': revenue_cagr_3y,
                'revenue_growth': revenue_cagr_3y,  # 兼容前端字段名
                'revenue_cagr_5y': revenue_cagr_5y,
                'profit_cagr_3y': profit_cagr_3y,
                'profit_growth': profit_cagr_3y,    # 兼容前端字段名
                'profit_cagr_5y': profit_cagr_5y,
                'roe': roe,
                'roa': roa,
                'gross_margin': gross_margin,
                'net_margin': net_margin,
                'growth_level': self._evaluate_growth(revenue_cagr_3y, 
                                                     profit_cagr_3y, 
                                                     roe),
                'score': self._score_growth(revenue_cagr_3y, 
                                           profit_cagr_3y, 
                                           roe)
            }
            
            logger.info(f"股票 {stock_code} 成长性分析完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"成长性分析失败 {stock_code}: {str(e)}", exc_info=True)
            # 尝试 Akshare 备用方案
            if self.akshare_source is not None:
                try:
                    ak_data = await self.akshare_source.get_financial_indicator(stock_code)
                    if ak_data:
                        return {
                            'revenue_cagr_3y': None,
                            'revenue_growth': None,
                            'revenue_cagr_5y': None,
                            'profit_cagr_3y': None,
                            'profit_growth': None,
                            'profit_cagr_5y': None,
                            'roe': ak_data.get('roe'), # akshare_service now returns ratio
                            'roa': ak_data.get('roa'), # akshare_service now returns ratio
                            'gross_margin': ak_data.get('gross_margin'), # akshare_service now returns ratio
                            'net_margin': ak_data.get('net_margin'), # akshare_service now returns ratio
                            'growth_level': self._evaluate_growth(None, None, ak_data.get('roe')),
                            'score': self._score_growth(None, None, ak_data.get('roe'))
                        }
                except Exception as ak_err:
                    logger.error(f"Akshare 备用方案也失败: {str(ak_err)}")
            return {}
    
    async def analyze_financial_health(self, stock_code: str) -> Dict:
        """财务健康度分析"""
        try:
            # 优先尝试新浪财经接口（最可靠）
            if self.akshare_source is not None:
                logger.info(f"使用新浪财经接口获取财务健康数据: {stock_code}")
                sina_balance = await self.akshare_source.get_financial_report_sina(stock_code, '资产负债表')
                
                if sina_balance and sina_balance.get('data') is not None and not sina_balance['data'].empty:
                    df = sina_balance['data']
                    latest = df.iloc[0]
                    
                    total_assets = float(latest.get('资产总计', 0)) if latest.get('资产总计') else None
                    total_liab = float(latest.get('负债合计', 0)) if latest.get('负债合计') else None
                    
                    total_equity = None
                    for col in ['所有者权益合计', '所有者权益(或股东权益)合计', '股东权益合计']:
                        if col in latest.index and pd.notna(latest.get(col)):
                            total_equity = float(latest.get(col))
                            break
                    
                    total_cur_assets = float(latest.get('流动资产合计', 0)) if latest.get('流动资产合计') else None
                    total_cur_liab = float(latest.get('流动负债合计', 0)) if latest.get('流动负债合计') else None
                    
                    # 计算财务指标
                    debt_ratio = (total_liab / total_assets) if total_assets and total_liab else None
                    current_ratio = (total_cur_assets / total_cur_liab) if total_cur_assets and total_cur_liab else None
                    
                    # 计算Altman Z-Score
                    z_score = self._calculate_altman_z_score(
                        total_assets or 100,
                        total_liab or 50,
                        total_equity or 50,
                        current_ratio or 1.5
                    )
                    
                    # 获取现金流数据
                    sina_cashflow = await self.akshare_source.get_financial_report_sina(stock_code, '现金流量表')
                    operating_cashflow = None
                    
                    if sina_cashflow and sina_cashflow.get('data') is not None and not sina_cashflow['data'].empty:
                        cf_df = sina_cashflow['data']
                        cf_latest = cf_df.iloc[0]
                        
                        # 尝试获取经营现金流
                        for col in ['经营活动产生的现金流量净额', '经营活动现金流入小计']:
                            if col in cf_latest.index and pd.notna(cf_latest.get(col)):
                                operating_cashflow = float(cf_latest.get(col))
                                break
                    
                    # 计算经营现金流/净利润比率
                    ocf_to_profit = None
                    if operating_cashflow:
                        sina_income = await self.akshare_source.get_financial_report_sina(stock_code, '利润表')
                        if sina_income and sina_income.get('data') is not None and not sina_income['data'].empty:
                            income_latest = sina_income['data'].iloc[0]
                            net_profit = float(income_latest.get('净利润', 0)) if income_latest.get('净利润') else 0
                            if net_profit > 0:
                                ocf_to_profit = operating_cashflow / net_profit
                    
                    result = {
                        'debt_ratio': debt_ratio,
                        'current_ratio': current_ratio,
                        'operating_cashflow': operating_cashflow,
                        'cash_flow': operating_cashflow,     # 兼容前端字段名
                        'ocf_to_profit': ocf_to_profit,
                        'altman_z_score': z_score,
                        'financial_health_level': self._evaluate_financial_health(debt_ratio if debt_ratio else 0, current_ratio or 1.5, z_score),
                        'score': self._score_financial_health(debt_ratio if debt_ratio else 0, current_ratio or 1.5, z_score)
                    }
                    
                    logger.info(f"股票 {stock_code} 财务健康度分析完成: {result}")
                    return result
            
            if not self.ts_pro:
                logger.warning(f"股票 {stock_code} 无法获取财务健康数据：Tushare 和 Akshare 均不可用")
                return {}
            
            # 获取资产负债表数据
            ts_code = f"{stock_code}.SH" if stock_code.startswith('6') else f"{stock_code}.SZ"
            df_balance = await self._call_tushare(
                'balancesheet',
                ts_code=ts_code,
                fields='end_date,total_assets,total_liab,total_equity,total_cur_assets,total_cur_liab'
            )
            
            # 获取现金流量表数据
            df_cashflow = await self._call_tushare(
                'cashflow',
                ts_code=ts_code,
                fields='end_date,n_cashflow_act,n_cashflow_inv_act,free_cashflow'
            )
            
            if df_balance.empty:
                logger.warning(f"股票 {stock_code} 未找到资产负债数据")
                return {}
            
            latest_balance = df_balance.iloc[0]
            
            # 资产负债率
            debt_ratio = float(latest_balance['total_liab']) / float(latest_balance['total_assets'])
            
            # 流动比率
            current_ratio = float(latest_balance['total_cur_assets']) / float(latest_balance['total_cur_liab'])
            
            # 获取经营现金流
            operating_cashflow = None
            ocf_to_profit = None
            if not df_cashflow.empty:
                latest_cashflow = df_cashflow.iloc[0]
                operating_cashflow = float(latest_cashflow['n_cashflow_act']) if latest_cashflow['n_cashflow_act'] else None
                
                # 计算经营现金流/净利润比率
                if operating_cashflow and not df_balance.empty:
                    # 获取净利润
                    df_income = await self._call_tushare(
                        'income',
                        ts_code=ts_code,
                        fields='end_date,n_income'
                    )
                    if not df_income.empty:
                        net_profit = float(df_income.iloc[0]['n_income'])
                        if net_profit > 0:
                            ocf_to_profit = operating_cashflow / net_profit
            
            # 计算 Altman Z-Score (简化版)
            z_score = self._calculate_altman_z_score(
                float(latest_balance['total_assets']),
                float(latest_balance['total_liab']),
                float(latest_balance['total_equity']),
                current_ratio
            )
            
            return {
                'debt_ratio': debt_ratio,
                'current_ratio': current_ratio,
                'operating_cashflow': operating_cashflow,
                'cash_flow': operating_cashflow,  # 兼容前端字段名
                'ocf_to_profit': ocf_to_profit,
                'altman_z_score': z_score,
                'financial_health_level': self._evaluate_financial_health(debt_ratio, current_ratio, z_score),
                'score': self._score_financial_health(debt_ratio, current_ratio, z_score)
            }
            
        except Exception as e:
            logger.error(f"财务健康度分析失败 {stock_code}: {str(e)}")
            return {}
    
    async def analyze_market_trend(self, stock_code: str) -> Dict:
        """市场价格趋势分析"""
        try:
            # 1. 获取K线数据 (3年数据约750条)
            # 优先尝试从本地数据库获取，如果不足则从 akshare 获取
            from services.stock_data_service import stock_data_service
            from database.session import async_session_maker
            
            klines = []
            try:
                async with async_session_maker() as db:
                    klines = await stock_data_service.get_kline_from_db(db, stock_code, "day", 750)
            except Exception as e:
                logger.warning(f"从数据库获取K线失败: {str(e)}")
            
            if not klines or len(klines) < 120: # 至少需要半年数据做基本分析
                logger.info(f"数据库数据不足({len(klines) if klines else 0})，尝试从 Akshare 获取: {stock_code}")
                klines_raw = await self.akshare_source.get_kline(stock_code, "day", 750)
                if klines_raw:
                    # 转换格式以匹配数据库返回的对象结构
                    klines = [SimpleNamespace(**k) for k in klines_raw]
            
            if not klines or len(klines) < 20:
                logger.warning(f"无法获取股票 {stock_code} 的足够K线数据，市场趋势分析跳过")
                return {
                    'price_percentile_3y': None,
                    'adx': None,
                    'volatility_30d': None,
                    'trend_direction': "未知",
                    'ma_status': "未知",
                    'score': 3.0
                }

            # 提取收盘价序列
            closes = np.array([float(k.close) for k in klines])
            latest_price = closes[-1]
            
            # 2. 计算价格分位数 (3年)
            min_price_3y = np.min(closes)
            max_price_3y = np.max(closes)
            price_percentile_3y = (latest_price - min_price_3y) / (max_price_3y - min_price_3y) if max_price_3y > min_price_3y else 0.5
            
            # 3. 计算 30 日波动率 (年化)
            volatility_30d = None
            if len(closes) >= 31:
                # 计算对数收益率的标准差
                log_returns = np.diff(np.log(closes[-31:]))
                volatility_30d = np.std(log_returns) * np.sqrt(252)
                
            # 4. 计算均线状态
            ma20 = np.mean(closes[-20:]) if len(closes) >= 20 else None
            ma60 = np.mean(closes[-60:]) if len(closes) >= 60 else None
            ma120 = np.mean(closes[-120:]) if len(closes) >= 120 else None
            
            ma_status_list = []
            if ma20: ma_status_list.append("MA20之" + ("上" if latest_price > ma20 else "下"))
            if ma60: ma_status_list.append("MA60之" + ("上" if latest_price > ma60 else "下"))
            if ma120: ma_status_list.append("MA120之" + ("上" if latest_price > ma120 else "下"))
            
            ma_status = " | ".join(ma_status_list) if ma_status_list else "均线数据不足"
            
            # 5. 趋势方向
            if ma20 and ma60:
                if latest_price > ma20 and ma20 > ma60:
                    trend_direction = "多头排列"
                elif latest_price < ma20 and ma20 < ma60:
                    trend_direction = "空头排列"
                elif latest_price > ma20:
                    trend_direction = "短期反弹"
                else:
                    trend_direction = "震荡下跌"
            else:
                trend_direction = "趋势不明"
                
            # 6. 计算 ADX (简化版)
            adx = self._calculate_simplified_adx(klines)
            
            # 7. 综合评分 (1-5)
            score = 3.0
            
            # 趋势加分
            if trend_direction == "多头排列":
                score += 1.0
            elif trend_direction == "空头排列":
                score -= 1.0
            elif trend_direction == "短期反弹":
                score += 0.3
            
            # 价格位置加分 (低位加分，高位减分)
            if price_percentile_3y < 0.2: 
                score += 0.7
            elif price_percentile_3y < 0.4:
                score += 0.3
            elif price_percentile_3y > 0.8:
                score -= 0.7
            elif price_percentile_3y > 0.6:
                score -= 0.3
                
            # 趋势强度加分
            if adx and adx > 25:
                if trend_direction == "多头排列":
                    score += 0.5
                elif trend_direction == "空头排列":
                    score -= 0.5
            
            score = max(1.0, min(5.0, score))

            result = {
                'price_percentile_3y': float(price_percentile_3y),
                'adx': float(adx) if adx else None,
                'volatility_30d': float(volatility_30d) if volatility_30d else None,
                'trend_direction': trend_direction,
                'ma_status': ma_status,
                'score': float(score)
            }
            logger.info(f"股票 {stock_code} 市场趋势分析完成: {trend_direction}, 评分: {score}")
            return result
            
        except Exception as e:
            logger.error(f"市场趋势分析失败 {stock_code}: {str(e)}", exc_info=True)
            return {
                'price_percentile_3y': None,
                'adx': None,
                'volatility_30d': None,
                'trend_direction': "分析出错",
                'ma_status': "分析出错",
                'score': 3.0
            }

    def _calculate_simplified_adx(self, klines: List, period: int = 14) -> Optional[float]:
        """计算简化版 ADX (平均趋向指数)"""
        try:
            if len(klines) < period * 2:
                return None
            
            highs = np.array([float(getattr(k, 'high', 0)) for k in klines])
            lows = np.array([float(getattr(k, 'low', 0)) for k in klines])
            closes = np.array([float(getattr(k, 'close', 0)) for k in klines])
            
            # 1. 计算 TR, +DM, -DM
            tr = np.zeros(len(klines))
            plus_dm = np.zeros(len(klines))
            minus_dm = np.zeros(len(klines))
            
            for i in range(1, len(klines)):
                # TR = max(H-L, |H-Cp|, |L-Cp|)
                tr[i] = max(highs[i] - lows[i], 
                            abs(highs[i] - closes[i-1]), 
                            abs(lows[i] - closes[i-1]))
                
                # +DM
                up_move = highs[i] - highs[i-1]
                down_move = lows[i-1] - lows[i]
                
                if up_move > down_move and up_move > 0:
                    plus_dm[i] = up_move
                else:
                    plus_dm[i] = 0
                    
                # -DM
                if down_move > up_move and down_move > 0:
                    minus_dm[i] = down_move
                else:
                    minus_dm[i] = 0
            
            # 2. 平滑函数 (Wilder's Smoothing)
            def wilder_smooth(data, p):
                res = np.zeros(len(data))
                if len(data) <= p: return res
                # 初始值为前 p 个的均值
                res[p] = np.mean(data[1:p+1])
                # 后续值: smoothed = (prev_smoothed * (p-1) + current) / p
                for j in range(p+1, len(data)):
                    res[j] = (res[j-1] * (p-1) + data[j]) / p
                return res
            
            str_tr = wilder_smooth(tr, period)
            str_plus_dm = wilder_smooth(plus_dm, period)
            str_minus_dm = wilder_smooth(minus_dm, period)
            
            # 避免除零
            str_tr = np.where(str_tr == 0, 0.0001, str_tr)
            
            # 3. 计算 +DI, -DI
            plus_di = 100 * str_plus_dm / str_tr
            minus_di = 100 * str_minus_dm / str_tr
            
            # 4. 计算 DX
            di_sum = plus_di + minus_di
            di_sum = np.where(di_sum == 0, 0.0001, di_sum)
            dx = 100 * abs(plus_di - minus_di) / di_sum
            
            # 5. 计算 ADX (平滑 DX)
            adx_series = wilder_smooth(dx, period)
            
            return float(adx_series[-1])
        except Exception as e:
            logger.debug(f"ADX 计算失败: {str(e)}")
            return None
    
    def _calculate_cagr(self, values: np.array) -> Optional[float]:
        """计算复合年增长率"""
        try:
            if len(values) < 2 or values[0] <= 0 or values[-1] <= 0:
                return None
            
            years = len(values) - 1
            cagr = (values[-1] / values[0]) ** (1 / years) - 1
            return cagr  # 返回比例，由前端负责显示百分比
        except:
            return None
    
    async def _get_profit_growth_rate(self, stock_code: str, years: int) -> Optional[float]:
        """获取净利润增长率"""
        try:
            if not self.ts_pro:
                return None
            
            ts_code = f"{stock_code}.SH" if stock_code.startswith('6') else f"{stock_code}.SZ"
            df = await self._call_tushare(
                'income',
                ts_code=ts_code,
                fields='end_date,n_income'
            )
            
            if df.empty or len(df) < years + 1:
                return None
            
            # 按日期排序
            df = df.sort_values('end_date')
            annual_data = df[df['end_date'].str.endswith('1231')].tail(years + 1)
            
            if len(annual_data) < years + 1:
                return None
            
            profits = annual_data['n_income'].values
            return self._calculate_cagr(profits) if profits[0] > 0 else None
            
        except:
            return None
    
    def _calculate_altman_z_score(self, total_assets: float, total_liab: float, 
                                  total_equity: float, current_ratio: float) -> Optional[float]:
        """计算 Altman Z-Score (简化版)"""
        try:
            # 简化版 Z-Score 计算
            # Z = 1.2X1 + 1.4X2 + 3.3X3 + 0.6X4 + 0.999X5
            # 这里使用简化公式
            
            x1 = (total_assets - total_liab) / total_assets  # 营运资金/总资产
            x2 = total_equity / total_liab  # 股东权益/负债
            x3 = current_ratio / 10  # 流动比率 (调整后)
            
            z_score = 1.2 * x1 + 1.4 * 0.1 + 3.3 * x3 + 0.6 * x2 + 0.999 * 0.5
            
            return z_score
        except:
            return None
    
    def _evaluate_valuation(self, pe: Optional[float], pb: Optional[float], 
                           peg: Optional[float]) -> str:
        """评估估值水平"""
        score = 0
        
        # PE评估
        if pe:
            if pe < 15:
                score += 2
            elif pe < 25:
                score += 1
            elif pe > 50:
                score -= 2
        
        # PB评估
        if pb:
            if pb < 1:
                score += 2
            elif pb < 2:
                score += 1
            elif pb > 5:
                score -= 1
        
        # PEG评估
        if peg:
            if peg < 1:
                score += 2
            elif peg > 2:
                score -= 2
        
        if score >= 4:
            return "低估"
        elif score >= 1:
            return "合理"
        else:
            return "高估"
    
    def _evaluate_growth(self, revenue_cagr: Optional[float], profit_cagr: Optional[float],
                        roe: Optional[float]) -> str:
        """评估成长性"""
        score = 0
        
        # 营收增长评估 (使用比例，如 0.2 代表 20%)
        if revenue_cagr:
            if revenue_cagr > 0.2:
                score += 2
            elif revenue_cagr > 0.1:
                score += 1
            elif revenue_cagr < 0:
                score -= 1
        
        # 利润增长评估
        if profit_cagr:
            if profit_cagr > 0.2:
                score += 2
            elif profit_cagr > 0.1:
                score += 1
            elif profit_cagr < 0:
                score -= 1
        
        # ROE评估
        if roe:
            if roe > 0.15:
                score += 2
            elif roe > 0.1:
                score += 1
            elif roe < 0.05:
                score -= 1
        
        if score >= 4:
            return "高成长"
        elif score >= 1:
            return "稳健增长"
        elif score >= -1:
            return "低速增长"
        else:
            return "负增长"
    
    def _evaluate_financial_health(self, debt_ratio: float, current_ratio: float,
                                   z_score: Optional[float]) -> str:
        """评估财务健康度"""
        score = 0
        
        # 资产负债率评估 (使用比例，如 0.5 代表 50%)
        if debt_ratio < 0.5:
            score += 2
        elif debt_ratio < 0.7:
            score += 1
        elif debt_ratio > 0.8:
            score -= 2
        
        # 流动比率评估
        if current_ratio > 2:
            score += 2
        elif current_ratio > 1:
            score += 1
        elif current_ratio < 0.5:
            score -= 2
        
        # Z-Score评估
        if z_score:
            if z_score > 3:
                score += 2
            elif z_score > 1.8:
                score += 1
            elif z_score < 1.8:
                score -= 2
        
        if score >= 4:
            return "优秀"
        elif score >= 2:
            return "良好"
        elif score >= 0:
            return "一般"
        else:
            return "较差"
    
    def _score_valuation(self, pe: Optional[float], pb: Optional[float],
                        peg: Optional[float]) -> float:
        """估值评分 (1-5分)"""
        level = self._evaluate_valuation(pe, pb, peg)
        score_map = {"低估": 5.0, "合理": 3.5, "高估": 1.5}
        return score_map.get(level, 3.0)
    
    def _score_growth(self, revenue_cagr: Optional[float], profit_cagr: Optional[float],
                     roe: Optional[float]) -> float:
        """成长性评分 (1-5分)"""
        level = self._evaluate_growth(revenue_cagr, profit_cagr, roe)
        score_map = {"高成长": 5.0, "稳健增长": 4.0, "低速增长": 2.5, "负增长": 1.0}
        return score_map.get(level, 3.0)
    
    def _score_financial_health(self, debt_ratio: float, current_ratio: float,
                                z_score: Optional[float]) -> float:
        """财务健康度评分 (1-5分)"""
        level = self._evaluate_financial_health(debt_ratio, current_ratio, z_score)
        score_map = {"优秀": 5.0, "良好": 4.0, "一般": 3.0, "较差": 1.5}
        return score_map.get(level, 3.0)
    
    def _generate_recommendation(self, valuation: Dict, growth: Dict,
                                 financial_health: Dict, market_trend: Dict,
                                 overall_score: float) -> Dict:
        """根据分析结果生成投资建议"""
        rating = "观望"
        reasons = []
        
        # 评分基础
        if overall_score >= 4.0:
            rating = "买入"
        elif overall_score >= 3.0:
            rating = "持有"
        elif overall_score < 2.0:
            rating = "卖出"
        else:
            rating = "观望"
            
        # 估值建议
        val_level = valuation.get('valuation_level', "合理")
        if val_level == "低估":
            reasons.append("当前估值水平较低，具备较好的安全边际")
        elif val_level == "高估":
            reasons.append("当前估值处于高位，需警惕回调风险")
            
        # 成长建议
        growth_level = self._evaluate_growth(growth.get('revenue_cagr_3y'), growth.get('profit_cagr_3y'), growth.get('roe'))
        if growth_level == "高成长":
            reasons.append("企业处于高速成长期，业绩增长动力强劲")
        elif growth_level == "负增长":
            reasons.append("业绩出现负增长，经营基本面面临挑战")
            
        # 健康度建议
        health_level = self._evaluate_financial_health(financial_health.get('debt_ratio', 0.5), financial_health.get('current_ratio', 1.0), financial_health.get('altman_z_score'))
        if health_level == "较差":
            reasons.append("财务健康度较差，负债率较高或流动性存在风险")
            
        # 趋势建议
        trend = market_trend.get('trend_direction', "未知")
        if trend == "多头排列":
            reasons.append("二级市场处于明显的上升趋势中，技术面配合良好")
        elif trend == "空头排列":
            reasons.append("技术面呈现空头排列，短期内仍有下行压力")
            
        if not reasons:
            reasons.append("各项指标相对平稳，建议关注后续业绩发布及市场情绪变化")
            
        return {
            'rating': rating,
            'reason': "；".join(reasons) + "。"
        }

    def _calculate_overall_score(self, valuation: Dict, growth: Dict,
                                 financial_health: Dict, market_trend: Dict) -> float:
        """计算综合评分"""
        weights = {
            'valuation': 0.3,
            'growth': 0.3,
            'financial_health': 0.25,
            'market_trend': 0.15
        }
        
        score = (
            valuation.get('score', 3.0) * weights['valuation'] +
            growth.get('score', 3.0) * weights['growth'] +
            financial_health.get('score', 3.0) * weights['financial_health'] +
            market_trend.get('score', 3.0) * weights['market_trend']
        )
        
        return round(score, 2)
    
    async def get_metrics_from_db(self, stock_code: str) -> Optional[Any]:
        """从数据库获取基本面指标 (结构化返回)"""
        try:
            async with async_session_maker() as db:
                return await ops_get_fundamental_metrics(db, stock_code)
        except Exception as e:
            logger.error(f"从数据库获取基本面指标失败 {stock_code}: {str(e)}")
            return None

    async def _save_metrics(self, stock_code: str, valuation: Dict, growth: Dict,
                           financial_health: Dict, market_trend: Dict, overall_score: float):
        """保存基本面指标到数据库（带重试机制，支持更新已存在的记录）"""
        max_retries = 3
        retry_delay = 0.5

        # 生成投资建议
        recommendation = self._generate_recommendation(
            valuation, growth, financial_health, market_trend, overall_score
        )

        for attempt in range(max_retries):
            try:
                async with async_session_maker() as db:
                    success = await save_fundamental_metrics(
                        db=db,
                        stock_code=stock_code,
                        valuation=valuation,
                        growth=growth,
                        financial_health=financial_health,
                        market_trend=market_trend,
                        overall_score=overall_score,
                        recommendation=recommendation
                    )

                    if success:
                        logger.debug(f"保存基本面指标成功: {stock_code}")
                        return
                    else:
                        logger.error(f"保存基本面指标失败: {stock_code}")
                        return

            except Exception as e:
                if "locked" in str(e).lower() and attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt) + random.random()
                    logger.warning(f"数据库锁定，重试 {attempt + 1}/{max_retries}，等待 {wait_time:.2f}s: {stock_code}")
                    await asyncio.sleep(wait_time)
                    continue
                logger.error(f"保存基本面指标失败 {stock_code}: {str(e)}")
                return
    
    async def _save_financial_history(self, stock_code: str, data: Dict, report_type: str = 'quarterly'):
        """保存财务历史数据到数据库 (委托给 ops 层)"""
        try:
            async with async_session_maker() as db:
                await save_financial_history(db, stock_code, data, report_type)
        except Exception as e:
            logger.error(f"保存财务历史数据失败 {stock_code}: {str(e)}")

    async def get_annual_report_from_db(self, stock_code: str) -> Optional[Dict]:
        """从数据库获取最新年报或季报数据"""
        try:
            # 1. 优先从本地Markdown文件加载
            markdown_data = await self.profile_loader.async_load(stock_code)
            if markdown_data:
                markdown_data['data_source'] = 'markdown'
                return markdown_data
            
            # 2. 从数据库加载 (使用 ops 函数)
            async with async_session_maker() as db:
                result = await get_latest_financial_report(db, stock_code)
                
                if result:
                    # 生成摘要
                    summary = self._generate_annual_report_summary(
                        revenue=result.get('revenue') or 0,
                        net_profit=result.get('net_profit') or 0,
                        eps=0  # 数据库暂未存储 EPS，此处设为0
                    )
                    result['summary'] = summary
                    return result
            return None
        except Exception as e:
            logger.error(f"从数据库获取年报失败 {stock_code}: {str(e)}")
            return None

    async def get_quarterly_data_from_db(self, stock_code: str, years: int = 3) -> Optional[Dict]:
        """从数据库获取最近N年的季度财务数据"""
        try:
            async with async_session_maker() as db:
                return await get_financial_history(db, stock_code, years)
        except Exception as e:
            logger.error(f"从数据库获取季度数据失败 {stock_code}: {str(e)}")
            return None

    async def get_annual_report(self, stock_code: str) -> Optional[Dict]:
        """
        获取最新年报或季报数据
        
        优先级：
        1. 本地Markdown文件（手动维护的数据）
        2. API获取（Tushare/Akshare），优先年报，无年报则获取最新季报
        3. 自动更新Markdown文件
        """
        try:
            # 1. 优先从本地Markdown文件加载
            markdown_data = await self.profile_loader.async_load(stock_code)
            if markdown_data:
                logger.info(f"从Markdown文件加载股票资料: {stock_code}")
                # 添加来源标识
                markdown_data['data_source'] = 'markdown'
                return markdown_data
            
            # 2. Markdown不存在，从API获取
            logger.info(f"Markdown文件不存在，从API获取数据: {stock_code}")
            
            # 优先使用 Tushare
            if self.ts_pro:
                ts_code = f"{stock_code}.SH" if stock_code.startswith('6') else f"{stock_code}.SZ"
                
                # 获取利润表数据（不限制period_type，获取所有报告期）
                df_income = await self._call_tushare(
                    'income',
                    ts_code=ts_code,
                    fields='end_date,ann_date,revenue,n_income,basic_eps,diluted_eps'
                )
                
                if not df_income.empty:
                    # 优先获取年报数据
                    annual_data = df_income[df_income['end_date'].str.endswith('1231')].head(1)
                    report_type = '年报'
                    
                    # 如果没有年报，获取最新的季报
                    if annual_data.empty:
                        logger.info(f"股票 {stock_code} 无年报数据，获取最新季报")
                        df_income_sorted = df_income.sort_values('end_date', ascending=False)
                        latest_data = df_income_sorted.head(1)
                        report_type = '季报'
                    else:
                        latest_data = annual_data
                    
                    if not latest_data.empty:
                        latest = latest_data.iloc[0]
                        
                        # 获取现金流量表数据
                        df_cashflow = await self._call_tushare(
                            'cashflow',
                            ts_code=ts_code,
                            fields='end_date,n_cashflow_act'
                        )
                        
                        # 计算毛利
                        revenue = float(latest['revenue']) if latest['revenue'] else 0.0
                        net_profit = float(latest['n_income']) if latest['n_income'] else 0.0
                        # 尝试从 income 表中获取毛利
                        gross_profit = None
                        if 'grossprofit_margin' in latest and pd.notna(latest['grossprofit_margin']):
                            gross_profit = revenue * (float(latest['grossprofit_margin']) / 100)
                        
                        operating_cashflow = None
                        if not df_cashflow.empty:
                            cf_data = df_cashflow[df_cashflow['end_date'] == latest['end_date']]
                            if not cf_data.empty:
                                operating_cashflow = float(cf_data.iloc[0]['n_cashflow_act'])
                        
                        # 生成年报摘要
                        summary = self._generate_annual_report_summary(
                            revenue=revenue,
                            net_profit=net_profit,
                            eps=latest['basic_eps']
                        )
                        
                        result = {
                            'stock_code': stock_code,
                            'report_type': report_type,
                            'report_date': latest['end_date'],
                            'ann_date': latest['ann_date'],
                            'revenue': revenue,
                            'net_profit': net_profit,
                            'gross_profit': gross_profit,
                            'basic_eps': float(latest['basic_eps']) if latest['basic_eps'] else None,
                            'diluted_eps': float(latest['diluted_eps']) if latest['diluted_eps'] else None,
                            'operating_cashflow': operating_cashflow,
                            'summary': summary,
                            'timestamp': datetime.now(),
                            'data_source': 'api'
                        }
                        
                        # 保存到数据库
                        await self._save_financial_history(stock_code, result, 'annual')
                        
                        # 保存到Markdown文件
                        try:
                            await self.profile_loader.async_save(stock_code, result)
                            logger.info(f"已保存股票资料到Markdown文件: {stock_code}")
                        except Exception as e:
                            logger.warning(f"保存Markdown文件失败: {e}")
                        
                        return result
            
            # Tushare 失败，尝试 Akshare 备用方案
            if self.akshare_source is not None:
                logger.info(f"Tushare 获取失败，尝试 Akshare 备用方案: {stock_code}")
                
                # 优先尝试新浪财经接口（更可靠）
                sina_income = await self.akshare_source.get_financial_report_sina(stock_code, '利润表')
                
                if sina_income and sina_income.get('data') is not None and not sina_income['data'].empty:
                    df = sina_income['data']
                    # 优先筛选年报数据（以 1231 结尾的报告期）
                    annual_data = df[df['报告日'].astype(str).str.endswith('1231')]
                    report_type = '年报'
                    
                    # 如果没有年报，获取最新季报
                    if annual_data.empty:
                        logger.info(f"股票 {stock_code} 无年报数据，获取最新季报")
                        latest = df.iloc[0]  # 数据已按日期降序排列
                        report_type = '季报'
                    else:
                        latest = annual_data.iloc[0]
                    
                    # 获取现金流量表
                    sina_cashflow = await self.akshare_source.get_financial_report_sina(stock_code, '现金流量表')
                    operating_cashflow = None
                    
                    if sina_cashflow and sina_cashflow.get('data') is not None and not sina_cashflow['data'].empty:
                        cf_df = sina_cashflow['data']
                        cf_data = cf_df[cf_df['报告日'] == latest['报告日']]
                        if not cf_data.empty:
                            # 尝试获取经营活动现金流
                            ocf_col = None
                            for col in ['经营活动产生的现金流量净额', '经营活动现金流入小计']:
                                if col in cf_data.columns:
                                    ocf_col = col
                                    break
                            if ocf_col:
                                operating_cashflow = float(cf_data.iloc[0][ocf_col])
                    
                    # 生成年报摘要
                    revenue = float(latest.get('营业总收入', 0)) if latest.get('营业总收入') else None
                    net_profit = float(latest.get('净利润', 0)) if latest.get('净利润') else None
                    eps = float(latest.get('基本每股收益', 0)) if latest.get('基本每股收益') else None
                    
                    # 获取毛利
                    operating_cost = float(latest.get('营业成本', 0)) if latest.get('营业成本') else 0
                    gross_profit = (revenue - operating_cost) if revenue else None
                    
                    summary = self._generate_annual_report_summary(
                        revenue=revenue or 0,
                        net_profit=net_profit or 0,
                        eps=eps or 0
                    )
                    
                    result = {
                        'stock_code': stock_code,
                        'report_type': report_type,
                        'report_date': latest['报告日'],
                        'ann_date': latest.get('更新日期', ''),
                        'revenue': revenue,
                        'net_profit': net_profit,
                        'gross_profit': gross_profit,
                        'basic_eps': eps,
                        'diluted_eps': None,  # 新浪财经可能没有这个字段
                        'operating_cashflow': operating_cashflow,
                        'summary': summary,
                        'timestamp': datetime.now(),
                        'data_source': 'api'
                    }
                    
                    # 保存到数据库
                    await self._save_financial_history(stock_code, result, 'annual')
                    
                    # 保存到Markdown文件
                    try:
                        await self.profile_loader.async_save(stock_code, result)
                        logger.info(f"已保存股票资料到Markdown文件: {stock_code}")
                    except Exception as e:
                        logger.warning(f"保存Markdown文件失败: {e}")
                    
                    return result
                
                # 如果新浪财经接口也失败，尝试旧的 Akshare 接口
                income_data = await self.akshare_source.get_income_statement(stock_code)
                
                if income_data:
                    # 获取财务指标
                    financial_indicator = await self.akshare_source.get_financial_indicator(stock_code)
                    
                    # 获取资产负债表
                    balance_sheet = await self.akshare_source.get_balance_sheet(stock_code)
                    
                    # 生成年报摘要
                    revenue = income_data.get('revenue') or 0
                    net_profit = income_data.get('net_profit') or 0
                    eps = (financial_indicator.get('eps') or 0) if financial_indicator else 0
                    
                    # 获取毛利
                    gross_profit = income_data.get('gross_profit')
                    
                    summary = self._generate_annual_report_summary(
                        revenue=revenue,
                        net_profit=net_profit,
                        eps=eps
                    )
                    
                    result = {
                        'stock_code': stock_code,
                        'report_type': '年报',  # 默认年报
                        'report_date': datetime.now().strftime('%Y1231'),
                        'ann_date': datetime.now().strftime('%Y%m%d'),
                        'revenue': revenue,
                        'net_profit': net_profit,
                        'gross_profit': gross_profit,
                        'basic_eps': eps,
                        'diluted_eps': eps,
                        'operating_cashflow': None,  # Akshare 暂无此数据
                        'summary': summary,
                        'timestamp': datetime.now(),
                        'data_source': 'api'
                    }
                    
                    # 保存到Markdown文件
                    try:
                        await self.profile_loader.async_save(stock_code, result)
                        logger.info(f"已保存股票资料到Markdown文件: {stock_code}")
                    except Exception as e:
                        logger.warning(f"保存Markdown文件失败: {e}")
                    
                    return result

            
            logger.warning(f"股票 {stock_code} 无法获取年报或季报数据：所有数据源均不可用")
            return None
            
        except Exception as e:
            logger.error(f"获取年报或季报数据失败 {stock_code}: {str(e)}")
            return None
    
    def _generate_annual_report_summary(self, revenue: float, net_profit: float, eps: float) -> str:
        """生成年报摘要"""
        try:
            revenue_yi = revenue / 100000000 if revenue else 0
            profit_yi = net_profit / 100000000 if net_profit else 0
            
            summary = f"营业收入{revenue_yi:.2f}亿元，"
            summary += f"净利润{profit_yi:.2f}亿元，"
            summary += f"每股收益{eps:.2f}元。"
            
            if net_profit and net_profit > 0:
                summary += "公司盈利能力良好。"
            else:
                summary += "公司处于亏损状态。"
            
            return summary
        except:
            return "年报数据摘要生成失败。"
    
    async def get_quarterly_data(self, stock_code: str, years: int = 3) -> Optional[Dict]:
        """
        获取最近N年的季度财务数据
        
        Args:
            stock_code: 股票代码
            years: 年数，默认3年
            
        Returns:
            季度财务数据
        """
        try:
            # 优先使用新浪财经接口（最可靠）
            if self.akshare_source is not None:
                logger.info(f"使用新浪财经接口获取季度数据: {stock_code}")
                sina_income = await self.akshare_source.get_financial_report_sina(stock_code, '利润表')
                
                if isinstance(sina_income, dict) and sina_income.get('data') is not None:
                    df = sina_income['data']
                    if hasattr(df, 'empty') and not df.empty:
                        # 取最近N年的数据（每年4个季度，共N*4个季度）
                        quarters_count = years * 4
                        quarterly_data = []
                        
                        for _, row in df.head(quarters_count).iterrows():
                            date_str = str(row.get('报告日', ''))
                            if not date_str:
                                continue
                            
                            # 解析日期
                            year = date_str[:4]
                            month = date_str[4:6] if len(date_str) >= 6 else ''
                            
                            # 确定季度
                            if month == '03':
                                quarter = 'Q1'
                            elif month == '06':
                                quarter = 'Q2'
                            elif month == '09':
                                quarter = 'Q3'
                            elif month == '12':
                                quarter = 'Q4'
                            else:
                                quarter = f'Q{(int(month) - 1) // 3 + 1}'
                            
                            # 获取财务数据
                            revenue_val = row.get('营业总收入')
                            net_profit_val = row.get('净利润')
                            operating_cost_val = row.get('营业成本')
                            
                            revenue = float(revenue_val) if revenue_val and pd.notna(revenue_val) else 0.0
                            net_profit = float(net_profit_val) if net_profit_val and pd.notna(net_profit_val) else 0.0
                            operating_cost = float(operating_cost_val) if operating_cost_val and pd.notna(operating_cost_val) else 0.0
                            
                            # 计算毛利和利润率
                            gross_profit = revenue - operating_cost
                            gross_margin = (gross_profit / revenue) if revenue > 0 else 0.0
                            
                            # 计算净利率
                            net_margin = (net_profit / revenue) if revenue > 0 else 0.0
                            
                            quarterly_data.append({
                                'date': f"{year}{quarter}",
                                'year': year,
                                'quarter': quarter,
                                'revenue': revenue,  # 营业收入（元）
                                'net_profit': net_profit,  # 净利润（元）
                                'gross_profit': gross_profit, # 毛利（元）
                                'gross_margin': gross_margin,  # 毛利率（比例）
                                'net_margin': net_margin,  # 净利率（比例）
                            })
                        
                        # 按时间正序排列
                        quarterly_data.reverse()
                        
                        if quarterly_data:
                            logger.info(f"股票 {stock_code} 获取到 {len(quarterly_data)} 个季度数据")
                            result = {
                                'stock_code': stock_code,
                                'quarters': quarterly_data,
                                'timestamp': datetime.now()
                            }
                            # 保存到数据库
                            await self._save_financial_history(stock_code, result, 'quarterly')
                            return result
            
            # 如果新浪接口失败，尝试 Tushare
            if self.ts_pro:
                ts_code = f"{stock_code}.SH" if stock_code.startswith('6') else f"{stock_code}.SZ"
                
                # 获取利润表数据（季度）
                df_income = await self._call_tushare(
                    'income',
                    ts_code=ts_code,
                    fields='end_date,revenue,n_income,oper_cost',
                    period_type='2'  # 季报
                )
                
                if not df_income.empty:
                    # 按日期倒序排序
                    df_income = df_income.sort_values('end_date', ascending=False)
                    
                    # 取最近N年的数据（每年4个季度，共N*4个季度）
                    quarters_count = years * 4
                    recent_quarters = df_income.head(quarters_count)
                    
                    # 构建季度数据列表
                    quarterly_data = []
                    for _, row in recent_quarters.iterrows():
                        end_date = row['end_date']
                        # 解析日期：YYYYMMDD格式
                        year = end_date[:4]
                        month = end_date[4:6]
                        
                        # 确定季度
                        if month == '03':
                            quarter = 'Q1'
                        elif month == '06':
                            quarter = 'Q2'
                        elif month == '09':
                            quarter = 'Q3'
                        elif month == '12':
                            quarter = 'Q4'
                        else:
                            quarter = f'Q{(int(month) - 1) // 3 + 1}'
                        
                        revenue = float(row['revenue']) if row['revenue'] else 0
                        net_profit = float(row['n_income']) if row['n_income'] else 0
                        operating_cost = float(row['oper_cost']) if row['oper_cost'] else 0
                        
                        # 计算毛利率
                        gross_profit = revenue - operating_cost
                        gross_margin = (gross_profit / revenue) if revenue > 0 else 0
                        
                        # 计算净利率
                        net_margin = (net_profit / revenue) if revenue > 0 else 0
                        
                        quarterly_data.append({
                            'date': f"{year}{quarter}",
                            'year': year,
                            'quarter': quarter,
                            'revenue': revenue,  # 营业收入（元）
                            'net_profit': net_profit,  # 净利润（元）
                            'gross_profit': gross_profit, # 毛利（元）
                            'gross_margin': gross_margin,  # 毛利率（比例）
                            'net_margin': net_margin,  # 净利率（比例）
                        })
                    
                    # 按时间正序排列
                    quarterly_data.reverse()
                    
                    result = {
                        'stock_code': stock_code,
                        'quarters': quarterly_data,
                        'timestamp': datetime.now()
                    }
                    # 保存到数据库
                    await self._save_financial_history(stock_code, result, 'quarterly')
                    return result
            
            # Tushare 失败，尝试 Akshare 备用方案
            if self.akshare_source is not None:
                logger.info(f"Tushare 获取季度数据失败，尝试 Akshare 备用方案: {stock_code}")
                
                # 优先尝试新浪财经接口（更可靠）
                sina_income = await self.akshare_source.get_financial_report_sina(stock_code, '利润表')
                
                if isinstance(sina_income, dict) and sina_income.get('data') is not None:
                    df = sina_income['data']
                    if hasattr(df, 'empty') and not df.empty:
                        # 取最近N年的数据（每年4个季度，共N*4个季度）
                        quarters_count = years * 4
                        quarterly_data = []
                        
                        for _, row in df.head(quarters_count).iterrows():
                            date_str = str(row.get('报告日', ''))
                            if not date_str:
                                continue
                            
                            # 解析日期
                            year = date_str[:4]
                            month = date_str[4:6] if len(date_str) >= 6 else ''
                            
                            # 确定季度
                            if month == '03':
                                quarter = 'Q1'
                            elif month == '06':
                                quarter = 'Q2'
                            elif month == '09':
                                quarter = 'Q3'
                            elif month == '12':
                                quarter = 'Q4'
                            else:
                                quarter = f'Q{(int(month) - 1) // 3 + 1}'
                            
                            # 获取财务数据
                            revenue_val = row.get('营业总收入')
                            net_profit_val = row.get('净利润')
                            operating_cost_val = row.get('营业成本')
                            
                            revenue = float(revenue_val) if revenue_val and pd.notna(revenue_val) else 0.0
                            net_profit = float(net_profit_val) if net_profit_val and pd.notna(net_profit_val) else 0.0
                            operating_cost = float(operating_cost_val) if operating_cost_val and pd.notna(operating_cost_val) else 0.0
                            
                            # 计算毛利率
                            gross_profit = revenue - operating_cost
                            gross_margin = (gross_profit / revenue) if revenue > 0 else 0.0
                            
                            # 计算净利率
                            net_margin = (net_profit / revenue) if revenue > 0 else 0.0
                            
                            quarterly_data.append({
                                'date': f"{year}{quarter}",
                                'year': year,
                                'quarter': quarter,
                                'revenue': revenue,  # 营业收入（元）
                                'net_profit': net_profit,  # 净利润（元）
                                'gross_profit': gross_profit, # 毛利（元）
                                'gross_margin': gross_margin,  # 毛利率（%）
                                'net_margin': net_margin,  # 净利率（%）
                            })
                        
                        # 按时间正序排列
                        quarterly_data.reverse()
                        
                        if quarterly_data:
                            result = {
                                'stock_code': stock_code,
                                'quarters': quarterly_data,
                                'timestamp': datetime.now()
                            }
                            # 保存到数据库
                            await self._save_financial_history(stock_code, result, 'quarterly')
                            return result
                
                # 如果新浪财经接口也失败，尝试旧的 Akshare 接口（通过 datasource 层）
                try:
                    # 获取利润表数据（按报告期）
                    try:
                        df = await self.akshare_source._call_akshare(
                            self.akshare_source._get_ak_module().stock_profit_sheet_by_report_em, symbol=stock_code
                        )
                    except (TypeError, Exception) as ak_e:
                        logger.warning(f"Akshare stock_profit_sheet_by_report_em 调用崩溃 {stock_code}: {str(ak_e)}")
                        df = None
                    
                    if df is not None and hasattr(df, 'empty') and not df.empty:
                        # 取最近N年的数据
                        quarterly_data = []
                        count = 0
                        max_count = years * 4
                        
                        for _, row in df.iterrows():
                            if count >= max_count:
                                break
                            
                            # 解析日期
                            date_str = str(row.get('报告期', ''))
                            if not date_str:
                                continue
                            
                            # 解析季度
                            year = date_str[:4]
                            month = date_str[5:7] if len(date_str) > 5 else ''
                            
                            if month == '03':
                                quarter = 'Q1'
                            elif month == '06':
                                quarter = 'Q2'
                            elif month == '09':
                                quarter = 'Q3'
                            elif month == '12':
                                quarter = 'Q4'
                            else:
                                continue
                            
                            # 获取财务数据
                            revenue_val = row.get('营业总收入')
                            net_profit_val = row.get('净利润')
                            operating_cost_val = row.get('营业成本')
                            
                            revenue = float(revenue_val) if revenue_val else 0.0
                            net_profit = float(net_profit_val) if net_profit_val else 0.0
                            operating_cost = float(operating_cost_val) if operating_cost_val else 0.0
                            
                            # 计算毛利率
                            gross_profit = revenue - operating_cost
                            gross_margin = (gross_profit / revenue) if revenue > 0 else 0
                            
                            # 计算净利率
                            net_margin = (net_profit / revenue) if revenue > 0 else 0
                            
                            quarterly_data.append({
                                'date': f"{year}{quarter}",
                                'year': year,
                                'quarter': quarter,
                                'revenue': revenue,
                                'net_profit': net_profit,
                                'gross_margin': gross_margin,
                                'net_margin': net_margin,
                            })
                            
                            count += 1
                        
                        # 按时间正序排列
                        quarterly_data.reverse()
                        
                        if quarterly_data:
                            result = {
                                'stock_code': stock_code,
                                'quarters': quarterly_data,
                                'timestamp': datetime.now()
                            }
                            # 保存到数据库
                            await self._save_financial_history(stock_code, result, 'quarterly')
                            return result
                            
                except Exception as e:
                    logger.error(f"Akshare 获取季度数据失败 {stock_code}: {str(e)}")
            
            logger.warning(f"股票 {stock_code} 无法获取季度数据：所有数据源均不可用")
            return None
            
        except Exception as e:
            logger.error(f"获取季度财务数据失败 {stock_code}: {str(e)}")
            return None
