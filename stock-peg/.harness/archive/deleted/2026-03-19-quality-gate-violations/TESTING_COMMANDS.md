# Testing Commands

## Backend Testing

```powershell
cd backend

# Linting
uv run ruff check .

# Type checking
uv run mypy .

# Unit tests
uv run pytest

# All-in-one
uv run ruff check . && uv run mypy . && uv run pytest
```

## Frontend Testing

```powershell
cd frontend

# Linting
npm run lint

# Build check
npm run build

# Type check
npm run type-check  # if available
```

## API Testing with curl

```powershell
# Health check
curl http://localhost:8000/health

# Indicator endpoint (use stock code for stability)
curl http://localhost:8000/api/indicators/force-index/601898

# Batch endpoint
curl -X POST http://localhost:8000/api/indicators/force-index-batch \
  -H "Content-Type: application/json" \
  -d '{"codes": ["601898", "600519"]}'
```

## Database Testing

```powershell
# Check database file
ls backend/data/*.db

# Query database
cd backend
uv run python -c "
from sqlalchemy import create_engine, text
engine = create_engine('sqlite:///data/stock_peg.db')
with engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM stock_kline_data'))
    print(result.scalar())
"
```
