"""Fundamental Operations - 基本面数据操作

提供基本面相关的数据库操作：
- 基本面指标
- 财务历史数据
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from types import SimpleNamespace

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import FundamentalMetrics, FinancialHistory

logger = logging.getLogger(__name__)


# ============== Fundamental Metrics Operations ==============

async def get_fundamental_metrics(
    db: AsyncSession,
    stock_code: str
) -> Optional[Any]:
    """
    从数据库获取基本面指标 (结构化返回)
    
    Args:
        db: 数据库会话
        stock_code: 股票代码
        
    Returns:
        结构化的基本面指标对象，便于路由直接使用 dot notation
    """
    try:
        stmt = select(FundamentalMetrics).where(
            FundamentalMetrics.stock_code == stock_code
        ).order_by(FundamentalMetrics.report_date.desc()).limit(1)
        
        result = await db.execute(stmt)
        metrics = result.scalars().first()
        
        if not metrics:
            return None
        
        # 构造结构化返回对象，以便路由可以直接使用 dot notation
        return SimpleNamespace(
            valuation={
                'pe_ttm': float(metrics.pe_ttm) if metrics.pe_ttm else None,
                'pe_lyr': float(metrics.pe_lyr) if metrics.pe_lyr else None,
                'pb': float(metrics.pb) if metrics.pb else None,
                'ps_ttm': float(metrics.ps_ttm) if metrics.ps_ttm else None,
                'peg': float(metrics.peg) if metrics.peg else None,
                'score': float(metrics.valuation_score) if metrics.valuation_score else 3.0
            },
            growth={
                'revenue_cagr_3y': float(metrics.revenue_cagr_3y) if metrics.revenue_cagr_3y else None,
                'revenue_cagr_5y': float(metrics.revenue_cagr_5y) if metrics.revenue_cagr_5y else None,
                'profit_cagr_3y': float(metrics.profit_cagr_3y) if metrics.profit_cagr_3y else None,
                'profit_cagr_5y': float(metrics.profit_cagr_5y) if metrics.profit_cagr_5y else None,
                'roe': float(metrics.roe) if metrics.roe else None,
                'roa': float(metrics.roa) if metrics.roa else None,
                'score': float(metrics.growth_score) if metrics.growth_score else 3.0
            },
            financial_health={
                'debt_ratio': float(metrics.debt_ratio) if metrics.debt_ratio else None,
                'current_ratio': float(metrics.current_ratio) if metrics.current_ratio else None,
                'ocf_to_profit': float(metrics.ocf_to_profit) if metrics.ocf_to_profit else None,
                'altman_z_score': float(metrics.altman_z_score) if metrics.altman_z_score else None,
                'score': float(metrics.financial_health_score) if metrics.financial_health_score else 3.0
            },
            market_trend={
                'price_percentile_3y': float(metrics.price_percentile_3y) if metrics.price_percentile_3y else None,
                'adx': float(metrics.adx) if metrics.adx else None,
                'volatility_30d': float(metrics.volatility_30d) if metrics.volatility_30d else None,
                'trend_direction': metrics.trend_direction,
                'ma_status': metrics.ma_status,
                'score': float(metrics.market_trend_score) if metrics.market_trend_score else 3.0
            },
            recommendation={
                'rating': metrics.recommendation_rating,
                'reason': metrics.recommendation_reason
            },
            overall_score=float(metrics.overall_score) if metrics.overall_score else 3.0,
            updated_at=metrics.created_at  # 使用创建时间作为更新时间
        )
        
    except Exception as e:
        logger.error(f"从数据库获取基本面指标失败 {stock_code}: {str(e)}")
        return None


async def save_fundamental_metrics(
    db: AsyncSession,
    stock_code: str,
    valuation: Dict,
    growth: Dict,
    financial_health: Dict,
    market_trend: Dict,
    overall_score: float,
    recommendation: Dict
) -> bool:
    """
    保存基本面指标到数据库（带重试机制，支持更新已存在的记录）
    
    Args:
        db: 数据库会话
        stock_code: 股票代码
        valuation: 估值指标
        growth: 成长性指标
        financial_health: 财务健康度
        market_trend: 市场趋势
        overall_score: 综合评分
        recommendation: 投资建议
        
    Returns:
        是否保存成功
    """
    try:
        # 检查是否已存在当天的记录
        today = datetime.now().date()
        stmt = select(FundamentalMetrics).where(
            and_(
                FundamentalMetrics.stock_code == stock_code,
                FundamentalMetrics.report_date == today
            )
        )
        result = await db.execute(stmt)
        existing_metrics = result.scalar_one_or_none()
        
        if existing_metrics:
            # 更新已存在的记录
            existing_metrics.pe_ttm = valuation.get('pe_ttm')
            existing_metrics.pe_lyr = valuation.get('pe_lyr')
            existing_metrics.pb = valuation.get('pb')
            existing_metrics.ps_ttm = valuation.get('ps_ttm')
            existing_metrics.peg = valuation.get('peg')
            
            existing_metrics.revenue_cagr_3y = growth.get('revenue_cagr_3y')
            existing_metrics.revenue_cagr_5y = growth.get('revenue_cagr_5y')
            existing_metrics.profit_cagr_3y = growth.get('profit_cagr_3y')
            existing_metrics.profit_cagr_5y = growth.get('profit_cagr_5y')
            existing_metrics.roe = growth.get('roe')
            existing_metrics.roa = growth.get('roa')
            
            existing_metrics.debt_ratio = financial_health.get('debt_ratio')
            existing_metrics.current_ratio = financial_health.get('current_ratio')
            existing_metrics.ocf_to_profit = financial_health.get('ocf_to_profit')
            existing_metrics.altman_z_score = financial_health.get('altman_z_score')
            
            existing_metrics.price_percentile_3y = market_trend.get('price_percentile_3y')
            existing_metrics.adx = market_trend.get('adx')
            existing_metrics.volatility_30d = market_trend.get('volatility_30d')
            existing_metrics.trend_direction = market_trend.get('trend_direction')
            existing_metrics.ma_status = market_trend.get('ma_status')
            
            existing_metrics.valuation_score = valuation.get('score')
            existing_metrics.growth_score = growth.get('score')
            existing_metrics.financial_health_score = financial_health.get('score')
            existing_metrics.market_trend_score = market_trend.get('score')
            existing_metrics.overall_score = overall_score
            
            # 投资建议
            existing_metrics.recommendation_rating = recommendation.get('rating')
            existing_metrics.recommendation_reason = recommendation.get('reason')
            
            logger.debug(f"更新基本面指标: {stock_code}")
        else:
            # 创建新记录
            metrics = FundamentalMetrics(
                stock_code=stock_code,
                report_date=today,
                
                # 估值指标
                pe_ttm=valuation.get('pe_ttm'),
                pe_lyr=valuation.get('pe_lyr'),
                pb=valuation.get('pb'),
                ps_ttm=valuation.get('ps_ttm'),
                peg=valuation.get('peg'),
                
                # 成长性指标
                revenue_cagr_3y=growth.get('revenue_cagr_3y'),
                revenue_cagr_5y=growth.get('revenue_cagr_5y'),
                profit_cagr_3y=growth.get('profit_cagr_3y'),
                profit_cagr_5y=growth.get('profit_cagr_5y'),
                roe=growth.get('roe'),
                roa=growth.get('roa'),
                
                # 财务健康度
                debt_ratio=financial_health.get('debt_ratio'),
                current_ratio=financial_health.get('current_ratio'),
                ocf_to_profit=financial_health.get('ocf_to_profit'),
                altman_z_score=financial_health.get('altman_z_score'),
                
                # 市场趋势
                price_percentile_3y=market_trend.get('price_percentile_3y'),
                adx=market_trend.get('adx'),
                volatility_30d=market_trend.get('volatility_30d'),
                trend_direction=market_trend.get('trend_direction'),
                ma_status=market_trend.get('ma_status'),
                
                # 综合评分
                valuation_score=valuation.get('score'),
                growth_score=growth.get('score'),
                financial_health_score=financial_health.get('score'),
                market_trend_score=market_trend.get('score'),
                overall_score=overall_score,
                
                # 投资建议
                recommendation_rating=recommendation.get('rating'),
                recommendation_reason=recommendation.get('reason')
            )
            db.add(metrics)
            logger.debug(f"新增基本面指标: {stock_code}")
        
        await db.commit()
        return True
        
    except Exception as e:
        logger.error(f"保存基本面指标失败 {stock_code}: {str(e)}")
        await db.rollback()
        return False


# ============== Financial History Operations ==============

async def get_financial_history(
    db: AsyncSession,
    stock_code: str,
    years: int = 3
) -> Optional[Dict]:
    """
    从数据库获取最近N年的季度财务数据
    
    Args:
        db: 数据库会话
        stock_code: 股票代码
        years: 年数，默认3年
        
    Returns:
        季度财务数据
    """
    try:
        # 获取最近 N*4 个季度
        stmt = select(FinancialHistory).where(
            FinancialHistory.stock_code == stock_code
        ).order_by(FinancialHistory.report_date.desc()).limit(years * 4)
        
        result = await db.execute(stmt)
        histories = result.scalars().all()
        
        if histories:
            quarterly_data = []
            for h in histories:
                date_str = h.report_date.strftime('%Y%m%d')
                year = date_str[:4]
                month = date_str[4:6]
                
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
                
                revenue = float(h.revenue) if h.revenue else 0.0
                net_profit = float(h.net_profit) if h.net_profit else 0.0
                gross_profit = float(h.gross_profit) if h.gross_profit else 0.0
                
                quarterly_data.append({
                    'date': f"{year}{quarter}",
                    'year': year,
                    'quarter': quarter,
                    'revenue': revenue,
                    'net_profit': net_profit,
                    'gross_profit': gross_profit,
                    'gross_margin': (gross_profit / revenue) if revenue > 0 else 0.0,
                    'net_margin': (net_profit / revenue) if revenue > 0 else 0.0
                })
            
            # 按时间正序排列
            quarterly_data.reverse()
            
            return {
                'stock_code': stock_code,
                'quarters': quarterly_data,
                'timestamp': datetime.now(),
                'data_source': 'db'
            }
        return None
        
    except Exception as e:
        logger.error(f"从数据库获取季度数据失败 {stock_code}: {str(e)}")
        return None


async def get_latest_financial_report(
    db: AsyncSession,
    stock_code: str
) -> Optional[Dict]:
    """
    从数据库获取最新年报或季报数据
    
    Args:
        db: 数据库会话
        stock_code: 股票代码
        
    Returns:
        最新财务报告数据
    """
    try:
        stmt = select(FinancialHistory).where(
            FinancialHistory.stock_code == stock_code
        ).order_by(FinancialHistory.report_date.desc()).limit(1)
        
        result = await db.execute(stmt)
        latest = result.scalars().first()
        
        if latest:
            # 模拟 API 返回格式
            report_date_str = latest.report_date.strftime('%Y%m%d')
            report_type = '年报' if report_date_str.endswith('1231') else '季报'
            
            return {
                'stock_code': stock_code,
                'report_type': report_type,
                'report_date': report_date_str,
                'revenue': float(latest.revenue) if latest.revenue else None,
                'net_profit': float(latest.net_profit) if latest.net_profit else None,
                'gross_profit': float(latest.gross_profit) if latest.gross_profit else None,
                'operating_cashflow': float(latest.operating_cashflow) if latest.operating_cashflow else None,
                'timestamp': datetime.now(),
                'data_source': 'db'
            }
        return None
        
    except Exception as e:
        logger.error(f"从数据库获取年报失败 {stock_code}: {str(e)}")
        return None


async def save_financial_history(
    db: AsyncSession,
    stock_code: str,
    data: Dict,
    report_type: str = 'quarterly'
) -> bool:
    """
    保存财务历史数据到数据库
    
    Args:
        db: 数据库会话
        stock_code: 股票代码
        data: 财务数据
        report_type: 报告类型 (quarterly/annual)
        
    Returns:
        是否保存成功
    """
    try:
        if report_type == 'quarterly':
            # 处理季度数据列表
            quarters = data.get('quarters', [])
            for q in quarters:
                # 解析报告日期 (YYYYQN -> YYYY-MM-DD)
                year = int(q['year'])
                quarter = q['quarter']
                if quarter == 'Q1':
                    month, day = 3, 31
                elif quarter == 'Q2':
                    month, day = 6, 30
                elif quarter == 'Q3':
                    month, day = 9, 30
                elif quarter == 'Q4':
                    month, day = 12, 31
                else:
                    continue
                
                report_date = datetime(year, month, day).date()
                
                # 检查是否已存在
                stmt = select(FinancialHistory).where(
                    and_(
                        FinancialHistory.stock_code == stock_code,
                        FinancialHistory.report_date == report_date
                    )
                )
                result = await db.execute(stmt)
                existing = result.scalars().first()
                
                if existing:
                    existing.revenue = q.get('revenue')
                    existing.net_profit = q.get('net_profit')
                    existing.gross_profit = q.get('gross_profit')
                    existing.report_type = 'quarterly'
                else:
                    new_history = FinancialHistory(
                        stock_code=stock_code,
                        report_date=report_date,
                        report_type='quarterly',
                        revenue=q.get('revenue'),
                        net_profit=q.get('net_profit'),
                        gross_profit=q.get('gross_profit')
                    )
                    db.add(new_history)
        
        elif report_type == 'annual':
            # 处理单条年报/最新季报数据
            report_date_str = str(data.get('report_date', ''))
            if not report_date_str:
                return False
            
            try:
                if len(report_date_str) == 8:
                    report_date = datetime.strptime(report_date_str, '%Y%m%d').date()
                else:
                    # 可能是其他格式，如 YYYY-MM-DD
                    import pandas as pd
                    report_date = pd.to_datetime(report_date_str).date()
            except Exception:
                logger.warning(f"无法解析报告日期: {report_date_str}")
                return False
            
            stmt = select(FinancialHistory).where(
                and_(
                    FinancialHistory.stock_code == stock_code,
                    FinancialHistory.report_date == report_date
                )
            )
            result = await db.execute(stmt)
            existing = result.scalars().first()
            
            actual_type = 'annual' if report_date_str.endswith('1231') else 'quarterly'
            
            if existing:
                existing.revenue = data.get('revenue')
                existing.net_profit = data.get('net_profit')
                existing.gross_profit = data.get('gross_profit')
                existing.operating_cashflow = data.get('operating_cashflow')
                existing.report_type = actual_type
            else:
                new_history = FinancialHistory(
                    stock_code=stock_code,
                    report_date=report_date,
                    report_type=actual_type,
                    revenue=data.get('revenue'),
                    net_profit=data.get('net_profit'),
                    gross_profit=data.get('gross_profit'),
                    operating_cashflow=data.get('operating_cashflow')
                )
                db.add(new_history)
        
        await db.commit()
        logger.info(f"已保存股票 {stock_code} 的 {report_type} 财务历史数据")
        return True
        
    except Exception as e:
        logger.error(f"保存财务历史数据失败 {stock_code}: {str(e)}")
        await db.rollback()
        return False
