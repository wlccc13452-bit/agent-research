# CODEBUDDY.md

This file provides guidance to CodeBuddy Code when working with code in this repository.

## Project Overview

EPAD Bot is a FastAPI-based WeCom (WeChat Work) bot service for stock/financial data research. It connects to WeCom via WebSocket for real-time messaging.


function load-env {
    $envFile = ".env"
    if (Test-Path $envFile) {
        Get-Content $envFile | ForEach-Object {
            $line = $_.Trim()
            if ($line -and !$line.StartsWith("#") -and $line.Contains("=")) {
                $name, $value = $line.Split("=", 2)
                $name = $name.Trim()
                $value = $value.Trim().Trim('"').Trim("'")
                [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
                Write-Host "Successful Load: $name" -ForegroundColor Cyan
            }
        }
    } else {
        Write-Error "Error: .env file not found in current directory."
    }
}



## Commands

```bash
# Install dependencies
uv sync

# Install with dev dependencies
uv sync --extra dev

# Run the development server
uv run epad-bot

# Or run directly with uvicorn
uv run uvicorn epad_bot.main:app --reload

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src

# Run a single test file
uv run pytest tests/test_api.py

# Run linter
uv run ruff check src tests

# Run linter with auto-fix
uv run ruff check --fix src tests

# Run type checker
uv run mypy src
```

## Project Structure

```
src/epad_bot/
├── __init__.py      # Package version
├── main.py          # FastAPI app entry point
├── config.py        # Pydantic settings from environment
├── api/
│   └── routes.py    # API route handlers
├── services/
│   └── wecom_client.py  # WebSocket client for WeCom
├── models/          # Pydantic models for request/response
└── utils/           # Helper utilities

tests/               # Test files
```

## Environment Configuration

Environment variables are loaded from `.bot_env`/`.env` and use the `CODEBUDDY_` prefix:

| Variable             | Description                                                 |
| -------------------- | ----------------------------------------------------------- |
| `CODEBUDDY_WECOM_BOT_ID`     | WeCom bot identifier                                        |
| `CODEBUDDY_WECOM_BOT_SECRET` | WeCom bot authentication secret                             |
| `CODEBUDDY_WECOM_BOT_WS_URL` | WebSocket URL (default:`wss://openws.work.weixin.qq.com`) |
| `CODEBUDDY_HOST`             | Server host (default:`0.0.0.0`)                           |
| `CODEBUDDY_PORT`             | Server port (default:`8100`)                              |
| `CODEBUDDY_DEBUG`            | Enable debug mode (default:`false`)                       |

## Key Architecture

- **FastAPI Application**: Main entry point in `main.py` with lifecycle events for startup/shutdown
- **Configuration**: Uses `pydantic-settings` to load configuration from `.env`
- **WeCom Client**: Async WebSocket client in `services/wecom_client.py` for real-time messaging
- **Settings Caching**: `get_settings()` is cached with `@lru_cache` for performance
