# -*- coding: utf-8 -*-
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

print("Checking Lark SDK availability...")

try:
    import lark_oapi as lark
    print("lark_oapi imported successfully")
    print(f"lark_oapi version: {lark.__version__ if hasattr(lark, '__version__') else 'unknown'}")
except ImportError as e:
    print(f"FAILED to import lark_oapi: {e}")

try:
    from lark_oapi.ws import Client as WSClient
    print("WSClient imported successfully")
except ImportError as e:
    print(f"FAILED to import WSClient: {e}")

try:
    from services.feishu_long_connection_service import feishu_long_connection_service, LARK_AVAILABLE
    print(f"LARK_AVAILABLE: {LARK_AVAILABLE}")
    print(f"Service enabled: {feishu_long_connection_service.enabled}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
