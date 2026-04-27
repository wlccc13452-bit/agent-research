# Project Startup Troubleshooting

> Extracted from: `.harness/skills/utils/project-lifecycle/SKILL.md`
> Last Updated: 2026-03-19

---

## Issue: Port Already in Use

**Symptom**: `start.bat` fails with port conflict

**Solution**:
```bash
# Check port usage
netstat -ano | findstr :8000
netstat -ano | findstr :5173

# Kill conflicting process
taskkill /PID [PID] /F

# Retry start
start.bat
```

---

## Issue: Backend Won't Start

**Symptom**: Port 8000 shows no service after `start.bat`

**Diagnosis**:
1. Check backend logs in the opened window
2. Verify `.env` file exists: `backend\.env`
3. Verify Python environment: `backend\.venv\Scripts\python.exe`

**Solution**:
```bash
cd backend

# Check if virtual environment exists
dir .venv\Scripts\python.exe

# Check if main.py exists
dir main.py

# Manually test start
.venv\Scripts\python.exe main.py
```

---

## Issue: Frontend Won't Start

**Symptom**: Port 5173 shows no service after `start.bat`

**Diagnosis**:
1. Check frontend logs in the opened window
2. Verify dependencies installed: `frontend\node_modules`

**Solution**:
```bash
cd frontend

# Install dependencies
npm install

# Manually test start
npm run dev
```

---

## Issue: Services Started but Can't Access

**Symptom**: Ports show LISTENING but browser can't connect

**Diagnosis**:
1. Check firewall settings
2. Verify correct URL (localhost not 127.0.0.1 for IPv6)
3. Check browser console for errors

**Solution**:
- Try `http://[::1]:5173` for IPv6
- Check Windows Firewall settings
- Verify no proxy interfering

---

## Related Files

- **SKILL**: `.harness/skills/utils/project-lifecycle/SKILL.md`
- **Knowledge Base**: `.harness/reference/knowledge-base/`
