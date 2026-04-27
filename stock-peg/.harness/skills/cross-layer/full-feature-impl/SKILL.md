# Full Feature Implementation SOP

## Purpose
Define standardized process for cross-stack feature development, ensuring consistency and completeness.

---

## Prerequisites

Before starting, confirm:
- [ ] Read `.harness/progress.md` to understand current progress
- [ ] Read `.harness/decisions.md` to understand existing decisions
- [ ] Read `.harness/memory/core-facts.md` to understand style preferences

---

## Development Process

### Phase 1: Design

#### 1.1 Define Requirements
```markdown
## Feature Name: xxx

### User Story
As [role], I want [behavior], so that [value]

### Data Structure
- Input: ...
- Output: ...
- Storage: ...
```

#### 1.2 Design API
```
POST /api/xxx
Request: { ... }
Response: { ... }
```

#### 1.3 Record Decision
If there are technical decisions, update `.harness/decisions.md`.

---

### Phase 2: Backend Implementation

#### 2.1 Data Model
```python
# database/models.py
class NewModel(Base):
    __tablename__ = "new_table"
    ...
```

#### 2.2 Pydantic Schema
```python
# models/xxx.py
class XxxRequest(BaseModel):
    ...

class XxxResponse(BaseModel):
    ...
```

#### 2.3 Service Layer
```python
# services/xxx_service.py
class XxxService:
    async def do_something(self, ...) -> ...:
        """Business logic"""
        ...
```

#### 2.4 Router Layer
```python
# routers/xxx.py
@router.post("/xxx")
async def handle_xxx(request: XxxRequest, db: AsyncSession = Depends(get_db)):
    service = XxxService(db)
    return await service.do_something(**request.model_dump())
```

#### 2.5 Register Router
```python
# main.py
from routers.xxx import router as xxx_router
app.include_router(xxx_router, prefix="/api/xxx", tags=["XXX"])
```

#### 2.6 Test API
```bash
# Start backend
cd backend && uv run python main.py

# Test
curl http://localhost:8000/api/xxx
```

---

### Phase 3: Frontend Implementation

#### 3.1 API Service Layer
```typescript
// services/xxx-api.ts
export async function fetchXxx(params: XxxParams): Promise<XxxResponse> {
  return apiGet('/api/xxx', params);
}
```

#### 3.2 TanStack Query Hook
```typescript
// hooks/useXxx.ts
export function useXxx(params: XxxParams) {
  return useQuery({
    queryKey: ['xxx', params],
    queryFn: () => fetchXxx(params),
  });
}
```

#### 3.3 UI Component
```typescript
// components/XxxCard.tsx
export function XxxCard({ data }: XxxCardProps) {
  return (
    <Card>
      <CardHeader>...</CardHeader>
      <CardContent>...</CardContent>
    </Card>
  );
}
```

#### 3.4 Page Component
```typescript
// pages/XxxPage.tsx
export function XxxPage() {
  const { data, isLoading } = useXxx(...);
  
  if (isLoading) return <Loading />;
  
  return <XxxCard data={data} />;
}
```

#### 3.5 Add Route
```typescript
// App.tsx
<Route path="/xxx" element={<XxxPage />} />
```

#### 3.6 Test Frontend
```bash
cd frontend && npm run dev
# Open http://localhost:5173/xxx
```

---

### Phase 4: Integration Testing (MANDATORY)

**⚠️ CRITICAL: This phase is MANDATORY and must be completed before marking feature as done.**

#### 4.1 Backend API Testing

**Step 1: Start Backend Server**
```bash
cd backend
uv run python main.py
# Or use project start script
d:\2026projects\stocks-research\stock-peg\start.bat
```

**Step 2: Test API Endpoints with curl**
```bash
# Test GET endpoint
curl http://localhost:8000/api/xxx

# Test POST endpoint
curl -X POST http://localhost:8000/api/xxx \
  -H "Content-Type: application/json" \
  -d '{"param1": "value1", "param2": "value2"}'

# Test error case (invalid input)
curl -X POST http://localhost:8000/api/xxx \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}'

# Check response time (should be < 1s for non-blocking)
curl -w "@-" -o /dev/null -s http://localhost:8000/api/xxx <<'EOF'
    time_namelookup:  %{time_namelookup}s\n
       time_connect:  %{time_connect}s\n
    time_appconnect:  %{time_appconnect}s\n
      time_redirect:  %{time_redirect}s\n
   time_starttransfer:  %{time_starttransfer}s\n
       time_total:  %{time_total}s\n
EOF
```

**Step 3: Verify Database Session Usage**
- [ ] Check all router functions use `db: AsyncSession = Depends(get_db)`
- [ ] NO `async for session in db:` (this is WRONG)
- [ ] Direct use of `db` parameter in service calls
- [ ] Example of CORRECT usage:
```python
@router.post("/xxx")
async def handle_xxx(request: XxxRequest, db: AsyncSession = Depends(get_db)):
    result = await service.do_something(db, **request.model_dump())
    return result
```

