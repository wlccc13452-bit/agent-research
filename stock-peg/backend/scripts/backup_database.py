"""
数据库自动备份脚本

功能：
1. 每日自动备份数据库
2. 保留最近7天的备份
3. 自动清理过期备份
4. 支持手动触发备份

使用方法：
    # 手动备份
    uv run python backend/scripts/backup_database.py
    
    # 定时任务（crontab）
    0 2 * * * cd /path/to/stock-peg && uv run python backend/scripts/backup_database.py
"""
import os
import sys
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseBackup:
    """数据库备份管理器"""
    
    def __init__(self):
        self.db_path = Path(__file__).parent.parent / "data" / "stock_peg.db"
        self.backup_dir = Path(__file__).parent.parent / "data" / "backups"
        self.max_backups = 7  # 保留最近7天
        
    def create_backup(self) -> bool:
        """
        创建数据库备份
        
        Returns:
            bool: 备份是否成功
        """
        try:
            # 确保备份目录存在
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 检查数据库文件是否存在
            if not self.db_path.exists():
                logger.error(f"数据库文件不存在: {self.db_path}")
                return False
            
            # 生成备份文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"stock_peg_{timestamp}.db"
            backup_path = self.backup_dir / backup_filename
            
            # 复制数据库文件
            shutil.copy2(self.db_path, backup_path)
            
            # 获取备份文件大小
            backup_size = backup_path.stat().st_size / (1024 * 1024)  # MB
            
            logger.info(f"[OK] 数据库备份成功: {backup_filename}")
            logger.info(f"  备份路径: {backup_path}")
            logger.info(f"  备份大小: {backup_size:.2f} MB")
            
            # 清理过期备份
            self._cleanup_old_backups()
            
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] 数据库备份失败: {e}", exc_info=True)
            return False
    
    def _cleanup_old_backups(self):
        """清理过期备份"""
        try:
            # 获取所有备份文件
            backups = sorted(
                self.backup_dir.glob("stock_peg_*.db"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            # 删除超过保留数量的备份
            if len(backups) > self.max_backups:
                for old_backup in backups[self.max_backups:]:
                    old_backup.unlink()
                    logger.info(f"  清理过期备份: {old_backup.name}")
                    
        except Exception as e:
            logger.error(f"清理过期备份失败: {e}", exc_info=True)
    
    def list_backups(self):
        """列出所有备份"""
        backups = sorted(
            self.backup_dir.glob("stock_peg_*.db"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        if not backups:
            logger.info("暂无备份文件")
            return
        
        logger.info(f"\n当前备份列表（共 {len(backups)} 个）：")
        for i, backup in enumerate(backups, 1):
            stat = backup.stat()
            size_mb = stat.st_size / (1024 * 1024)
            mtime = datetime.fromtimestamp(stat.st_mtime)
            logger.info(f"{i}. {backup.name} | {size_mb:.2f} MB | {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def restore_backup(self, backup_name: str) -> bool:
        """
        恢复数据库备份
        
        Args:
            backup_name: 备份文件名
            
        Returns:
            bool: 恢复是否成功
        """
        try:
            backup_path = self.backup_dir / backup_name
            
            if not backup_path.exists():
                logger.error(f"备份文件不存在: {backup_path}")
                return False
            
            # 创建当前数据库的备份（以防恢复失败）
            if self.db_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_backup = self.db_path.with_suffix(f".db.pre_restore_{timestamp}")
                shutil.copy2(self.db_path, temp_backup)
                logger.info(f"[OK] 已创建恢复前备份: {temp_backup.name}")
            
            # 恢复数据库
            shutil.copy2(backup_path, self.db_path)
            logger.info(f"[OK] 数据库恢复成功: {backup_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] 数据库恢复失败: {e}", exc_info=True)
            return False


def main():
    """主函数"""
    backup_manager = DatabaseBackup()
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "list":
            backup_manager.list_backups()
        elif command == "restore" and len(sys.argv) > 2:
            backup_name = sys.argv[2]
            backup_manager.restore_backup(backup_name)
        else:
            logger.error(f"未知命令: {command}")
            logger.info("使用方法:")
            logger.info("  uv run python backend/scripts/backup_database.py        # 创建备份")
            logger.info("  uv run python backend/scripts/backup_database.py list   # 列出备份")
            logger.info("  uv run python backend/scripts/backup_database.py restore <backup_name>  # 恢复备份")
    else:
        # 默认：创建备份
        success = backup_manager.create_backup()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
