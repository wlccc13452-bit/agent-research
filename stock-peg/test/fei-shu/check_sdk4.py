import lark_oapi
from lark_oapi.event.dispatcher_handler import EventDispatcherHandler
import inspect

# 创建 builder
print("=== EventDispatcherHandlerBuilder ===")
builder = EventDispatcherHandler.builder("", "")
print(f"Builder type: {type(builder)}")
print(f"Builder class: {builder.__class__.__name__}")

# 检查 builder 的方法
methods = [m for m in dir(builder) if not m.startswith('_')]
print(f"\nBuilder methods: {methods}")

# 查找 register 方法
print("\n=== Looking for register methods ===")
for method in methods:
    if 'register' in method.lower():
        print(f"Found: {method}")
        try:
            m = getattr(builder, method)
            if callable(m):
                sig = inspect.signature(m)
                print(f"  {method} params: {sig}")
        except Exception as e:
            print(f"  {method} error: {e}")

# 尝试查找消息相关的注册方法
print("\n=== Looking for message-related methods ===")
for method in methods:
    if 'message' in method.lower() or 'im' in method.lower() or 'p2' in method.lower():
        print(f"Found: {method}")
