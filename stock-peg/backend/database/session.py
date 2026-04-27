"""数据库会话管理"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import event, text, create_engine
from config.settings import settings
from pathlib import Path
from services.database_logger import db_logger
import time
import logging

# 确保数据目录存在
Path("./data").mkdir(exist_ok=True)

# 创建异步引擎
# 注意：echo=False 强制关闭SQL输出，避免控制台噪音
engine = create_async_engine(
    settings.database_url,
    echo=False,  # 强制关闭SQL输出
    future=True,
    # 增加连接超时，处理 SQLite 锁定问题
    connect_args={"timeout": 60} if "sqlite" in settings.database_url else {},
    # 减少连接池大小，处理高并发下的 SQLite 锁定问题
    # SQLite 仅允许一个写入者，WAL模式下允许多个读取者
    pool_size=5 if "sqlite" in settings.database_url else 50,
    max_overflow=10 if "sqlite" in settings.database_url else 100,
    pool_timeout=120
)

# 为 SQLite 启用 WAL 模式，提高并发性能
if "sqlite" in settings.database_url:
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        # 提高忙碌等待超时
        cursor.execute("PRAGMA busy_timeout=60000")
        cursor.close()

# 创建异步会话工厂
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db():
    """获取数据库会话（带日志记录）"""
    task_id = db_logger.start_db_operation(
        operation_type='session',
        operation_name='数据库会话',
        metadata={'action': 'get_db'}
    )
    
    start_time = time.time()
    
    async with async_session_maker() as session:
        try:
            db_logger.log_db_event(task_id, 'session_created')
            yield session
            
            # 提交事务
            commit_start = time.time()
            await session.commit()
            commit_duration = (time.time() - commit_start) * 1000
            db_logger.log_db_event(task_id, 'transaction_committed', {
                'duration_ms': commit_duration
            })
            
            total_duration = (time.time() - start_time) * 1000
            db_logger.end_db_operation(task_id, success=True)
            
        except Exception as e:
            # 回滚事务
            rollback_start = time.time()
            await session.rollback()
            rollback_duration = (time.time() - rollback_start) * 1000
            db_logger.log_db_event(task_id, 'transaction_rolled_back', {
                'duration_ms': rollback_duration,
                'error': str(e)
            })
            
            total_duration = (time.time() - start_time) * 1000
            db_logger.end_db_operation(task_id, success=False, error=str(e))
            raise
            
        finally:
            await session.close()


async def init_db():
    """初始化数据库"""
    from database.base import Base
    
    task_id = db_logger.start_db_operation(
        operation_type='init',
        operation_name='初始化数据库',
        metadata={'action': 'create_tables'},
        silent=False  # 启动时的数据库初始化逻辑比较重要，建议在控制台显示
    )
    
    start_time = time.time()
    
    try:
        async with engine.begin() as conn:
            db_logger.log_db_event(task_id, 'connection_established')
            
            create_start = time.time()
            # 仅在表不存在时创建
            await conn.run_sync(Base.metadata.create_all)
            
            # 确保唯一索引存在 (处理旧数据库升级)
            if "sqlite" in settings.database_url:
                # 检查索引是否已存在，避免重复执行昂贵的清理操作
                result = await conn.execute(text(
                    "SELECT name FROM sqlite_master WHERE type='index' AND name='uq_stock_kline'"
                ))
                if not result.fetchone():
                    db_logger.log_db_event(task_id, 'creating_indices', {'target': 'stock_kline_data'})
                    # 1. 清理 stock_kline_data
                    await conn.execute(text("""
                        DELETE FROM stock_kline_data 
                        WHERE id IN (
                            SELECT id FROM (
                                SELECT id, ROW_NUMBER() OVER (
                                    PARTITION BY stock_code, trade_date, period 
                                    ORDER BY id
                                ) as row_num 
                                FROM stock_kline_data
                            ) t WHERE t.row_num > 1
                        )
                    """))
                    
                    # 2. 创建 K线数据唯一索引
                    await conn.execute(text("""
                        CREATE UNIQUE INDEX IF NOT EXISTS uq_stock_kline 
                        ON stock_kline_data (stock_code, trade_date, period)
                    """))
                
                result = await conn.execute(text(
                    "SELECT name FROM sqlite_master WHERE type='index' AND name='uq_fundamental_metrics'"
                ))
                if not result.fetchone():
                    db_logger.log_db_event(task_id, 'creating_indices', {'target': 'fundamental_metrics'})
                    # 3. 清理 fundamental_metrics
                    await conn.execute(text("""
                        DELETE FROM fundamental_metrics 
                        WHERE id IN (
                            SELECT id FROM (
                                SELECT id, ROW_NUMBER() OVER (
                                    PARTITION BY stock_code, report_date 
                                    ORDER BY id
                                ) as row_num 
                                FROM fundamental_metrics
                            ) t WHERE t.row_num > 1
                        )
                    """))
                    
                    # 4. 创建 财务指标唯一索引
                    await conn.execute(text("""
                        CREATE UNIQUE INDEX IF NOT EXISTS uq_fundamental_metrics 
                        ON fundamental_metrics (stock_code, report_date)
                    """))
            
            create_duration = (time.time() - create_start) * 1000
            
            db_logger.log_db_event(task_id, 'tables_checked', {
                'duration_ms': create_duration
            })
        
        db_logger.end_db_operation(task_id, success=True)
        
    except Exception as e:
        db_logger.end_db_operation(task_id, success=False, error=str(e))
        raise


# 创建同步引擎（用于飞书消息保存等需要同步操作的场景）
sync_engine = create_engine(
    settings.database_url.replace("+aiosqlite", "").replace("sqlite+aiosqlite", "sqlite"),
    echo=False,
    future=True,
    connect_args={"timeout": 60} if "sqlite" in settings.database_url else {},
)

# 创建同步会话工厂
sync_session_maker = sessionmaker(
    bind=sync_engine,
    class_=Session,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


def get_db_sync() -> Session:
    """获取同步数据库会话"""
    return sync_session_maker()


async def check_db_health() -> dict:
    """Check database connection pool health
    
    用于检测连接池是否正常，特别是长连接线程持有的连接是否失效
    
    Returns:
        Health status dict with connection info
    """
    import logging
    logger = logging.getLogger(__name__)
    
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "pool_size": engine.pool.size(),
        "checked_out": engine.pool.checkedout(),
        "overflow": engine.pool.overflow(),
        "checked_in": engine.pool.checkedin(),
    }
    
    try:
        # 执行简单查询测试连接
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.fetchone()
            
        logger.debug(f"[OK] Database health check passed: pool_size={health_status['pool_size']}")
        return health_status
        
    except Exception as e:
        logger.error(f"[ERROR] Database health check failed: {e}")
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
        
        # 尝试重连：清理连接池
        try:
            await engine.dispose()
            logger.info("🔄 Database connection pool disposed, will reconnect on next use")
        except Exception as dispose_error:
            logger.error(f"Failed to dispose connection pool: {dispose_error}")
        
        return health_status
