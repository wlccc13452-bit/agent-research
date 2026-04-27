# FRONTEND.md - Frontend Development Standards

## Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19.x | UI Framework |
| TypeScript | 5.7 | Type System |
| Vite | 6.x | Build Tool |
| Tailwind CSS | 4.0 | Styling |
| Zustand | 5.0 | Global State Management |
| TanStack Query | 5.66 | Server State Management |
| ECharts | 5.6 | Charts |
| React Router | 7.2 | Routing |

---

## Directory Structure

```
frontend/src/
├── components/       # Reusable UI components
│   └── ui/          # shadcn base components
├── pages/           # Page components (route-level)
├── hooks/           # Custom Hooks
├── services/        # API call layer
├── stores/          # Zustand stores
├── lib/             # Utility functions
├── config/          # Configuration constants
├── contexts/        # React Context (use sparingly)
├── utils/           # General utilities
└── types/           # Type definitions (if separate files needed)
```

---

## Command Runtime Preference

- Use PowerShell-first command examples for frontend development workflows.
- Keep Bash snippets only as optional fallback when cross-platform usage is required.
- Prefer PowerShell path navigation (`Set-Location`) in run instructions.

```powershell
# Install frontend dependencies
Set-Location frontend
npm install

# Start development server
npm run dev

# Run tests
npm run test
```

---

## Interface Scope (No Duplication)

- This file documents frontend consumption contracts and frontend implementation standards only.
- Keep only:
  - How frontend calls `/api/*`
  - How frontend consumes `/ws` push events
  - Query cache and UI refresh strategy
- Do not maintain backend endpoint inventory or MCP tool catalog in this file.
- Backend interface catalog is maintained in `BACKEND.md`.
- Cross-layer topology is maintained in `ARCHITECTURE.md`.

---

## Frontend Integration Contract

### HTTP Contract (Consumption View)

- Base path: `/api/*` (via Vite proxy)
- Frontend must call through `services/` wrappers, not direct fetch in components.
- Error policy: failed requests are surfaced by TanStack Query and rendered with UI fallback.

### WebSocket Contract (Consumption View)

- Endpoint: `ws://localhost:8000/ws` in local development
- Frontend handles push events and maps them to UI refresh:
  - `price_update` → refresh realtime cards
  - `kline_updated` → invalidate kline query cache
  - `holdings_updated` → refresh holdings views
  - `watchlist_updated` → refresh daily watchlist views
  - `fundamental_updated` → refresh fundamental panels

### Cache/Refresh Rules

- Query state is managed by TanStack Query.
- WebSocket event handlers should invalidate related query keys immediately.
- Local UI state (expand/collapse, selected tabs, dialogs) remains in component state or store.

---

## State Management Strategy

### Zustand (Global State)
Used for:
- User preferences
- Theme switching
- Cross-component shared non-server state

```typescript
// stores/stock-store.ts
import { create } from 'zustand';

interface StockState {
  selectedStock: string | null;
  setSelectedStock: (code: string | null) => void;
}

export const useStockStore = create<StockState>((set) => ({
  selectedStock: null,
  setSelectedStock: (code) => set({ selectedStock: code }),
}));
```

### TanStack Query (Server State)
Used for:
- API data fetching
- Cache management
- Auto refresh

```typescript
// services/stock-api.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

export const useStockKLine = (code: string, period: string = 'day') => {
  return useQuery({
    queryKey: ['kline', code, period],
    queryFn: () => fetch(`/api/stocks/${code}/kline?period=${period}`).then(r => r.json()),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};
```

### Local State
Used for:
- Form inputs
- UI interaction state (expand/collapse, loading)
- Component internal state

---

## API Call Standards

### Unified `/api` Prefix
Vite proxy is configured, frontend uses `/api/*` directly.

### Service Layer Wrapper
```typescript
// services/api-client.ts
const API_BASE = '/api';

export async function apiGet<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(`${API_BASE}${path}`, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  }
  const res = await fetch(url);
  if (!res.ok) throw new Error(`API Error: ${res.status}`);
  return res.json();
}
```

### Error Handling
```typescript
// Using TanStack Query error handling
const { data, error, isLoading } = useQuery({
  queryKey: ['stock', code],
  queryFn: () => apiGet<StockData>(`/stocks/${code}`),
  retry: 2,
});

if (error) {
  return <ErrorBanner message={error.message} />;
}
```

---

## Styling Standards

### Tailwind CSS First
```tsx
// ✅ Recommended
<div className="flex items-center gap-2 rounded-lg bg-slate-100 p-4">
  <span className="text-sm font-medium text-slate-700">{label}</span>
</div>

// ❌ Avoid
<div style={{ display: 'flex', padding: '16px' }}>
```

### shadcn Components
Project uses shadcn/ui component library, located in `components/ui/`.

```tsx
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardContent } from '@/components/ui/card';

<Card>
  <CardHeader>
    <CardTitle>Stock Details</CardTitle>
  </CardHeader>
  <CardContent>
    <Button variant="default">View More</Button>
  </CardContent>
</Card>
```

