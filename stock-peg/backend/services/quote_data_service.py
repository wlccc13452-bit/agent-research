"""
行情数据数据库服务
实现行情数据的本地存储和读取
"""
import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import StockRealtimeQuote
from database.operations.quote_ops import (
    get_quote as ops_get_quote,
    save_quote as ops_save_quote,
    check_update_necessity as ops_check_update_necessity,
    get_all_quotes as ops_get_all_quotes,
)
from models import StockQuote
from services.managed_logger import StockDataLogger

# 使用受管理的日志器(受配置文件控制)
logger = StockDataLogger('quote_data')


class QuoteDataService:
    """行情数据数据库服务"""
    
    async def get_quote_from_db(self, db: AsyncSession, stock_code: str) -> Optional[StockQuote]:
        """
        从数据库获取行情数据
        
        Args:
            db: 数据库会话
            stock_code: 股票代码
            
        Returns:
            StockQuote对象，如果不存在则返回None
        """
        try:
            quote_data = await ops_get_quote(db, stock_code)
            
            if quote_data:
                logger.info(f"[OK] 从数据库获取行情数据: {stock_code}")
                return StockQuote(
                    code=quote_data.stock_code,
                    name=quote_data.stock_name or '',
                    price=float(quote_data.price) if quote_data.price else 0.0,
                    change=float(quote_data.change) if quote_data.change else 0.0,
                    change_pct=float(quote_data.change_pct) if quote_data.change_pct else 0.0,
                    open=float(quote_data.open) if quote_data.open else 0.0,
                    high=float(quote_data.high) if quote_data.high else 0.0,
                    low=float(quote_data.low) if quote_data.low else 0.0,
                    volume=int(quote_data.volume) if quote_data.volume else 0,
                    amount=float(quote_data.amount) if quote_data.amount else 0.0,
                    timestamp=quote_data.trade_time or quote_data.updated_at or datetime.now()
                )
            
            return None
            
        except Exception as e:
            logger.error(f"[ERROR] 从数据库获取行情数据失败 {stock_code}: {str(e)}")
            return None
    
    async def save_quote_to_db(
        self, 
        db: AsyncSession, 
        quote: StockQuote,
        data_source: str = 'api'
    ) -> bool:
        """
        保存行情数据到数据库
        
        Args:
            db: 数据库会话
            quote: 行情数据
            data_source: 数据来源
            
        Returns:
            是否保存成功
        """
        try:
            quote_data = {
                'code': quote.code,
                'name': quote.name,
                'price': quote.price,
                'change': quote.change,
                'change_pct': quote.change_pct,
                'open': quote.open,
                'high': quote.high,
                'low': quote.low,
                'volume': quote.volume,
                'amount': quote.amount,
            }
            
            success = await ops_save_quote(db, quote_data, data_source)
            
            if success:
                logger.info(f"[OK] 保存行情数据到数据库: {quote.code}")
            return success
            
        except Exception as e:
            logger.error(f"[ERROR] 保存行情数据到数据库失败 {quote.code}: {str(e)}")
            return False
    
    async def batch_save_quotes(
        self, 
        db: AsyncSession, 
        quotes: List[StockQuote],
        data_source: str = 'api'
    ) -> int:
        """
        批量保存行情数据
        
        Args:
            db: 数据库会话
            quotes: 行情数据列表
            data_source: 数据来源
            
        Returns:
            成功保存的数量
        """
        success_count = 0
        for quote in quotes:
            if await self.save_quote_to_db(db, quote, data_source):
                success_count += 1
        return success_count
    
    async def get_quotes_from_db(
        self, 
        db: AsyncSession, 
        stock_codes: List[str]
    ) -> List[StockQuote]:
        """
        批量从数据库获取行情数据 (优化版：单次批量查询)
        
        Args:
            db: 数据库会话
            stock_codes: 股票代码列表
            
        Returns:
            行情数据列表
        """
        try:
            if not stock_codes:
                return []
                
            from database.operations.quote_ops import get_quotes_batch
            quotes_data = await get_quotes_batch(db, stock_codes)
            
            quotes = []
            for q in quotes_data:
                quotes.append(StockQuote(
                    code=q.stock_code,
                    name=q.stock_name or '',
                    price=float(q.price) if q.price else 0.0,
                    change=float(q.change) if q.change else 0.0,
                    change_pct=float(q.change_pct) if q.change_pct else 0.0,
                    open=float(q.open) if q.open else 0.0,
                    high=float(q.high) if q.high else 0.0,
                    low=float(q.low) if q.low else 0.0,
                    volume=int(q.volume) if q.volume else 0,
                    amount=float(q.amount) if q.amount else 0.0,
                    timestamp=q.trade_time or q.updated_at or datetime.now()
                ))
            
            logger.info(f"[OK] 批量从数据库获取行情数据: 成功 {len(quotes)}/{len(stock_codes)}")
            return quotes
            
        except Exception as e:
            logger.error(f"[ERROR] 批量从数据库获取行情数据失败: {str(e)}")
            return []
    
    async def check_update_necessity(
        self, 
        db: AsyncSession, 
        stock_code: str,
        max_age_seconds: int = 60
    ) -> Dict:
        """
        检查行情数据是否需要更新
        
        Args:
            db: 数据库会话
            stock_code: 股票代码
            max_age_seconds: 最大允许的数据年龄（秒）
            
        Returns:
            {
                'needs_update': bool,
                'reason': str,
                'last_update': datetime or None
            }
        """
        return await ops_check_update_necessity(db, stock_code, max_age_seconds)
    
    async def get_all_quotes_from_db(self, db: AsyncSession) -> List[StockQuote]:
        """
        获取数据库中所有行情数据
        
        Args:
            db: 数据库会话
            
        Returns:
            行情数据列表
        """
        try:
            quotes_data = await ops_get_all_quotes(db)
            
            quotes = []
            for q in quotes_data:
                quotes.append(StockQuote(
                    code=q.stock_code,
                    name=q.stock_name or '',
                    price=float(q.price) if q.price else 0.0,
                    change=float(q.change) if q.change else 0.0,
                    change_pct=float(q.change_pct) if q.change_pct else 0.0,
                    open=float(q.open) if q.open else 0.0,
                    high=float(q.high) if q.high else 0.0,
                    low=float(q.low) if q.low else 0.0,
                    volume=int(q.volume) if q.volume else 0,
                    amount=float(q.amount) if q.amount else 0.0,
                    timestamp=q.trade_time or q.updated_at or datetime.now()
                ))
            
            logger.info(f"[OK] 从数据库获取所有行情数据: {len(quotes)}条")
            return quotes
            
        except Exception as e:
            logger.error(f"[ERROR] 从数据库获取所有行情数据失败: {str(e)}")
            return []

    async def update_stock_quote(self, db: AsyncSession, stock_code: str) -> Dict:
        """
        更新股票行情数据 (从网络API获取并保存到数据库)
        
        Returns:
            {
                'success': bool,
                'message': str,
                'quote': StockQuote or None
            }
        """
        try:
            from services.stock_service import StockService
            stock_service = StockService()
            
            # 从网络API获取最新行情
            quote = await stock_service.get_quote(stock_code, use_cache=False)
            
            if quote:
                # 保存到数据库
                success = await self.save_quote_to_db(db, quote, data_source='api')
                
                if success:
                    return {
                        'success': True,
                        'message': '行情更新成功',
                        'quote': quote
                    }
                else:
                    return {
                        'success': False,
                        'message': '行情保存到数据库失败',
                        'quote': None
                    }
            else:
                return {
                    'success': False,
                    'message': '无法从网络API获取行情数据',
                    'quote': None
                }
        except Exception as e:
            logger.error(f"[ERROR] 更新行情数据失败 {stock_code}: {str(e)}")
            return {
                'success': False,
                'message': f'更新异常: {str(e)}',
                'quote': None
            }


# 单例实例
quote_data_service = QuoteDataService()
