# Project Lifecycle Management

## Skill Name
project-lifecycle

## Description
Start and stop Stock PEG project services (backend + frontend) using standardized batch scripts.

## Trigger Phrases
- "启动项目"
- "start project"
- "关闭项目"
- "stop project"
- "启动服务"
- "start services"
- "/start"
- "/stop"
- "运行项目"
- "run project"

## Mandatory Read Order
1. `.harness/memory/core-facts.md` - Environment ports and constraints
2. `.harness/AGENTS.md` - Global rules

---

## Step-by-Step Execution

### START PROJECT

#### Single Step: Execute Start Script
1. Run `start.bat` **ONCE** and wait for completion:
   ```bash
   d:/2026projects/stocks-research/stock-peg/start.bat
   ```

2. **DO NOT** run any additional verification commands
   - `start.bat` handles all cleanup, startup, and verification internally
   - Wait for the script to complete (~10 seconds)
   - Script will open 2 new PowerShell windows automatically

3. Display service status to user after script completes:
   - Frontend: http://localhost:5173
   - Backend: http://localhost:8000
   - API Docs: http://localhost:8000/docs

**CRITICAL:**
- ✅ Execute `start.bat` exactly **ONCE**
- ❌ DO NOT run `netstat` or `curl` after `start.bat`
- ❌ DO NOT run any additional commands
- ✅ Simply wait for script to finish and display URLs

---

### STOP PROJECT

#### Phase 1: Service Discovery
1. Check running services:
   ```bash
   netstat -ano | findstr :8000
   netstat -ano | findstr :5173
   ```

#### Phase 2: Execute Stop Script
2. If services running, kill processes:
   ```bash
   # Kill backend (port 8000)
   for /f "tokens=5" %a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do taskkill /PID %a /F
   
   # Kill frontend (port 5173)
   for /f "tokens=5" %a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do taskkill /PID %a /F
   ```

3. Alternative: Run cleanup script if available:
   ```bash
   cd d:/2026projects/stocks-research/stock-peg
   kill-end.bat
   ```

#### Phase 3: Verification
4. Verify services stopped:
   ```bash
   netstat -ano | findstr :8000
   netstat -ano | findstr :5173
   ```
   - Expected: No output (ports free)

5. Confirm to user: "All services stopped successfully"

---

## Prohibitions (Hard Rules – Never Violate)

### Service Management
- ❌ NEVER manually start services without using `start.bat`
- ❌ NEVER run `start.bat` more than once per startup
- ❌ NEVER run additional verification commands (netstat, curl) after `start.bat`
- ❌ NEVER assume services are running without checking
- ❌ NEVER kill processes without confirming they are Stock PEG services

### Port Safety
- ❌ NEVER start services if ports already in use by other applications
- ❌ NEVER use ports other than 8000 (backend) and 5173 (frontend)

### Process Management
- ❌ NEVER kill processes by name alone (always verify port first)
- ❌ NEVER leave orphaned processes running

---

## Allowed Tools
- `execute_command` - Run shell commands
- `read_file` - Read configuration files

---

## Output Format

### Start Success
```
✅ **Project Started Successfully**

**Services Running:**
- 🟢 Frontend: http://localhost:5173
- 🟢 Backend: http://localhost:8000
- 📚 API Docs: http://localhost:8000/docs

**Process Info:**
- Backend PID: [PID from netstat]
- Frontend PID: [PID from netstat]

Ready for development!
```

### Stop Success
```
✅ **Project Stopped Successfully**

**Services Terminated:**
- Backend (port 8000) - Stopped
- Frontend (port 5173) - Stopped

All processes cleaned up.
```

### Already Running
```
⚠️ **Services Already Running**

**Current Status:**
- Frontend: http://localhost:5173 (PID: [PID])
- Backend: http://localhost:8000 (PID: [PID])

Use "/stop" to restart or continue with current services.
```

---

## Troubleshooting

> **For detailed troubleshooting steps, see `.harness/reference/knowledge-base/PROJECT_STARTUP_ERRORS.md`**

Common issues:
- Port already in use → Check and kill conflicting processes
- Backend won't start → Verify `.env` and `.venv`
- Frontend won't start → Run `npm install`
- Can't access services → Check firewall and IPv6

---

## Related Skills
- `python-env-management` - Python environment setup
- `market-check` - Test market data API after startup

---

## Notes

### Why Execute `start.bat` ONLY ONCE?
1. **All-in-One Script**: `start.bat` handles everything:
   - Cleans up old processes (ports 8000, 5173)
   - Starts backend in new window
   - Waits 5 seconds for initialization
   - Starts frontend in new window
   - Verifies services started
   
2. **No Additional Commands Needed**:
   - ❌ Don't run `netstat` (script already does this)
   - ❌ Don't run `curl` (script handles verification)
   - ❌ Don't run multiple `start.bat` calls
   
3. **Single Execution Principle**:
   - One command: `start.bat`
   - Wait for completion (~10 seconds)
   - Done - services are ready

### Service Architecture
```
start.bat (execute ONCE)
  ├─ Clean up old processes (ports 8000, 5173)
  ├─ Kill orphaned node.exe and python.exe
  ├─ Start backend (new PowerShell window #1)
  │   └─ FastAPI on port 8000
  ├─ Wait 5 seconds for backend initialization
  ├─ Start frontend (new PowerShell window #2)
  │   └─ Vite on port 5173
  └─ Display service URLs and exit
```

### Port Configuration
- **Backend**: 8000 (configurable in `.env` and `settings.py`)
- **Frontend**: 5173 (Vite default, configurable in `vite.config.ts`)
- **Alternative Frontend**: 5175 (used if 5173 occupied)

---

## Remember

**This SKILL ensures:**
- ✅ Consistent project startup across all sessions
- ✅ No port conflicts or orphaned processes
- ✅ Clear verification of service health
- ✅ Standardized troubleshooting procedures
