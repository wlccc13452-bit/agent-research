"""Database Health Check - 数据库健康检查

提供数据库连接池健康检查功能
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


async def check_database_health() -> Dict[str, Any]:
    """
    检查数据库健康状态
    
    Returns:
        健康状态字典
    """
    try:
        from database.session import check_db_health
        return await check_db_health()
    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
