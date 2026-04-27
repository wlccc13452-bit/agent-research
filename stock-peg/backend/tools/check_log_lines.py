"""检查日志文件行数"""
from pathlib import Path

log_dir = Path("d:/play-ground/股票研究/stock-peg/backend/logs")

for log_file in ["app.log", "error.log"]:
    path = log_dir / log_file
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            lines = sum(1 for _ in f)
        print(f"{log_file}: {lines} lines")
    else:
        print(f"{log_file}: not found")
