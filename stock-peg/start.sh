#!/bin/bash

echo "================================"
echo "  Stock PEG 项目启动脚本"
echo "================================"
echo ""
echo "将打开2个窗口:"
echo "  - Server窗口: 后端服务 (端口8000)"
echo "  - Client窗口: 前端服务 (端口5173)"
echo ""

echo "启动后端服务..."
osascript -e 'tell application "Terminal" to do script "cd '$(pwd)'/backend && python main.py"'
sleep 3

echo "启动前端服务..."
osascript -e 'tell application "Terminal" to do script "cd '$(pwd)'/frontend && npm run dev"'

echo ""
echo "================================"
echo "  启动完成！"
echo "================================"
echo ""
echo "后端服务: http://localhost:8000"
echo "前端服务: http://localhost:5173"
echo "API文档:  http://localhost:8000/docs"
echo ""
