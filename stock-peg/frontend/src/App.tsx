import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import './App.css';

// 导入组件
import HeadBar from './components/HeadBar';
import { StockLoadingProvider } from './contexts/StockLoadingContext';

// 导入页面组件
import Dashboard from './pages/Dashboard';
import Predictions from './pages/Predictions';
import Reports from './pages/Reports';
import USMarket from './pages/USMarket';
import StockDetail from './pages/StockDetail';
import Feishu from './pages/Feishu';

// 创建 Query Client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

// 全局状态Context
interface AppContextType {
  selectedStockSector: string | undefined;
  setSelectedStockSector: (sector: string | undefined) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function useAppContext() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within AppProvider');
  }
  return context;
}

function AppProvider({ children }: { children: ReactNode }) {
  const [selectedStockSector, setSelectedStockSector] = useState<string | undefined>();

  return (
    <AppContext.Provider value={{ selectedStockSector, setSelectedStockSector }}>
      {children}
    </AppContext.Provider>
  );
}

function App() {
  useEffect(() => {
    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      const message =
        event.reason instanceof Error
          ? event.reason.message
          : typeof event.reason === 'string'
            ? event.reason
            : '';

      // 忽略音频播放相关的错误（浏览器自动播放策略导致）
      if (
        message.includes('The play() request was interrupted by a call to pause()') ||
        message.includes('The play() request was interrupted') ||
        message.includes('play() failed') ||
        message.includes('NotAllowedError')
      ) {
        console.log('忽略音频播放错误:', message);
        event.preventDefault();
        return;
      }

      // 其他未处理的错误也记录下来
      console.error('Unhandled promise rejection:', event.reason);
    };

    window.addEventListener('unhandledrejection', handleUnhandledRejection);
    return () => {
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
    };
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <AppProvider>
        <StockLoadingProvider>
          <Router>
            <div className="app">
              {/* 顶部导航栏 */}
              <HeadBarWrapper />
              
              {/* 主内容区 - 全宽 */}
              <main className="main-content-full">
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/predictions" element={<Predictions />} />
                  <Route path="/reports" element={<Reports />} />
                  <Route path="/us-market" element={<USMarket />} />
                  <Route path="/stock/:stockCode" element={<StockDetail />} />
                  <Route path="/feishu" element={<Feishu />} />
                </Routes>
              </main>
            </div>
          </Router>
        </StockLoadingProvider>
      </AppProvider>
    </QueryClientProvider>
  );
}

// HeadBar包装器 - 获取全局状态
function HeadBarWrapper() {
  return <HeadBar />;
}

export default App;
