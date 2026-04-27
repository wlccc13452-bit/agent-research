# Frontend UI Testing

## Skill Name
frontend-ui-test

## Description
Automated frontend UI testing using Playwright to verify page rendering, data display, and user interactions.

## Trigger Phrases
- "test frontend UI"
- "verify UI display"
- "check if stock shows on page"
- "自动测试网页"
- "/test-ui"

## Mandatory Read Order
1. `.harness/memory/core-facts.md` - Environment ports and constraints
2. `.harness/AGENTS.md` - Global rules

---

## Step-by-Step Execution

### Phase 1: Environment Setup

1. **Check services running**:
   ```bash
   # Backend on port 8000
   curl http://localhost:8000/docs
   # Frontend on port 5173
   curl http://localhost:5173
   ```

2. **Install Playwright if needed**:
   ```bash
   cd backend
   uv add playwright
   uv run playwright install chromium
   ```

### Phase 2: Create Test Script

3. **Create test script in `test/temp/ui-test/`**:
   - Location: `test/temp/ui-test/test_ui.py`
   - Purpose: Verify specific UI functionality
   - Include: Screenshot capture for debugging

### Phase 3: Execute Test

4. **Run the test**:
   ```bash
   cd backend
   uv run python ../test/temp/ui-test/test_ui.py
   ```

5. **Verify results**:
   - Check console output
   - Review screenshots in `test/temp/ui-test/screenshots/`
   - Confirm test assertions pass

### Phase 4: Report Results

6. **Display test results to user**:
   - Screenshot paths
   - Test pass/fail status
   - Any errors found

---

## Prohibitions (Hard Rules – Never Violate)

### Test Isolation
- ❌ NEVER run tests against production URLs
- ❌ NEVER leave browser windows open after test
- ❌ NEVER skip screenshot capture for debugging

### Performance
- ❌ NEVER run tests in parallel without proper isolation
- ❌ NEVER forget to close Playwright context

### Data Integrity
- ❌ NEVER modify database during UI tests
- ❌ NEVER create test data in production schema

---

## Allowed Tools
- `execute_command` - Run test scripts
- `read_file` - Read test files
- `write_to_file` - Create test scripts
- `web_fetch` - Simple HTTP requests (not for JS-rendered pages)

---

## Output Format

```
**Frontend UI Test Report**

**Test Target**: [URL or page name]
**Test Date**: [YYYY-MM-DD HH:MM:SS]

**Results**:
- ✅ [Test 1 name]: PASSED
- ❌ [Test 2 name]: FAILED - [Reason]
- ✅ [Test 3 name]: PASSED

**Screenshots**:
- Before: `test/temp/ui-test/screenshots/before.png`
- After: `test/temp/ui-test/screenshots/after.png`

**Summary**: [X] tests passed, [Y] tests failed
```

---

## Example Test Script Template

```python
# test/temp/ui-test/test_ui.py
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime

async def test_watchlist_display():
    """Test if daily watchlist shows on Holdings page"""
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Navigate to Holdings page
            await page.goto('http://localhost:5173', wait_until='networkidle')
            await page.wait_for_timeout(2000)  # Wait for data load
            
            # Take screenshot
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = f'test/temp/ui-test/screenshots/watchlist_{timestamp}.png'
            await page.screenshot(path=screenshot_path, full_page=True)
            
            # Check if watchlist section exists
            watchlist_section = await page.query_selector('text=每日关注')
            assert watchlist_section is not None, "Watchlist section not found"
            
            # Check if stock is displayed
            stock_element = await page.query_selector('text=方正科技')
            assert stock_element is not None, "Stock '方正科技' not found on page"
            
            print(f"✅ Test PASSED: Watchlist and stock displayed correctly")
            print(f"📸 Screenshot: {screenshot_path}")
            
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(test_watchlist_display())
```

---

## Troubleshooting

### Issue: Playwright not found
**Solution**: Install Playwright
```bash
cd backend
uv add playwright
uv run playwright install chromium
```

### Issue: Page not loading
**Solution**: Check services are running
```bash
curl http://localhost:8000/docs
curl http://localhost:5173
```

### Issue: Element not found
**Solution**: Increase wait time or check selector
```python
await page.wait_for_selector('text=每日关注', timeout=10000)
```

### Issue: Screenshot directory not found
**Solution**: Create directory
```bash
mkdir -p test/temp/ui-test/screenshots
```

---

## Related Skills
- `project-lifecycle` - Start/stop services
- `memory-update-protocol` - Update progress after test

---

## Notes

### Why Playwright?
- Handles JavaScript-rendered pages (React)
- Better than Selenium for modern web apps
- Supports async/await
- Built-in screenshot and video capture
- Works with Vite dev server

### Test Best Practices
1. Always use `headless=True` for automated tests
2. Always close browser context
3. Always capture screenshots for debugging
4. Use meaningful assertion messages
5. Wait for network idle before checking elements

### Integration with Development Workflow
- Run after frontend changes
- Run after API changes
- Run before committing code
- Include in CI/CD pipeline (future)

---

**Version**: 1.0  
**Last Updated**: 2026-03-14
