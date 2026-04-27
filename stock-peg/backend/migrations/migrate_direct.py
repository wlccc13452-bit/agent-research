"""直接执行数据库迁移脚本

如果没有使用 Alembic，可以直接运行此脚本
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database.session import sync_session_maker
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_database():
    """执行数据库迁移"""
    try:
        with sync_session_maker() as session:
            # 检查字段是否已存在
            check_sql = text("""
                SELECT COUNT(*) as count 
                FROM pragma_table_info('daily_reports') 
                WHERE name='smart_analysis'
            """)
            
            result = session.execute(check_sql).fetchone()
            
            if result[0] > 0:
                logger.info("字段已存在，跳过迁移")
                return
            
            # 添加新字段
            alter_sql = text("""
                ALTER TABLE daily_reports 
                ADD COLUMN smart_analysis TEXT,
                ADD COLUMN smart_analysis_formatted TEXT,
                ADD COLUMN pmr_data TEXT,
                ADD COLUMN llm_model VARCHAR(50),
                ADD COLUMN llm_provider VARCHAR(50)
            """)
            
            session.execute(alter_sql)
            session.commit()
            
            logger.info("[OK] 数据库迁移成功！已添加智能分析字段")
            
    except Exception as e:
        logger.error(f"[ERROR] 数据库迁移失败: {str(e)}")
        raise


if __name__ == "__main__":
    print("开始数据库迁移...")
    migrate_database()
    print("迁移完成！")
