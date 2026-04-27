"""
飞书机器人权限检查脚本
检查应用配置和权限是否正确
"""
import json
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

if not APP_ID or not APP_SECRET:
    print("[错误] 未找到飞书配置")
    exit(1)

print("="*60)
print("飞书机器人权限检查")
print("="*60)
print(f"\n[App ID] {APP_ID}")
print(f"[配置文件] backend/.env")

# 尝试获取 tenant_access_token
import lark_oapi as lark

try:
    client = lark.Client.builder() \
        .app_id(APP_ID) \
        .app_secret(APP_SECRET) \
        .log_level(lark.LogLevel.ERROR) \
        .build()
    
    print("\n[测试1] 获取 tenant_access_token")
    print("  正在获取访问令牌...")
    
    # 获取 tenant_access_token（使用内部接口）
    import requests
    
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload = {
        "app_id": APP_ID,
        "app_secret": APP_SECRET
    }
    
    resp = requests.post(url, json=payload)
    data = resp.json()
    
    if data.get("code") == 0:
        token = data.get("tenant_access_token", "")
        expire = data.get("expire", 0)
        print(f"  [成功] tenant_access_token 已获取")
        print(f"  [令牌] {token[:20]}...")
        print(f"  [过期] {expire} 秒")
    else:
        print(f"  [失败] {data.get('code')}: {data.get('msg')}")
        exit(1)
    
    print("\n[测试2] 权限检查")
    print("  [必需权限]")
    print("  - im:message (获取消息)")
    print("  - im:message:send_as_bot (发送消息)")
    print("  - im:message:receive_as_bot (接收消息)")
    print("  [操作] 请在飞书开放平台确认以上权限")
    
    print("\n[测试3] 事件订阅检查")
    print("  [必需事件]")
    print("  - im.message.receive_v1 (接收消息)")
    print("  [操作] 请在飞书开放平台确认事件订阅")
    
except Exception as e:
    print(f"\n[异常] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("检查完成")
print("="*60)
print("\n[配置步骤]")
print(f"1. 访问: https://open.feishu.cn/app/{APP_ID}/")
print("2. 权限管理 → 消息 → 开通以下权限:")
print("   - im:message")
print("   - im:message:send_as_bot")
print("   - im:message:receive_as_bot")
print("3. 事件订阅 → 订阅事件列表 → 添加:")
print("   - im.message.receive_v1")
print("4. 版本管理 → 创建版本并发布")
print("\n[文档] 详细说明: FEISHU_CONFIG_CHECKLIST.md")

