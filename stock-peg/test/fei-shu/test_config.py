"""
快速测试飞书配置
"""
from pathlib import Path

# 加载配置
def load_env_values() -> dict[str, str]:
    candidates = [
        Path(__file__).resolve().parent / ".env",
        Path(__file__).resolve().parents[2] / "backend" / ".env",
    ]
    env_path = None
    for path in candidates:
        if path.exists():
            env_path = path
            break
    if not env_path:
        env_path = candidates[0]
    
    values: dict[str, str] = {}
    if not env_path.exists():
        return values
    
    with env_path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values

ENV_VALUES = load_env_values()
APP_ID = ENV_VALUES.get("FEISHU_APP_ID", "")
APP_SECRET = ENV_VALUES.get("FEISHU_APP_SECRET", "")

print(f"[配置文件路径] {Path(__file__).resolve().parents[2] / 'backend' / '.env'}")
print(f"[文件存在] {(Path(__file__).resolve().parents[2] / 'backend' / '.env').exists()}")
print(f"[App ID] {APP_ID[:10]}..." if APP_ID else "[错误] 未找到 FEISHU_APP_ID")
print(f"[App Secret] {APP_SECRET[:10]}..." if APP_SECRET else "[错误] 未找到 FEISHU_APP_SECRET")
print(f"[配置项数量] {len(ENV_VALUES)}")

if APP_ID and APP_SECRET:
    print("\n[状态] 配置正确，可以运行 bot_chat.py")
else:
    print("\n[错误] 请检查 backend/.env 配置文件")
