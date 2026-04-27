"""
Log Cleanup Service - Automatic cleanup of old log files

Automatically removes log files older than configured days
and limits the number of files per directory.
"""
import os
import shutil
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional
from configparser import ConfigParser

logger = logging.getLogger(__name__)


class LogCleanupService:
    """Service for automatic log file cleanup"""
    
    def __init__(self, config_path: str = "config/console_output.ini"):
        """Initialize log cleanup service
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.logs_dir = Path("logs")
        
        # Load configuration
        self.config = ConfigParser()
        self.config.read(config_path, encoding='utf-8')
        
        # Get cleanup settings
        self.enabled = self._getboolean('enable_auto_cleanup', True)
        self.max_age_days = self._getint('max_age_days', 3)
        self.max_files_per_dir = self._getint('max_files_per_dir', 500)
        self.cleanup_directories = self._getlist('cleanup_directories', [])
        self.file_extensions = self._getlist('file_extensions', ['.log', '.json'])
        self.cleanup_schedule = self._get('cleanup_schedule', 'startup')
        self.min_file_age_seconds = self._getint('min_file_age_seconds', 3600)
        self.remove_empty_dirs = self._getboolean('remove_empty_directories', False)
        self.log_operations = self._getboolean('log_cleanup_operations', True)
        self.dry_run = self._getboolean('dry_run', False)
        
        # Backup settings
        self.create_backup = self._getboolean('create_backup_before_cleanup', False)
        self.backup_retention_days = self._getint('backup_retention_days', 7)
        
    def _getboolean(self, key: str, fallback: bool) -> bool:
        """Get boolean value from config"""
        try:
            return self.config.getboolean('log_cleanup', key, fallback=fallback)
        except:
            return fallback
    
    def _getint(self, key: str, fallback: int) -> int:
        """Get integer value from config"""
        try:
            return self.config.getint('log_cleanup', key, fallback=fallback)
        except:
            return fallback
    
    def _get(self, key: str, fallback: str) -> str:
        """Get string value from config"""
        try:
            return self.config.get('log_cleanup', key, fallback=fallback)
        except:
            return fallback
    
    def _getlist(self, key: str, fallback: List[str]) -> List[str]:
        """Get list value from config (comma-separated)"""
        try:
            value = self.config.get('log_cleanup', key, fallback='')
            if value:
                return [item.strip() for item in value.split(',') if item.strip()]
            return fallback
        except:
            return fallback
    
    def cleanup_all(self) -> dict:
        """Execute cleanup on all configured directories
        
        Returns:
            Summary dict with cleanup statistics
        """
        if not self.enabled:
            if self.log_operations:
                logger.info("[LOG CLEANUP] Automatic cleanup is disabled")
            return {'enabled': False}
        
        if self.log_operations:
            logger.info("=" * 60)
            logger.info("[LOG CLEANUP] Starting automatic log cleanup")
            logger.info("=" * 60)
            logger.info(f"[LOG CLEANUP] Max age: {self.max_age_days} days")
            logger.info(f"[LOG CLEANUP] Max files per dir: {self.max_files_per_dir}")
            logger.info(f"[LOG CLEANUP] Dry run: {self.dry_run}")
        
        stats = {
            'enabled': True,
            'total_files_deleted': 0,
            'total_size_freed': 0,
            'directories_cleaned': 0,
            'errors': [],
            'details': {}
        }
        
        # Get directories to clean
        if self.cleanup_directories:
            dirs_to_clean = [self.logs_dir / d for d in self.cleanup_directories]
        else:
            # Clean all subdirectories
            dirs_to_clean = [d for d in self.logs_dir.iterdir() if d.is_dir() and d.name != 'backup']
        
        # Clean each directory
        for dir_path in dirs_to_clean:
            if dir_path.exists() and dir_path.is_dir():
                dir_stats = self._cleanup_directory(dir_path)
                stats['total_files_deleted'] += dir_stats['files_deleted']
                stats['total_size_freed'] += dir_stats['size_freed']
                stats['directories_cleaned'] += 1
                stats['details'][dir_path.name] = dir_stats
        
        # Clean old backups if enabled
        if self.create_backup:
            backup_stats = self._cleanup_old_backups()
            stats['total_files_deleted'] += backup_stats['files_deleted']
            stats['total_size_freed'] += backup_stats['size_freed']
        
        # Remove empty directories if configured
        if self.remove_empty_dirs:
            self._remove_empty_directories(dirs_to_clean)
        
        # Log summary
        if self.log_operations:
            logger.info("=" * 60)
            logger.info("[LOG CLEANUP] Cleanup completed")
            logger.info(f"[LOG CLEANUP] Files deleted: {stats['total_files_deleted']}")
            logger.info(f"[LOG CLEANUP] Size freed: {stats['total_size_freed'] / 1024 / 1024:.2f} MB")
            logger.info(f"[LOG CLEANUP] Directories cleaned: {stats['directories_cleaned']}")
            if stats['errors']:
                logger.warning(f"[LOG CLEANUP] Errors: {len(stats['errors'])}")
            logger.info("=" * 60)
        
        return stats
    
    def _cleanup_directory(self, dir_path: Path) -> dict:
        """Clean up a single directory
        
        Args:
            dir_path: Path to directory to clean
            
        Returns:
            Statistics for this directory
        """
        stats = {
            'files_deleted': 0,
            'size_freed': 0,
            'files_by_age': 0,
            'files_by_count': 0
        }
        
        if self.log_operations:
            logger.info(f"\n[LOG CLEANUP] Cleaning directory: {dir_path.name}")
        
        # Get all files with matching extensions
        files_to_consider = []
        for ext in self.file_extensions:
            files_to_consider.extend(dir_path.glob(f"*{ext}"))
        
        if not files_to_consider:
            return stats
        
        # Sort by modification time (oldest first)
        files_to_consider.sort(key=lambda f: f.stat().st_mtime)
        
        # Calculate cutoff time
        now = datetime.now()
        age_cutoff = now - timedelta(days=self.max_age_days)
        min_age_time = now - timedelta(seconds=self.min_file_age_seconds)
        
        files_to_delete = []
        
        # Step 1: Delete files older than max_age_days
        for file_path in files_to_consider:
            try:
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                file_size = file_path.stat().st_size
                
                # Check if file is old enough
                if file_mtime < age_cutoff:
                    # Check if file is not too young (safety check)
                    if file_mtime < min_age_time:
                        files_to_delete.append(file_path)
                        stats['files_by_age'] += 1
                        if self.log_operations:
                            logger.debug(f"[LOG CLEANUP] Old file: {file_path.name} ({file_mtime.strftime('%Y-%m-%d %H:%M')})")
            except Exception as e:
                if self.log_operations:
                    logger.warning(f"[LOG CLEANUP] Error checking file {file_path.name}: {e}")
        
        # Step 2: If still too many files, delete oldest ones
        remaining_files = [f for f in files_to_consider if f not in files_to_delete]
        if len(remaining_files) > self.max_files_per_dir:
            # Sort remaining files by mtime (oldest first)
            remaining_files.sort(key=lambda f: f.stat().st_mtime)
            
            # Delete oldest files until we reach the limit
            files_to_remove = remaining_files[:-self.max_files_per_dir]
            for file_path in files_to_remove:
                try:
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    # Safety check: don't delete very recent files
                    if file_mtime < min_age_time:
                        files_to_delete.append(file_path)
                        stats['files_by_count'] += 1
                        if self.log_operations:
                            logger.debug(f"[LOG CLEANUP] Excess file: {file_path.name}")
                except Exception as e:
                    if self.log_operations:
                        logger.warning(f"[LOG CLEANUP] Error checking file {file_path.name}: {e}")
        
        # Delete files
        for file_path in files_to_delete:
            try:
                file_size = file_path.stat().st_size
                
                # Create backup if enabled
                if self.create_backup:
                    self._backup_file(file_path)
                
                if self.dry_run:
                    if self.log_operations:
                        logger.info(f"[LOG CLEANUP] [DRY RUN] Would delete: {file_path.name}")
                else:
                    file_path.unlink()
                    stats['files_deleted'] += 1
                    stats['size_freed'] += file_size
                    if self.log_operations:
                        logger.info(f"[LOG CLEANUP] Deleted: {file_path.name}")
            except Exception as e:
                error_msg = f"Failed to delete {file_path.name}: {e}"
                if self.log_operations:
                    logger.error(f"[LOG CLEANUP] {error_msg}")
        
        return stats
    
    def _backup_file(self, file_path: Path) -> bool:
        """Backup a file before deletion
        
        Args:
            file_path: Path to file to backup
            
        Returns:
            True if backup successful
        """
        try:
            backup_dir = self.logs_dir / 'backup' / datetime.now().strftime('%Y-%m-%d')
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            backup_path = backup_dir / file_path.name
            
            # If backup already exists, add timestamp
            if backup_path.exists():
                timestamp = datetime.now().strftime('%H%M%S')
                backup_path = backup_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"
            
            shutil.copy2(file_path, backup_path)
            return True
        except Exception as e:
            if self.log_operations:
                logger.warning(f"[LOG CLEANUP] Failed to backup {file_path.name}: {e}")
            return False
    
    def _cleanup_old_backups(self) -> dict:
        """Clean up old backup files
        
        Returns:
            Statistics for backup cleanup
        """
        stats = {
            'files_deleted': 0,
            'size_freed': 0
        }
        
        backup_dir = self.logs_dir / 'backup'
        if not backup_dir.exists():
            return stats
        
        # Calculate cutoff time
        now = datetime.now()
        cutoff = now - timedelta(days=self.backup_retention_days)
        
        # Delete old backup directories
        for date_dir in backup_dir.iterdir():
            if date_dir.is_dir():
                try:
                    # Try to parse directory name as date
                    dir_date = datetime.strptime(date_dir.name, '%Y-%m-%d')
                    if dir_date < cutoff:
                        # Calculate size before deletion
                        dir_size = sum(f.stat().st_size for f in date_dir.rglob('*') if f.is_file())
                        
                        if self.dry_run:
                            if self.log_operations:
                                logger.info(f"[LOG CLEANUP] [DRY RUN] Would delete backup: {date_dir.name}")
                        else:
                            shutil.rmtree(date_dir)
                            stats['files_deleted'] += 1
                            stats['size_freed'] += dir_size
                            if self.log_operations:
                                logger.info(f"[LOG CLEANUP] Deleted old backup: {date_dir.name}")
                except ValueError:
                    # Directory name is not a date, skip
                    pass
                except Exception as e:
                    if self.log_operations:
                        logger.warning(f"[LOG CLEANUP] Error cleaning backup {date_dir.name}: {e}")
        
        return stats
    
    def _remove_empty_directories(self, dirs: List[Path]) -> None:
        """Remove empty directories
        
        Args:
            dirs: List of directories to check
        """
        for dir_path in dirs:
            try:
                if dir_path.exists() and dir_path.is_dir():
                    # Check if directory is empty
                    if not any(dir_path.iterdir()):
                        if self.dry_run:
                            if self.log_operations:
                                logger.info(f"[LOG CLEANUP] [DRY RUN] Would remove empty directory: {dir_path.name}")
                        else:
                            dir_path.rmdir()
                            if self.log_operations:
                                logger.info(f"[LOG CLEANUP] Removed empty directory: {dir_path.name}")
            except Exception as e:
                if self.log_operations:
                    logger.warning(f"[LOG CLEANUP] Error removing directory {dir_path.name}: {e}")
    
    def get_cleanup_preview(self) -> dict:
        """Preview what would be cleaned without actually deleting
        
        Returns:
            Preview statistics
        """
        # Temporarily enable dry run
        original_dry_run = self.dry_run
        self.dry_run = True
        
        # Run cleanup in dry run mode
        stats = self.cleanup_all()
        
        # Restore original setting
        self.dry_run = original_dry_run
        
        return stats


# Global instance
log_cleanup_service = LogCleanupService()


def run_startup_cleanup():
    """Run cleanup on server startup (if configured)"""
    service = log_cleanup_service
    
    if service.cleanup_schedule in ['startup', 'both']:
        return service.cleanup_all()
    else:
        return {'enabled': False, 'reason': 'cleanup_schedule not set to startup'}


def run_daily_cleanup():
    """Run daily cleanup (if configured)"""
    service = log_cleanup_service
    
    if service.cleanup_schedule in ['daily', 'both']:
        return service.cleanup_all()
    else:
        return {'enabled': False, 'reason': 'cleanup_schedule not set to daily'}
