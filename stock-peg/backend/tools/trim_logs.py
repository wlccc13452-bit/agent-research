"""
日志文件裁剪工具
手动裁剪超过100行的日志文件
"""
import os
from pathlib import Path


def trim_log_file(file_path: str, max_lines: int = 100) -> bool:
    """
    裁剪日志文件，只保留最新的max_lines行
    
    Args:
        file_path: 日志文件路径
        max_lines: 最大保留行数
        
    Returns:
        是否执行了裁剪
    """
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return False
    
    # 读取所有行
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        print(f"{file_path}: 当前 {total_lines} 行")
        
        # 如果行数超过限制，裁剪
        if total_lines > max_lines:
            trimmed_lines = lines[-max_lines:]
            
            # 重新写入
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(trimmed_lines)
            
            print(f"{file_path}: 已裁剪为 {max_lines} 行")
            return True
        else:
            print(f"{file_path}: 行数未超过限制，无需裁剪")
            return False
            
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {e}")
        return False


def main():
    """处理所有日志文件"""
    log_dir = Path(__file__).parent.parent / "logs"
    
    # 需要处理的日志文件
    log_files = [
        log_dir / "app.log",
        log_dir / "error.log"
    ]
    
    print("=" * 60)
    print("日志文件裁剪工具")
    print("=" * 60)
    
    for log_file in log_files:
        if log_file.exists():
            trim_log_file(str(log_file), max_lines=100)
            print()
    
    print("=" * 60)
    print("处理完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
