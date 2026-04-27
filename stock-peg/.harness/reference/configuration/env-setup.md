# Environment Configuration Guide

**Priority**: Standard
**Last Updated**: 2026-03-15

This document explains how to configure the Stock PEG project environment.

---

## Configuration Files Location

```
stock-peg/
├── backend/
│   └── config/
│       ├── .env           # Backend configuration (API keys, ports)
│       └── .env.example   # Configuration template
└── frontend/
    ├── .env               # Frontend configuration (API address)
    └── .env.example       # Configuration template
```

---

## Key Configuration Items

### 1. Server Port Configuration

**Backend Configuration** (`backend/config/.env`):
```env
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

**Frontend Configuration** (`frontend/.env`):
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

**Important**:
- After modifying backend port, must also update frontend configuration
- Restart both frontend and backend services after changes

---

### 2. API Key Configuration

Configure the following keys in `backend/config/.env`:

| Configuration | Purpose | Get from |
|--------------|---------|----------|
| `TUSHARE_TOKEN` | A-share financial data | https://tushare.pro/register |
| `ZHIPU_API_KEY` | Zhipu AI analysis service | https://open.bigmodel.cn/ |
| `ALPHAVANTAGE_API_KEY` | US stock data source (recommended) | https://www.alphavantage.co/support/#api-key |
| `FINNHUB_API_KEY` | US stock data source (backup) | https://finnhub.io/register |

---

### 3. Layout Configuration

Backend layout configuration: `backend/config/layout.ini`

```ini
[layout]
left_panel_width = 15      # Left panel width (%)
right_panel_width = 20     # Right panel width (%)
center_panel_min_width = 20 # Center minimum width (%)
headbar_height = 56        # Top bar height (pixels)
statusbar_height = 32      # Bottom bar height (pixels)
```

---

## Quick Setup Steps

### 1. First-time Setup

```bash
# 1. Copy configuration templates
cp backend/config/.env.example backend/config/.env
cp frontend/.env.example frontend/.env

# 2. Edit backend configuration, fill in your API keys
nano backend/config/.env

# 3. Frontend configuration defaults to port 8001, no changes needed (unless backend port changes)
```

---

### 2. Modify Port

If you need to change port (e.g., to 8002):

```bash
# 1. Modify backend configuration
# backend/config/.env
SERVER_PORT=8002

# 2. Modify frontend configuration
# frontend/.env
VITE_API_BASE_URL=http://localhost:8002
VITE_WS_URL=ws://localhost:8002/ws

# 3. Restart services
```

---

### 3. Check Current Port Usage

```bash
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000
```

---

## Configuration Verification

### Backend Verification

After starting backend service, visit:
- Health check: http://localhost:8000/health
- API docs: http://localhost:8000/docs

### Frontend Verification

After starting frontend service, visit:
- Application: http://localhost:5173

---

## Common Issues

### Q1: Port Already in Use?

```bash
# Windows - Find and kill process
netstat -ano | findstr :8000
taskkill /F /PID <process_id>

# Linux/Mac
lsof -i :8000
kill -9 <process_id>
```

---

### Q2: API Key Invalid?

- Confirm key is correctly entered in `backend/config/.env`
- Check for spaces or quotes in key
- Verify key is valid (not expired)

---

### Q3: Frontend Cannot Connect to Backend?

1. Check if backend is running: visit http://localhost:8000/health
2. Check frontend configuration: confirm `frontend/.env` port matches backend
3. Check firewall: ensure port is not blocked
4. Check CORS: backend has CORS configured, should not have CORS issues

---

### Q4: Configuration Changes Not Taking Effect?

- Restart services after modifying configuration files
- Frontend may need cache clear: `Ctrl+Shift+R` hard refresh

---

## Security Tips

- **Do NOT commit `.env` files to Git** (excluded in `.gitignore`)
- **Only commit `.env.example` template files**
- **Do NOT share API keys with others**
- **Production environment: use environment variables instead of `.env` files**

---

## Related Documents

- Project Structure: `.harness/ARCHITECTURE.md`
- Backend Guide: `.harness/BACKEND.md`
- Frontend Guide: `.harness/FRONTEND.md`
- Progress: `.harness/progress.md`

---

**Last Updated**: 2026-03-13
