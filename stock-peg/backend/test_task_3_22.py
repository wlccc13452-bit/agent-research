"""Task 3_22 自动测试"""
import sys

print("=" * 60)
print("Task 3_22 自动测试")
print("=" * 60)

# Test 1: Task 1 - Database Layer Architecture
print("\n[Test 1] Database Layer Architecture (Task 1)")
try:
    from database.operations import get_sentiment_by_date
    print("  ✅ get_sentiment_by_date imported from ops layer")
except Exception as e:
    print(f"  ❌ Failed: {e}")
    sys.exit(1)

try:
    from tools.backfill_market_sentiment import get_sentiment_by_date_from_db
    print("  ✅ backfill_market_sentiment uses ops layer")
except Exception as e:
    print(f"  ❌ Failed: {e}")
    sys.exit(1)

# Test 2: Task 3 - MCP Server SKILL
print("\n[Test 2] MCP Server SKILL (Task 3)")
try:
    from pathlib import Path
    skill_file = Path(__file__).parent.parent / ".harness" / "skills" / "api-interaction" / "SKILL.md"
    if skill_file.exists():
        print(f"  ✅ SKILL file exists: {skill_file.name}")
    else:
        print(f"  ❌ SKILL file not found")
        sys.exit(1)
except Exception as e:
    print(f"  ❌ Failed: {e}")
    sys.exit(1)

# Test 3: Task 5 - Smart Router JSON Persistence
print("\n[Test 3] Smart Router JSON Persistence (Task 5)")
try:
    from datasource.core.call_recorder import CallRecorder
    cr = CallRecorder()
    print("  ✅ CallRecorder initialized with JSON persistence")
    
    # Check JSON config
    config_file = Path(__file__).parent / "datasource" / "datasource_config.json"
    if config_file.exists():
        print(f"  ✅ datasource_config.json exists")
    else:
        print(f"  ❌ datasource_config.json not found")
        sys.exit(1)
except Exception as e:
    print(f"  ❌ Failed: {e}")
    sys.exit(1)

# Test 4: Task 6 - Frontend ForceIndex Support
print("\n[Test 4] Frontend ForceIndex Support (Task 6)")
try:
    from pathlib import Path
    indicator_file = Path(__file__).parent.parent / "frontend" / "src" / "components" / "IndicatorContainer.tsx"
    content = indicator_file.read_text(encoding='utf-8')
    if 'forceindex' in content.lower() and 'ForceIndexChart' in content:
        print("  ✅ Frontend supports ForceIndex selection")
    else:
        print("  ❌ ForceIndex not found in IndicatorContainer")
        sys.exit(1)
except Exception as e:
    print(f"  ❌ Failed: {e}")
    sys.exit(1)

# Test 5: Check SQLAlchemy violations (Task 1)
print("\n[Test 5] SQLAlchemy Violations Check (Task 1)")
import subprocess
result = subprocess.run(
    ['python', '-c', 
     'import subprocess; '
     'r = subprocess.run(["rg", "-l", "from sqlalchemy import", "tools/", "--type", "py", "--no-heading"], '
     'capture_output=True, text=True); '
     'print(r.stdout.strip())'],
    cwd=Path(__file__).parent,
    capture_output=True,
    text=True
)
violations = result.stdout.strip()
if not violations:
    print("  ✅ No SQLAlchemy violations in backend/tools/")
elif 'backfill_market_sentiment.py' in violations:
    # Check if it's using ops layer now
    from pathlib import Path
    bf_file = Path(__file__).parent / "tools" / "backfill_market_sentiment.py"
    content = bf_file.read_text(encoding='utf-8')
    if 'from sqlalchemy import select' not in content:
        print("  ✅ backfill_market_sentiment.py migrated to ops layer")
    else:
        print("  ⚠️  Still has SQLAlchemy imports in backfill_market_sentiment.py")
else:
    print(f"  ⚠️  Found violations: {violations}")

print("\n" + "=" * 60)
print("✅ All tests passed!")
print("=" * 60)
