client 只向server要求本地数据，如果server发现不存在或者没有更新，client不应等待server更新数据！，server应在后台更新后再推送给client，client不可以向让server，”同步服务器本地行情“是否存在问题不满足要求？检查项目是否存在问题！



移除客户端主动触发的“强制更新”逻辑和UI。

检查并修改 LoadingScreen.tsx 和 EnhancedLoadingScreen.tsx，移除“同步服务器本地行情”步骤或重命名为“加载本地行情数据”，并确保非阻塞。

禁用客户端触发的 /force-update 接口。

移除“同步服务器本地行情”步骤或重命名为“加载本地行情数据”，并确保非阻塞。

确保数据缺失时立即返回并异步启动后台更新。

移除或限制客户端触发的 /force-update 接口。

确保在数据缺失时立即返回 404 或旧数据，并静默启动后台更新。

验证 WebSocket 推送机制，确保后台更新完成后前端能自动刷新。

验证 WebSocket 推送机制 (background_updater.py)，确保后台更新完成后前端能自动接收数据。
