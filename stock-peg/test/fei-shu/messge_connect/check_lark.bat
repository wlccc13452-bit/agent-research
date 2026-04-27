@echo off
cd /d d:\play-ground\股票研究\stock-peg\backend
.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, '.'); from services.feishu_long_connection_service import feishu_long_connection_service, LARK_AVAILABLE; print('LARK_AVAILABLE:', LARK_AVAILABLE); print('enabled:', feishu_long_connection_service.enabled)"
