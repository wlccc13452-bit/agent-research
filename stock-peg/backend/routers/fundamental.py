"""基本面分析路由"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from services.fundamental_analyzer import FundamentalAnalyzer
from services.background_updater import background_updater
from services.data_update_manager import data_update_manager
from services.data_source_tracker import data_source_tracker
from database.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

# 创建基本面分析器
fundamental_analyzer = FundamentalAnalyzer()


def _build_empty_section(section: str, stock_code: str, is_updating: bool) -> Dict:
    empty_map = {
        'valuation': {
            'pe_ttm': None,
            'pe_lyr': None,
            'pb': None,
            'ps_ttm': None,
            'peg': None,
            'score': 3.0
        },
        'growth': {
            'revenue_cagr_3y': None,
            'revenue_cagr_5y': None,
            'profit_cagr_3y': None,
            'profit_cagr_5y': None,
            'roe': None,
            'roa': None,
            'score': 3.0
        },
        'financial_health': {
            'debt_ratio': None,
            'current_ratio': None,
            'ocf_to_profit': None,
            'altman_z_score': None,
            'score': 3.0
        }
    }
    payload = dict(empty_map.get(section, {}))
    payload['is_updating'] = is_updating
    payload['stock_code'] = stock_code
    payload['message'] = '财务数据尚未准备好，已启动后台更新' if is_updating else '财务数据尚未准备好'
    return payload


@router.get("/{stock_code}/annual-report")
async def get_annual_report(stock_code: str, db: AsyncSession = Depends(get_db)):
    """获取最新年报或季报数据"""
    try:
        # 1. 检查数据更新必要性
        update_necessity = await data_update_manager.check_update_necessity(stock_code, 'financial')
        
        # 2. 如果需要更新，则提交后台任务（异步）
        is_updating = False
        if update_necessity['needs_update']:
            logger.info(f"财务数据需要更新: {stock_code}, 原因: {update_necessity['reason']}")
            await background_updater.submit_fundamental_update_task(stock_code)
            is_updating = True
            
        # 3. 优先从数据库获取现有数据（真实数据）
        report = await fundamental_analyzer.get_annual_report_from_db(stock_code)
        
        # 4. 判断数据来源
        data_source = 'db' if report else 'none'
        
        # 5. 如果数据库没数据，确保后台更新已触发
        if not report and not is_updating:
            logger.info(f"数据库中无财务数据，触发后台更新: {stock_code}")
            await background_updater.submit_fundamental_update_task(stock_code)
            is_updating = True
        
        # 5. 记录数据来源
        await data_source_tracker.track_data_read(
            db=db,
            data_type='financial',
            stock_code=stock_code,
            data_source=data_source,
            last_update_time=update_necessity.get('last_update'),
            is_updating=is_updating,
            metadata={'report_type': 'annual'}
        )
        
        # 6. 构建响应
        if not report:
            # 返回空数据而不是 404，避免前端报错
            logger.warning(f"股票 {stock_code} 暂无年报或季报数据")
            empty_data = {
                'stock_code': stock_code,
                'report_type': None,
                'report_date': None,
                'revenue': None,
                'net_profit': None,
                'basic_eps': None,
                'summary': '暂无年报或季报数据，可能原因：Tushare权限不足或数据源不可用',
                'timestamp': None
            }
            return data_source_tracker.build_metadata_response(
                data=empty_data,
                data_type='financial',
                stock_code=stock_code,
                data_source='none',
                is_updating=False
            )
        
        return data_source_tracker.build_metadata_response(
            data=report,
            data_type='financial',
            stock_code=stock_code,
            data_source=data_source,
            last_update=update_necessity.get('last_update'),
            is_updating=is_updating
        )
        
    except Exception as e:
        logger.error(f"获取年报或季报数据失败 {stock_code}: {str(e)}")
        # 返回空数据而不是 500 错误
        error_data = {
            'stock_code': stock_code,
            'report_type': None,
            'report_date': None,
            'revenue': None,
            'net_profit': None,
            'basic_eps': None,
            'summary': f'获取年报或季报数据失败: {str(e)}',
            'timestamp': None
        }
        return data_source_tracker.build_metadata_response(
            data=error_data,
            data_type='financial',
            stock_code=stock_code,
            data_source='error',
            is_updating=False,
            extra_metadata={'error': str(e)}
        )


@router.get("/{stock_code}/quarterly")
async def get_quarterly_data(stock_code: str, years: int = 3, db: AsyncSession = Depends(get_db)):
    """获取最近N年的季度财务数据"""
    try:
        # 1. 检查数据更新必要性
        update_necessity = await data_update_manager.check_update_necessity(stock_code, 'financial')
        
        # 2. 如果需要更新，则提交后台任务（异步）
        is_updating = False
        if update_necessity['needs_update']:
            logger.info(f"财务季度数据需要更新: {stock_code}, 原因: {update_necessity['reason']}")
            await background_updater.submit_fundamental_update_task(stock_code)
            is_updating = True
            
        # 3. 优先从数据库获取现有数据（真实数据）
        data = await fundamental_analyzer.get_quarterly_data_from_db(stock_code, years)
        
        # 4. 判断数据来源
        data_source = 'db' if data else 'none'
        
        # 5. 如果数据库没数据，确保后台更新已触发
        if not data and not is_updating:
            logger.info(f"数据库中无季度财务数据，触发后台更新: {stock_code}")
            await background_updater.submit_fundamental_update_task(stock_code)
            is_updating = True
        
        # 5. 记录数据来源
        await data_source_tracker.track_data_read(
            db=db,
            data_type='financial',
            stock_code=stock_code,
            data_source=data_source,
            last_update_time=update_necessity.get('last_update'),
            is_updating=is_updating,
            metadata={'report_type': 'quarterly', 'years': years}
        )
        
        # 6. 构建响应
        if not data:
            # 返回空数据而不是 404，避免前端报错
            logger.warning(f"股票 {stock_code} 暂无季度财务数据")
            empty_data = {
                'stock_code': stock_code,
                'quarters': [],
                'message': '暂无季度数据，可能原因：Tushare权限不足或数据源不可用'
            }
            return data_source_tracker.build_metadata_response(
                data=empty_data,
                data_type='financial',
                stock_code=stock_code,
                data_source='none',
                is_updating=False
            )
        
        return data_source_tracker.build_metadata_response(
            data=data,
            data_type='financial',
            stock_code=stock_code,
            data_source=data_source,
            last_update=update_necessity.get('last_update'),
            is_updating=is_updating,
            extra_metadata={'years': years}
        )
        
    except Exception as e:
        logger.error(f"获取季度财务数据失败 {stock_code}: {str(e)}")
        # 返回空数据而不是 500 错误
        error_data = {
            'stock_code': stock_code,
            'quarters': [],
            'message': f'获取季度数据失败: {str(e)}'
        }
        return data_source_tracker.build_metadata_response(
            data=error_data,
            data_type='financial',
            stock_code=stock_code,
            data_source='error',
            is_updating=False,
            extra_metadata={'error': str(e)}
        )


@router.get("/{stock_code}/valuation")
async def get_valuation(stock_code: str):
    """获取估值指标 (优先从缓存/数据库获取)"""
    try:
        # 1. 优先从综合分析结果中获取（如果已缓存）
        from services.extended_cache import financial_analysis_cache
        cached_analysis = await financial_analysis_cache.get(stock_code)
        
        if cached_analysis and 'valuation' in cached_analysis:
            return cached_analysis['valuation']
            
        # 2. 如果没有缓存，检查数据库
        metrics = await fundamental_analyzer.get_metrics_from_db(stock_code)
        if metrics and metrics.valuation:
            return metrics.valuation
            
        update_necessity = await data_update_manager.check_update_necessity(stock_code, 'financial')
        is_updating = False
        if update_necessity['needs_update']:
            logger.info(f"估值数据缺失，触发后台更新: {stock_code}")
            await background_updater.submit_fundamental_update_task(stock_code)
            is_updating = True
        return _build_empty_section('valuation', stock_code, is_updating)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取估值指标失败 {stock_code}: {str(e)}")
        return _build_empty_section('valuation', stock_code, False)


@router.get("/{stock_code}/growth")
async def get_growth(stock_code: str):
    """获取成长性指标 (优先从缓存/数据库获取)"""
    try:
        # 1. 优先从综合分析结果中获取（如果已缓存）
        from services.extended_cache import financial_analysis_cache
        cached_analysis = await financial_analysis_cache.get(stock_code)
        
        if cached_analysis and 'growth' in cached_analysis:
            return cached_analysis['growth']
            
        # 2. 如果没有缓存，检查数据库
        metrics = await fundamental_analyzer.get_metrics_from_db(stock_code)
        if metrics and metrics.growth:
            return metrics.growth
            
        update_necessity = await data_update_manager.check_update_necessity(stock_code, 'financial')
        is_updating = False
        if update_necessity['needs_update']:
            logger.info(f"成长性数据缺失，触发后台更新: {stock_code}")
            await background_updater.submit_fundamental_update_task(stock_code)
            is_updating = True
        return _build_empty_section('growth', stock_code, is_updating)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取成长性指标失败 {stock_code}: {str(e)}")
        return _build_empty_section('growth', stock_code, False)


@router.get("/{stock_code}/financial-health")
async def get_financial_health(stock_code: str):
    """获取财务健康度 (优先从缓存/数据库获取)"""
    try:
        # 1. 优先从综合分析结果中获取（如果已缓存）
        from services.extended_cache import financial_analysis_cache
        cached_analysis = await financial_analysis_cache.get(stock_code)
        
        if cached_analysis and 'financial_health' in cached_analysis:
            return cached_analysis['financial_health']
            
        # 2. 如果没有缓存，检查数据库
        metrics = await fundamental_analyzer.get_metrics_from_db(stock_code)
        if metrics and metrics.financial_health:
            return metrics.financial_health
            
        update_necessity = await data_update_manager.check_update_necessity(stock_code, 'financial')
        is_updating = False
        if update_necessity['needs_update']:
            logger.info(f"财务健康度数据缺失，触发后台更新: {stock_code}")
            await background_updater.submit_fundamental_update_task(stock_code)
            is_updating = True
        return _build_empty_section('financial_health', stock_code, is_updating)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取财务健康度失败 {stock_code}: {str(e)}")
        return _build_empty_section('financial_health', stock_code, False)


@router.get("/{stock_code}")
async def analyze_fundamental(stock_code: str):
    """获取股票基本面分析 (优先从缓存/数据库获取)"""
    try:
        # 1. 优先从缓存获取
        from services.extended_cache import financial_analysis_cache
        cached_analysis = await financial_analysis_cache.get(stock_code)
        if cached_analysis:
            return cached_analysis
            
        # 2. 尝试从数据库获取
        metrics = await fundamental_analyzer.get_metrics_from_db(stock_code)
        if metrics:
            # 将数据库模型转换为字典
            result = {
                'stock_code': stock_code,
                'valuation': metrics.valuation,
                'growth': metrics.growth,
                'financial_health': metrics.financial_health,
                'market_trend': metrics.market_trend,
                'recommendation': metrics.recommendation,
                'overall_score': metrics.overall_score,
                'timestamp': metrics.updated_at
            }
            # 存入缓存
            await financial_analysis_cache.set(result, stock_code)
            return result
            
        # 3. 触发后台更新
        logger.info(f"基本面分析数据缺失，触发后台更新: {stock_code}")
        await background_updater.submit_fundamental_update_task(stock_code)
        
        # 返回空数据而不是 404，避免前端报错
        empty_data = {
            'stock_code': stock_code,
            'valuation': {},
            'growth': {},
            'financial_health': {},
            'market_trend': {},
            'recommendation': {
                'rating': '观望',
                'reason': '财务数据正在加载中，请稍后再试'
            },
            'overall_score': None,
            'timestamp': None,
            'is_updating': True,
            'message': '财务数据尚未准备好，已启动后台更新'
        }
        return empty_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"基本面分析失败 {stock_code}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