**Step 4: Check Database Records**
```bash
# Use sqlite3 to verify data
sqlite3 backend/data/stock_peg.db
> SELECT * FROM new_table LIMIT 5;
> .quit
```

**Step 5: Backend Checklist**
- [ ] API returns correct response format
- [ ] Error handling returns proper HTTP status codes
- [ ] Response time < 1s (non-blocking principle)
- [ ] Database operations work correctly
- [ ] No `async for session in db` in routers

#### 4.2 Frontend Integration Testing

**Step 1: Start Frontend**
```bash
cd frontend
npm run dev
```

**Step 2: Open Browser and Test**
```
Open: http://localhost:5173/xxx
```

**Step 3: Browser Console Check**
- Open DevTools (F12)
- Check Console tab for errors
- Check Network tab for API calls
- Verify response data structure

**Step 4: Test User Interactions**
- [ ] Page loads without errors
- [ ] Loading state displays correctly
- [ ] Data renders from API
- [ ] Error state displays if API fails
- [ ] User actions trigger correct API calls

#### 4.3 End-to-End Testing

**Step 1: Complete User Flow**
- Perform complete user operation from start to finish
- Verify each step works
- Check data persists correctly

**Step 2: WebSocket Testing (if applicable)**
- [ ] Backend broadcasts update
- [ ] Frontend receives WebSocket message
- [ ] UI updates automatically

**Step 3: Cross-Browser Testing**
- [ ] Test in Chrome
- [ ] Test in Firefox
- [ ] Test in Edge (optional)

**Step 4: Mobile Testing (if applicable)**
- [ ] Test responsive layout
- [ ] Test touch interactions

#### 4.4 Document Test Results

**Create Test Report**:
```markdown
## Test Report: [Feature Name]

Date: YYYY-MM-DD
Tester: AI Agent

### Backend Tests
- [x] API endpoint returns correct response
- [x] Error handling works
- [x] Response time: 0.3s (PASS)
- [x] Database session usage correct (PASS)

### Frontend Tests
- [x] Page loads without errors
- [x] Data displays correctly
- [x] No console errors

### Issues Found
- None

### Conclusion
✅ Feature tested and working correctly
```

#### 4.5 Failure Protocol

**If ANY test fails:**

1. **STOP**: Do NOT mark feature as complete
2. **DEBUG**: Investigate the root cause
3. **FIX**: Correct the issue
4. **RE-TEST**: Run all tests again from Phase 4.1
5. **DOCUMENT**: Note the issue and fix in test report

**Common Issues and Fixes:**
- Issue: `'async for' requires an object with __aiter__ method`
  - Fix: Change `async for session in db` to direct `db` usage
  
- Issue: API returns 404
  - Fix: Check router registration in main.py
  
- Issue: Frontend can't reach API
  - Fix: Check Vite proxy configuration

**NO FEATURE IS COMPLETE UNTIL ALL TESTS PASS**

---

### Phase 5: Cleanup

#### 5.1 Update Documentation
- [ ] Update `progress.md`
- [ ] Create session summary (if needed)

#### 5.2 Commit Code
```bash
git add .
git commit -m "feat: implement xxx feature"
git push
```

---

## Checklist

### Backend Checklist
- [ ] Type annotations complete
- [ ] Async operations correct
- [ ] Non-blocking principle
- [ ] Error handling complete
- [ ] Logging reasonable

### Frontend Checklist
- [ ] TypeScript no errors
- [ ] Component reusable
- [ ] Loading state handled
- [ ] Error state handled
- [ ] Responsive design

### Cross-Layer Checklist
- [ ] API contract consistent
- [ ] Data flow clear
- [ ] No direct database access (frontend)

---

## Example: Adding "Stock Alert" Feature

### Phase 1
```markdown
## Feature Name: Stock Alert

### User Story
As an investor, I want to set price alerts, so I can get notified when stock price reaches target

### API Design
POST /api/alerts
Request: { code: string, target_price: number, direction: "up"|"down" }
Response: { id: string, code: string, target_price: number, status: "active" }
```

### Phase 2-5
Follow the process above...

---

## FAQ

### Q: When modifying both frontend and backend, what's the order?
A: Backend first, then frontend. Ensure API is stable before developing frontend.

### Q: What to do when adding new dependencies?
A:
- Backend: Modify `pyproject.toml`, run `uv sync`
- Frontend: Run `npm install <package>`
- Include lock files in commit

### Q: What to do when facing technical decision conflicts?
A: Record in `decisions.md`, note reasons and alternatives, let user decide.
