"""数据更新管理器 - 智能更新检查和锁机制"""
import logging
from typing import Dict, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from database import DataUpdateLog
from database.session import async_session_maker
from database.operations import (
    record_update_start as ops_record_update_start,
    record_update_complete as ops_record_update_complete,
    check_kline_data_integrity,
    check_financial_data_integrity,
    check_us_index_data_integrity,
)
from config.settings import settings

logger = logging.getLogger(__name__)


class DataUpdateManager:
    """智能数据更新管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataUpdateManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # 更新锁：防止同一股票并发更新
        # 格式：{stock_code: lock_time}
        self.update_locks: Dict[str, datetime] = {}
        
        # 更新缓存：记录最近更新时间
        # 格式：{stock_code_data_type: {last_update: datetime, status: str}}
        self.update_cache_store: Dict[str, Dict] = {}
        
        # 锁过期时间（秒，从配置读取）
        self.lock_expire_seconds = settings.lock_expire_seconds
        
        # 缓存过期时间（秒，从配置读取）
        self.cache_expire_seconds = settings.cache_expire_seconds
        
        self._initialized = True
        logger.info("DataUpdateManager 初始化完成")
    
    def acquire_lock(self, stock_code: str) -> bool:
        """获取更新锁
        
        Returns:
            True: 成功获取锁，可以更新
            False: 锁被占用，不能更新
        """
        now = datetime.now()
        
        # 检查是否存在锁
        if stock_code in self.update_locks:
            lock_time = self.update_locks[stock_code]
            # 检查锁是否过期
            if (now - lock_time).total_seconds() < self.lock_expire_seconds:
                logger.debug(f"股票 {stock_code} 更新锁被占用，锁定于 {lock_time}")
                return False
            else:
                # 锁已过期，清除锁
                logger.debug(f"股票 {stock_code} 更新锁已过期，清除锁")
                del self.update_locks[stock_code]
        
        # 获取锁
        self.update_locks[stock_code] = now
        logger.debug(f"股票 {stock_code} 成功获取更新锁")
        return True
    
    def release_lock(self, stock_code: str):
        """释放更新锁"""
        if stock_code in self.update_locks:
            del self.update_locks[stock_code]
            logger.debug(f"股票 {stock_code} 释放更新锁")
    
    def is_locked(self, stock_code: str) -> bool:
        """检查是否被锁定"""
        now = datetime.now()
        if stock_code in self.update_locks:
            lock_time = self.update_locks[stock_code]
            if (now - lock_time).total_seconds() < self.lock_expire_seconds:
                return True
            else:
                # 锁已过期，清除
                del self.update_locks[stock_code]
        return False
    
    async def check_update_necessity(self, stock_code: str, data_type: str = "kline", db: AsyncSession = None) -> Dict:
        """检查更新必要性
        
        Args:
            stock_code: 股票代码
            data_type: 数据类型 (kline/financial)
            db: 可选的数据库会话，如果提供则复用
            
        Returns:
            {
                'needs_update': bool,
                'reason': str,
                'last_update': datetime,
                'data_source': str  # db/api
            }
        """
        # 0. 验证股票代码
        if not stock_code or stock_code.startswith('UNKNOWN'):
            return {
                'needs_update': False,
                'reason': f'无效的股票代码: {stock_code}',
                'last_update': None,
                'data_source': 'db'
            }
            
        now = datetime.now()
        cache_key = f"{stock_code}_{data_type}"
        
        # 1. 检查更新锁
        if self.is_locked(stock_code):
            return {
                'needs_update': False,
                'reason': '更新进行中',
                'last_update': None,
                'data_source': 'db'
            }
        
        # 2. 检查缓存更新时间
        if cache_key in self.update_cache_store:
            cache_data = self.update_cache_store[cache_key]
            last_update = cache_data.get('last_update')
            cache_time = cache_data.get('cache_time', now)
            
            # 检查缓存是否过期
            if last_update and (now - cache_time).total_seconds() < self.cache_expire_seconds:
                hours_since_update = (now - last_update).total_seconds() / 3600
                
                # K线数据：交易时段和非交易时段使用不同间隔
                if data_type == 'kline':
                    current_hour = now.hour
                    is_trading_time = 9 <= current_hour <= 15
                    
                    # 从配置读取更新间隔
                    trading_interval = settings.kline_trading_update_interval
                    non_trading_interval = settings.kline_non_trading_update_interval
                    
                    if is_trading_time and hours_since_update < trading_interval:
                        return {
                            'needs_update': False,
                            'reason': f'数据足够新（{hours_since_update:.1f}小时前更新）',
                            'last_update': last_update,
                            'data_source': 'db'
                        }
                    elif not is_trading_time and hours_since_update < non_trading_interval:
                        return {
                            'needs_update': False,
                            'reason': f'非交易时段，数据足够新（{hours_since_update:.1f}小时前更新）',
                            'last_update': last_update,
                            'data_source': 'db'
                        }
                
                # 财务数据：从配置读取更新间隔（天）
                elif data_type == 'financial':
                    financial_interval_days = settings.financial_update_interval_days
                    if hours_since_update / 24 < financial_interval_days:
                        return {
                            'needs_update': False,
                            'reason': f'财务数据已最新（{hours_since_update/24:.1f}天前更新）',
                            'last_update': last_update,
                            'data_source': 'db'
                        }
                
                # 美股指数：从配置读取更新间隔（小时）
                elif data_type == 'us_index':
                    us_index_interval = settings.us_index_update_interval_hours
                    if hours_since_update < us_index_interval:
                        return {
                            'needs_update': False,
                            'reason': f'美股指数已最新（{hours_since_update:.1f}小时前更新）',
                            'last_update': last_update,
                            'data_source': 'db'
                        }
        
        # 3. 检查数据库完整性和最后更新时间
        db_check = await self._check_database_integrity(stock_code, data_type, db)
        
        if not db_check['is_complete']:
            return {
                'needs_update': True,
                'reason': db_check['reason'],
                'last_update': db_check.get('last_update'),
                'data_source': 'api'
            }
        
        # 4. 检查数据时效性
        last_update = db_check.get('last_update')
        if last_update:
            hours_since_update = (now - last_update).total_seconds() / 3600
            
            if data_type == 'kline':
                current_hour = now.hour
                is_trading_time = 9 <= current_hour <= 15
                
                # 从配置读取更新间隔
                trading_interval = settings.kline_trading_update_interval
                non_trading_interval = settings.kline_non_trading_update_interval
                
                if is_trading_time and hours_since_update < trading_interval:
                    return {
                        'needs_update': False,
                        'reason': f'数据足够新（{hours_since_update:.1f}小时前更新）',
                        'last_update': last_update,
                        'data_source': 'db'
                    }
                elif not is_trading_time and hours_since_update < non_trading_interval:
                    return {
                        'needs_update': False,
                        'reason': f'非交易时段，数据足够新（{hours_since_update:.1f}小时前更新）',
                        'last_update': last_update,
                        'data_source': 'db'
                    }
                else:
                    return {
                        'needs_update': True,
                        'reason': f'距离上次更新超过{hours_since_update:.1f}小时',
                        'last_update': last_update,
                        'data_source': 'db'
                    }
            elif data_type == 'financial':
                days_since_update = hours_since_update / 24
                if days_since_update < 7:
                    return {
                        'needs_update': False,
                        'reason': f'财务数据已最新（{days_since_update:.1f}天前更新）',
                        'last_update': last_update,
                        'data_source': 'db'
                    }
                return {
                    'needs_update': True,
                    'reason': f'财务数据距上次更新{days_since_update:.1f}天',
                    'last_update': last_update,
                    'data_source': 'db'
                }
        
        return {
            'needs_update': True,
            'reason': '需要更新',
            'last_update': last_update,
            'data_source': 'api'
        }
    
    async def _check_database_integrity(self, stock_code: str, data_type: str, db: AsyncSession = None) -> Dict:
        """检查数据库完整性
        
        Args:
            stock_code: 股票代码
            data_type: 数据类型
            db: 可选的数据库会话
            
        Returns:
            {
                'is_complete': bool,
                'reason': str,
                'last_update': datetime,
                'record_count': int
            }
        """
        try:
            if db is None:
                async with async_session_maker() as session:
                    return await self._check_db_with_session(session, stock_code, data_type)
            else:
                return await self._check_db_with_session(db, stock_code, data_type)
        except Exception as e:
            logger.error(f"检查数据库完整性失败 {stock_code}: {str(e)}")
            return {
                'is_complete': False,
                'reason': f"数据库检查失败: {str(e)}",
                'last_update': None,
                'record_count': 0
            }

    async def _check_db_with_session(self, db: AsyncSession, stock_code: str, data_type: str) -> Dict:
        """使用提供的会话检查数据库完整性"""
        if data_type == 'kline':
            return await check_kline_data_integrity(db, stock_code)
        if data_type == 'financial':
            return await check_financial_data_integrity(db, stock_code)
        if data_type == 'us_index':
            return await check_us_index_data_integrity(db, stock_code)
        return {
            'is_complete': True,
            'reason': '数据完整',
            'last_update': None,
            'record_count': 0
        }
    
    def update_cache_entry(self, stock_code: str, data_type: str, last_update: datetime, status: str = 'completed'):
        """更新缓存"""
        cache_key = f"{stock_code}_{data_type}"
        self.update_cache_store[cache_key] = {
            'last_update': last_update,
            'status': status,
            'cache_time': datetime.now()
        }
        logger.debug(f"更新缓存: {cache_key}, last_update={last_update}, status={status}")
    
    def clear_cache(self, stock_code: str, data_type: str = None):
        """清除缓存"""
        if data_type:
            cache_key = f"{stock_code}_{data_type}"
            if cache_key in self.update_cache_store:
                del self.update_cache_store[cache_key]
        else:
            keys_to_delete = [k for k in self.update_cache_store.keys() if k.startswith(f"{stock_code}_")]
            for key in keys_to_delete:
                del self.update_cache_store[key]
    
    async def get_all_update_status(self, stock_codes: List[str], data_type: str = "kline") -> Dict:
        """获取所有股票的更新状态
        
        Returns:
            {
                'needs_update_count': int,
                'last_global_update': datetime,
                'stocks': [
                    {
                        'stock_code': str,
                        'needs_update': bool,
                        'last_update': datetime,
                        'reason': str
                    }
                ]
            }
        """
        stocks_status = []
        needs_update_count = 0
        last_global_update = None
        
        async with async_session_maker() as db:
            for stock_code in stock_codes:
                status = await self.check_update_necessity(stock_code, data_type, db)
                stocks_status.append({
                    'stock_code': stock_code,
                    'needs_update': status['needs_update'],
                    'last_update': status.get('last_update'),
                    'reason': status['reason']
                })
                
                if status['needs_update']:
                    needs_update_count += 1
                
                # 更新全局最后更新时间
                if status.get('last_update'):
                    if last_global_update is None or status['last_update'] > last_global_update:
                        last_global_update = status['last_update']
        
        return {
            'needs_update_count': needs_update_count,
            'last_global_update': last_global_update,
            'stocks': stocks_status
        }
    
    async def record_update_start(self, stock_code: str, data_type: str, update_type: str = 'auto') -> int:
        """记录更新开始
        
        Returns:
            log_id: 更新日志ID
        """
        import asyncio
        import random
        
        max_retries = 5
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                async with async_session_maker() as db:
                    log_id = await ops_record_update_start(db, stock_code, data_type, update_type)
                    return log_id
                
            except Exception as e:
                if "locked" in str(e).lower() and attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt) + random.random()
                    logger.warning(f"数据库锁定，重试 {attempt + 1}/{max_retries}，等待 {wait_time:.2f}s: {stock_code}")
                    await asyncio.sleep(wait_time)
                    continue
                logger.error(f"记录更新开始失败: {str(e)}")
                return 0
        return 0
    
    async def record_update_complete(self, log_id: int, records_updated: int, error_message: str = None):
        """记录更新完成"""
        import asyncio
        import random
        
        if log_id == 0:
            return

        max_retries = 5
        retry_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                async with async_session_maker() as db:
                    success = await ops_record_update_complete(db, log_id, records_updated, error_message)
                    if success:
                        # 更新缓存
                        self.update_cache_entry(stock_code='', data_type='', last_update=datetime.now(), status='completed' if not error_message else 'failed')
                    return
                
            except Exception as e:
                if "locked" in str(e).lower() and attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt) + random.random()
                    logger.warning(f"数据库锁定，重试 {attempt + 1}/{max_retries}，等待 {wait_time:.2f}s: log_id={log_id}")
                    await asyncio.sleep(wait_time)
                    continue
                logger.error(f"记录更新完成失败: {str(e)}")
                break


# 单例实例
data_update_manager = DataUpdateManager()