### Responsive Design
```tsx
// Mobile first
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {stocks.map(stock => <StockCard key={stock.code} {...stock} />)}
</div>
```

---

## Component Standards

### Functional Component + Types
```tsx
// components/StockCard.tsx
interface StockCardProps {
  code: string;
  name: string;
  price: number;
  change: number;
  onClick?: () => void;
}

export function StockCard({ code, name, price, change, onClick }: StockCardProps) {
  const isPositive = change >= 0;
  
  return (
    <div 
      className="p-4 rounded-lg border cursor-pointer hover:shadow-md transition-shadow"
      onClick={onClick}
    >
      <div className="font-medium">{name}</div>
      <div className="text-lg font-bold">{price.toFixed(2)}</div>
      <div className={isPositive ? 'text-red-500' : 'text-green-500'}>
        {isPositive ? '+' : ''}{change.toFixed(2)}%
      </div>
    </div>
  );
}
```

### Hooks Usage Order
```tsx
function MyComponent() {
  // 1. State hooks
  const [isOpen, setIsOpen] = useState(false);
  
  // 2. Context / Store hooks
  const user = useUserStore((s) => s.user);
  
  // 3. TanStack Query hooks
  const { data, isLoading } = useStockQuery(code);
  
  // 4. Custom hooks
  const { theme } = useTheme();
  
  // 5. Effects
  useEffect(() => {
    // ...
  }, [deps]);
  
  // 6. Event handlers
  const handleClick = useCallback(() => {
    // ...
  }, [deps]);
  
  // 7. Render
  return <div>...</div>;
}
```

---

## Chart Standards

### ECharts Usage
```tsx
import ReactECharts from 'echarts-for-react';

function KLineChart({ data }: { data: KLineData[] }) {
  const option = {
    xAxis: { type: 'category', data: data.map(d => d.date) },
    yAxis: { type: 'value' },
    series: [{
      type: 'candlestick',
      data: data.map(d => [d.open, d.close, d.low, d.high]),
    }],
  };
  
  return <ReactECharts option={option} style={{ height: 400 }} />;
}
```

---

## Path Aliases

```typescript
// tsconfig.app.json configured
import { Button } from '@/components/ui/button';
import { useStockQuery } from '@/services/stock-api';
import { formatNumber } from '@/lib/utils';
```

---

## Performance Optimization

### Lazy Load Pages
```tsx
// App.tsx
const Dashboard = lazy(() => import('@/pages/Dashboard'));
const StockDetail = lazy(() => import('@/pages/StockDetail'));

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/stock/:code" element={<StockDetail />} />
      </Routes>
    </Suspense>
  );
}
```

### Memo Optimization
```tsx
// Only use when props change frequently and render is expensive
const StockCard = memo(function StockCard({ code, name, price }: StockCardProps) {
  return <div>...</div>;
});
```

---

## WebSocket Integration

### Real-time Data Push
```tsx
// hooks/useWebSocket.ts
import { useEffect, useRef } from 'react';

export function useWebSocket(url: string, onMessage: (data: unknown) => void) {
  const wsRef = useRef<WebSocket | null>(null);
  
  useEffect(() => {
    const ws = new WebSocket(url);
    ws.onmessage = (e) => onMessage(JSON.parse(e.data));
    wsRef.current = ws;
    
    return () => ws.close();
  }, [url, onMessage]);
  
  return wsRef.current;
}

// Usage
function StockPrice() {
  const [price, setPrice] = useState(0);
  
  useWebSocket('ws://localhost:8000/ws', (data) => {
    if (data.type === 'price_update') {
      setPrice(data.price);
    }
  });
  
  return <div>{price}</div>;
}
```

---

## Prohibitions

1. ❌ Directly calling backend database
2. ❌ Reading local files (`自持股票.md` etc.)
3. ❌ Using `any` type
4. ❌ Inline styles (`style={{ }}`)
5. ❌ Class components
6. ❌ Direct `fetch` in components (wrap in service)

---

## MCP Server Integration

The backend exposes MCP Server tools via API endpoints. Frontend can access:

| Tool Category | Backend Endpoint | Frontend Service |
|--------------|------------------|------------------|
| Stock Quotes | `/api/stock/quote/{code}` | `stockApi.getQuote()` |
| K-line Data | `/api/stock/kline/{code}` | `stockApi.getKline()` |
| Technical Indicators | `/api/indicators/force-index/{code}` | `indicatorApi.getForceIndex()` |
| Market Sentiment | `/api/market/sentiment` | `marketApi.getSentiment()` |
| Holdings | `/api/holdings` | `holdingsApi.getAll()` |

See `.harness/skills/api-interaction/SKILL.md` for complete API reference.

---

## Testing Standards

### Component Testing
```bash
npm run test
```

### E2E Testing
```bash
npm run test:e2e
```
