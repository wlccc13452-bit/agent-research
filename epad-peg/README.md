# EPAD Bot

WeCom bot for stock/financial data research.
1. 管理员权限：code $PROFILE
加入下面代码
···
function Load-Env {
    if (Test-Path .env) {
        Get-Content .env | ForEach-Object {
            # 忽略注释和空行
            if ($_ -match '^[^#].*?=.*$') {
                $name, $value = $_.Split('=', 2)
                $name = $name.Trim()
                $value = $value.Trim().Trim('"').Trim("'")
                [Environment]::SetEnvironmentVariable($name, $value, "Process")
                Write-Host "✅ Loaded: $name" -ForegroundColor Cyan
            }
        }
    } else {
        Write-Warning ".env file not found in current directory."
    }
}
···
node 
1. 重启 PowerShell（或者在当前窗口输入 . $PROFILE）。
2. 确保你当前在 D:\play-ground\股票研究\epad-bot\epad-peg 目录下。
3. 输入命令：load-env
4. 再次运行：codebuddy
如果屏幕输出了你 .env 里的 ID，那么执行 /remote-control 时就不会报错了。
## Quick Start

```bash
# Install dependencies
uv sync --extra dev

# Run the server
uv run epad-bot
```

## API Endpoints

- `GET /api/health` - Health check endpoint
