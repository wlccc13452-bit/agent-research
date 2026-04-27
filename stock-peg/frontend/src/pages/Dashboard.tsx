import { useQuery, useQueryClient } from '@tanstack/react-query';
import { dailyWatchlistApi, fundamentalApi, initialDataApi, klineFastApi, stocksApi } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import { DEFAULT_LAYOUT_CONFIG, useLayoutConfig } from '../hooks/useLayoutConfig';
import { useAppContext } from '../App';
import { useEffect, useState, useMemo, useRef, useCallback } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { stockLoadingLogger } from '../utils/stockLoadingLogger';
import { useStockLoading } from '../contexts/StockLoadingContext';
import { clientLogger } from '../services/clientLogger';

// 新组件
import StatusBar from '../components/StatusBar';
import LeftPanel from '../components/LeftPanel';
import MainGroup from '../components/MainGroup';
import RightPanel from '../components/RightPanel';
import ResizableDivider from '../components/ResizableDivider';
import EnhancedLoadingScreen from '../components/EnhancedLoadingScreen';

// TAB类型定义
type TabValue = 'financial' | 'industry' | 'bot';
type ChartType = 'kline' | 'intraday';
type InitialDataBase = {
  holdings: { sectors: any[]; last_updated: string | null };
  indices: any;
  quotes: any[];
  watchlistSummary: { dates: any[]; total_dates: number; total_stocks: number };
  sync_progress: number;
  sync_message: string;
  sync_error: string | null;
};
type InitialDataPending = InitialDataBase & { sync_status: 'pending' | 'syncing' };
type InitialDataReady = InitialDataBase & { sync_status: 'ready' };
type InitialDataState = InitialDataPending | InitialDataReady;

const normalizeStockCode = (code?: string) => {
  if (!code) return '';
  return code
    .replace(/^(sh|sz)/i, '')
    .replace(/\.(SH|SZ)$/i, '')
    .trim();
};

export default function Dashboard() {
  const MIN_PANEL_WIDTH = 10;
  const MAX_PANEL_WIDTH = 40;

  const queryClient = useQueryClient();
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  
  // 记录Dashboard初始化
  useEffect(() => {
    clientLogger.info('loading', '开始加载智能仪表盘页面', {
      url: window.location.href
    });
    console.log('📊 [客户端日志] 开始加载智能仪表盘页面');
    
    // 页面卸载时手动刷新日志
    return () => {
      clientLogger.manualFlush();
    };
  }, []);
  
  // WebSocket服务器推送 - 用于接收数据更新推送
  const { isConnected, quotes, subscribe } = useWebSocket();
  
  // 加载进度追踪
  const { startLoading, updateStage, completeLoading, loadingState, setError } = useStockLoading();
  
  // 自持股票加载详细进度
  const [holdingsLoadingDetail, setHoldingsLoadingDetail] = useState<{
    totalSectors: number;
    currentSector: number;
    totalStocks: number;
    currentStock: number;
    currentSectorName: string;
    currentStockName: string;
  }>({
    totalSectors: 0,
    currentSector: 0,
    totalStocks: 0,
    currentStock: 0,
    currentSectorName: '',
    currentStockName: ''
  });
  
  // 加载状态 - 立即进入仪表盘，不等待服务器
  const [isReady, setIsReady] = useState(true); // 立即显示仪表盘
  const [holdingsReady, setHoldingsReady] = useState(false); // 自持股票数据是否就绪

  const [selectedStockCode, setSelectedStockCode] = useState<string | null>(null);
  const [selectedIndexCode, setSelectedIndexCode] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabValue>('bot'); // 默认激活 Bot tab
  const [chartType, setChartType] = useState<ChartType>('kline');
  const [mobileTab, setMobileTab] = useState<'market' | 'chart' | 'analysis'>('chart');
  const [isResizing, setIsResizing] = useState(false);
  
  // 存储metadata信息用于显示详细的加载步骤
  const [loadingMetadata, setLoadingMetadata] = useState<{
    is_updating?: boolean;
    actual_count?: number;
    requested_count?: number;
    last_update?: string;
  }>({});
  
  // 日志跟踪会话ID
  const currentSessionIdRef = useRef<string | null>(null);
  const selectedStockCodeRef = useRef<string | null>(null);
  const marketPushInvalidateRef = useRef(0);

  useEffect(() => {
    selectedStockCodeRef.current = selectedStockCode;
  }, [selectedStockCode]);
  
  // 全局状态 - 设置选中的板块
  const { setSelectedStockSector } = useAppContext();
  
  // 当选择指数时，清空股票选择
  const handleSelectIndex = (code: string) => {
    setSelectedIndexCode(code);
    setSelectedStockCode(null);
  };
  
  // 当选择股票时，清空指数选择
  const handleSelectStock = (code: string) => {
    // 强制校验代码有效性
    if (!code || code.startsWith('UNKNOWN')) {
      console.warn(`[Dashboard] 拒绝选择无效股票代码: ${code}`);
      return;
    }
    
    // 结束上一个会话
    if (currentSessionIdRef.current) {
      stockLoadingLogger.endSession(currentSessionIdRef.current);
    }
    
    // 开始新的会话
    const sessionId = stockLoadingLogger.startSession(code, 'stock_click');
    currentSessionIdRef.current = sessionId;
    
    stockLoadingLogger.logEvent(sessionId, 'frontend_stock_selected', 'frontend', {
      stockCode: code
    });
    
    setSelectedStockCode(code);
    setSelectedIndexCode(null);
  };
  
  // 布局配置
  const { config: layoutConfig, saveConfig } = useLayoutConfig();
  
  // 用于防止重复警告的标志
  const resizeWarningShownRef = useRef({ left: false, right: false });
  
  // 验证并修复布局配置
  useEffect(() => {
    const total = layoutConfig.leftPanelWidth + layoutConfig.rightPanelWidth;
    const centerWidth = 100 - total;
    
    if (centerWidth < layoutConfig.centerPanelMinWidth || total > 95) {
      console.warn('检测到无效布局配置，重置为默认值');
      saveConfig({
        leftPanelWidth: DEFAULT_LAYOUT_CONFIG.leftPanelWidth,
        rightPanelWidth: DEFAULT_LAYOUT_CONFIG.rightPanelWidth
      });
    }
    
    // 重置警告标志
    resizeWarningShownRef.current = { left: false, right: false };
  }, []); // 仅在组件挂载时检查一次
  
  // 输出当前布局宽度比例
  useEffect(() => {
    const centerWidth = 100 - layoutConfig.leftPanelWidth - layoutConfig.rightPanelWidth;
    console.log('📊 布局宽度比例:');
    console.log(`  左侧面板 (LeftPanel): ${layoutConfig.leftPanelWidth}%`);
    console.log(`  中间面板 (MainGroup): ${centerWidth.toFixed(1)}%`);
    console.log(`  右侧面板 (RightPanel): ${layoutConfig.rightPanelWidth}%`);
    console.log(`  总计: ${layoutConfig.leftPanelWidth + centerWidth + layoutConfig.rightPanelWidth}%`);
  }, [layoutConfig.leftPanelWidth, layoutConfig.rightPanelWidth]);
  
  // 监听持仓更新事件
  useEffect(() => {
    const handleWebSocketUpdate = (event: Event) => {
      const customEvent = event as CustomEvent;
      const message = customEvent.detail;
      if (!message || !message.type) return;
      const invalidateMarketRelatedData = () => {
        const now = Date.now();
        if (now - marketPushInvalidateRef.current < 15000) return;
        marketPushInvalidateRef.current = now;
        queryClient.invalidateQueries({ queryKey: ['market-sentiment'] });
        queryClient.invalidateQueries({ queryKey: ['industry-sectors'] });
        queryClient.invalidateQueries({ queryKey: ['concept-sectors'] });
        queryClient.invalidateQueries({ queryKey: ['north-money-flow'] });
        queryClient.invalidateQueries({ queryKey: ['north-money-top10'] });
        queryClient.invalidateQueries({ queryKey: ['sector-fund-flow'] });
      };

      switch (message.type) {
        case 'startup_progress': {
          // 后台预加载进度 - 仅用于日志，不影响前端显示
          const progress = message.progress || {};
          console.log('📡 [后台任务] 预加载进度:', progress.stage, progress.current, '/', progress.total);
          break;
        }
        case 'kline_updated': {
          const stockCode = message.stock_code || message.symbol;
          if (stockCode && !stockCode.startsWith('UNKNOWN')) {
            console.log('📡 Dashboard 收到 K 线数据更新推送:', stockCode);
            const pushedKline = Array.isArray(message.data?.kline) ? message.data.kline : [];
            if (pushedKline.length > 0) {
              // 更新快速加载缓存
              queryClient.setQueryData(['kline-quick', stockCode], (prev: any) => ({
                ...(prev || {}),
                data: pushedKline,
                local_data_available: true,
                is_updating: false,
                update_reason: null,
                last_update: message.timestamp || prev?.last_update || null,
                actual_count: pushedKline.length
              }));
            } else {
              // 如果没有数据，失效相关查询
              queryClient.invalidateQueries({ queryKey: ['kline-quick', stockCode] });
              queryClient.invalidateQueries({ queryKey: ['kline-full', stockCode] });
            }
            
            // 失效其他相关查询
            queryClient.invalidateQueries({ queryKey: ['kline', stockCode] });
            queryClient.invalidateQueries({ queryKey: ['kline', 'index', stockCode] });
            queryClient.invalidateQueries({ queryKey: ['pmr', stockCode] });
          }
          break;
        }
        case 'financial_updated':
        case 'financial-updated': {
          const fStockCode = message.stock_code;
          if (fStockCode && !fStockCode.startsWith('UNKNOWN')) {
            console.log('📡 Dashboard 收到财务数据更新推送:', fStockCode);
            queryClient.invalidateQueries({ queryKey: ['fundamental', fStockCode] });
            queryClient.invalidateQueries({ queryKey: ['valuation', fStockCode] });
            queryClient.invalidateQueries({ queryKey: ['annual-report', fStockCode] });
            queryClient.invalidateQueries({ queryKey: ['quarterly-data', fStockCode] });
          }
          break;
        }
        case 'quote_updated':
        case 'quote': {
          const qStockCode = String(message.stock_code || message.data?.code || message.quote?.code || '');
          if (!qStockCode) return;
          
          const normalizedCode = qStockCode
            .replace(/^(sh|sz)/i, '')
            .replace(/\.(SH|SZ)$/i, '');
          
          // 如果是正在查看的股票行情，更新它
          const activeStockCode = selectedStockCodeRef.current;
          if (activeStockCode && (activeStockCode.includes(normalizedCode) || normalizedCode.includes(activeStockCode))) {
            const quoteData = message.data || message.quote;
            if (quoteData) {
              queryClient.setQueryData(['quote', activeStockCode], (oldData: any) => {
                if (!oldData) return quoteData;
                return { ...oldData, ...quoteData };
              });
            }
          }

          // 指数行情更新
          if (['000001', '399001', '399006'].includes(normalizedCode)) {
            queryClient.invalidateQueries({ queryKey: ['cn-indices'] });
            queryClient.invalidateQueries({ queryKey: ['initial-data'] });
          }
          invalidateMarketRelatedData();
          break;
        }
        case 'market_sentiment_updated':
        case 'market_data_updated':
        case 'sector_updated':
          invalidateMarketRelatedData();
          break;
        case 'us_index_updated':
          queryClient.invalidateQueries({ queryKey: ['initial-data'] });
          queryClient.invalidateQueries({ queryKey: ['us-indices'] });
          invalidateMarketRelatedData();
          break;
        case 'holdings_updated':
          queryClient.invalidateQueries({ queryKey: ['initial-data'] });
          break;
        case 'watchlist_updated':
          queryClient.invalidateQueries({ queryKey: ['daily-watchlist'] });
          queryClient.invalidateQueries({ queryKey: ['dashboard-watchlist-summary'] });
          queryClient.invalidateQueries({ queryKey: ['initial-data'] });
          break;
        case 'background_update_progress':
          // 后台更新进度 - 仅用于日志
          console.log('📡 [后台任务] 更新进度:', message.progress);
          break;
        case 'initial_sync_error':
          // 初始同步错误 - 仅记录日志，不影响前端显示
          console.error('📡 [后台任务] 初始同步错误:', message.message);
          break;
        case 'pmr_precompute_start':
        case 'pmr_precompute_progress':
        case 'pmr_precompute_complete':
          // PMR 预计算通知
          console.log(`📡 PMR 预计算 ${message.type}:`, message.message);
          if (message.type === 'pmr_precompute_complete' && message.stock_code) {
            queryClient.invalidateQueries({ queryKey: ['pmr', message.stock_code] });
          }
          break;
      }
    };
    
    window.addEventListener('websocket-message', handleWebSocketUpdate);
    return () => {
      window.removeEventListener('websocket-message', handleWebSocketUpdate);
    };
  }, [queryClient]);

  const { data: initialData, isLoading: loadingInitialData, isError: isInitialDataError, error: initialDataError } = useQuery<InitialDataState>({
    queryKey: ['initial-data', isConnected ? 'ws-online' : 'ws-offline'],
    queryFn: async () => {
      try {
        console.log('📡 Dashboard 正在获取初始数据...');
        const timeoutMs = isConnected ? 30000 : 20000;
        const payload = await initialDataApi.getInitialData(timeoutMs);
        const holdings = payload.holdings || { sectors: [], last_updated: null };
        const baseData: InitialDataBase = {
          holdings,
          indices: [],
          quotes: [],
          watchlistSummary: { dates: [], total_dates: 0, total_stocks: 0 },
          sync_progress: Number(payload.sync_progress || 0),
          sync_message: payload.sync_message || '',
          sync_error: payload.sync_error || null
        };
        if (payload.sync_status === 'ready') {
          return { ...baseData, sync_status: 'ready' };
        }
        return { ...baseData, sync_status: payload.sync_status === 'syncing' ? 'syncing' : 'pending' };
      } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        return {
          holdings: { sectors: [], last_updated: null },
          indices: [],
          quotes: [],
          watchlistSummary: { dates: [], total_dates: 0, total_stocks: 0 },
          sync_progress: 0,
          sync_message: isConnected ? '初始化数据拉取失败，等待重试' : '等待 WebSocket 与服务连接',
          sync_error: message.includes('超时') ? null : message,
          sync_status: 'pending'
        };
      }
    },
    staleTime: 2000,
    refetchInterval: (query) => {
      const data = query.state.data as InitialDataState | undefined;
      if (!data) {
        return 2000;
      }
      const sectorsCount = data.holdings?.sectors?.length || 0;
      if (sectorsCount === 0) {
        return 2000;
      }
      return false;
    },
  });

  const hasInitialSectors = (initialData?.holdings?.sectors?.length || 0) > 0;

  const { data: watchlistSummaryData } = useQuery({
    queryKey: ['dashboard-watchlist-summary'],
    queryFn: () => dailyWatchlistApi.getSummary(false, 10),
    enabled: hasInitialSectors,
    retry: 2,
    staleTime: 10000,
    refetchInterval: 30000,
  });
  
  useEffect(() => {
    // 立即请求行情数据
    if (!hasInitialSectors || !initialData?.holdings) return;

    const fetchQuotes = async () => {
      const holdings = initialData.holdings;
      const holdingCodes = holdings?.sectors
        ? holdings.sectors.flatMap((s: any) => (s.stocks || []).map((st: any) => st.code))
        : [];
      const allCodes = Array.from(new Set(holdingCodes.filter((code: string) => code && !code.startsWith('UNKNOWN'))));

      if (allCodes.length > 0) {
        try {
          const quotes = (await stocksApi.getQuotes(allCodes)) as any[];
          queryClient.setQueriesData({ queryKey: ['initial-data'] }, (old: any) => ({
            ...old,
            quotes
          }));
        } catch (err) {
          // 静默处理超时，后续轮询会重试
          const errMsg = err instanceof Error ? err.message : String(err);
          if (!errMsg.includes('超时')) {
            console.error('📡 Dashboard 获取行情数据失败:', err);
          }
        }
      }
    };

    fetchQuotes();
  }, [hasInitialSectors, initialData?.holdings, queryClient]);

  useEffect(() => {
    if (hasInitialSectors && !holdingsReady) {
      setHoldingsReady(true);
    }
    if (!loadingInitialData && !holdingsReady && initialData?.sync_status === 'ready') {
      setHoldingsReady(true);
    }
  }, [hasInitialSectors, loadingInitialData, holdingsReady, initialData?.sync_status]);

  useEffect(() => {
    // 立即请求动态关注数据
    if (!hasInitialSectors) return;
    const timer = setTimeout(async () => {
      try {
        const watchlistSummary = await dailyWatchlistApi.getSummary(false, 10);
        queryClient.setQueriesData({ queryKey: ['initial-data'] }, (old: any) => ({
          ...old,
          watchlistSummary
        }));
      } catch (error) {
        // 静默处理超时，后续轮询会重试
        const errMsg = error instanceof Error ? error.message : String(error);
        if (!errMsg.includes('超时')) {
          console.error('📡 Dashboard 获取动态关注失败:', error);
        }
      }
    }, 2500);
    return () => clearTimeout(timer);
  }, [hasInitialSectors, queryClient]);

  useEffect(() => {
    // 立即请求指数行情
    if (!hasInitialSectors) return;
    const timer = setTimeout(async () => {
      try {
        const indices = await stocksApi.getIndicesQuotes();
        queryClient.setQueriesData({ queryKey: ['initial-data'] }, (old: any) => ({
          ...old,
          indices
        }));
      } catch (error) {
        // 静默处理超时
        const errMsg = error instanceof Error ? error.message : String(error);
        if (!errMsg.includes('超时')) {
          console.error('📡 Dashboard 获取指数行情失败:', error);
        }
      }
    }, 1200);
    return () => clearTimeout(timer);
  }, [hasInitialSectors, queryClient]);

  useEffect(() => {
    if (!isInitialDataError) return;
    const message = initialDataError instanceof Error ? initialDataError.message : String(initialDataError);
    console.error('📡 Dashboard 初始数据加载异常:', message);
  }, [isInitialDataError, initialDataError]);

  useEffect(() => {
    if (hasInitialSectors && initialData?.holdings?.sectors?.[0]?.stocks?.[0]?.code && !selectedStockCode) {
      const firstCode = initialData.holdings.sectors[0].stocks[0].code;
      queryClient.prefetchQuery({
        queryKey: ['kline-quick', firstCode],
        queryFn: async () => {
          const result = await klineFastApi.getKlineFast(firstCode, 'day', 100, undefined, true, true, 10000);
          return result;
        }
      });
    }
  }, [hasInitialSectors, initialData, selectedStockCode, queryClient]);

  const holdings = initialData?.holdings;
  const initialQuotes = initialData?.quotes;
  const indicesData = initialData?.indices;
  const loadingHoldings = loadingInitialData;
  const loadingQuotes = loadingInitialData;

  useEffect(() => {
    if (!isConnected) return;
    const holdingCodes = holdings?.sectors
      ? holdings.sectors.flatMap((s: any) => (s.stocks || []).map((st: any) => st.code))
      : [];
    const watchlistSummary = watchlistSummaryData || initialData?.watchlistSummary;
    const watchlistCodes = watchlistSummary?.dates
      ? watchlistSummary.dates.flatMap((dateGroup: any) =>
          (dateGroup.stocks || []).map((stock: any) => stock.stock_code)
        )
      : [];
    const codes = Array.from(
      new Set(
        [...holdingCodes, ...watchlistCodes]
          .filter((code: string) => code && !code.startsWith('UNKNOWN'))
          .map((code: string) => normalizeStockCode(code))
          .filter(Boolean)
      )
    );
    if (codes.length > 0) {
      subscribe(codes);
    }
  }, [isConnected, holdings, watchlistSummaryData, initialData?.watchlistSummary, subscribe]);

  const holdingStocks = useMemo(() => {
    if (!holdings?.sectors) return [];
    return holdings.sectors.flatMap((sector: any) =>
      (sector.stocks || []).map((stock: any) => ({
        code: stock.code,
        name: stock.name,
        sector: sector.name
      }))
    );
  }, [holdings]);

  const watchlistStocks = useMemo(() => {
    const summary = watchlistSummaryData || initialData?.watchlistSummary;
    if (!summary?.dates) return [];
    return summary.dates.flatMap((dateGroup: any) =>
      (dateGroup.stocks || [])
        .filter((stock: any) => stock.stock_code && !stock.stock_code.startsWith('UNKNOWN'))
        .map((stock: any) => ({
          code: stock.stock_code,
          name: stock.stock_name,
          sector: '动态关注'
        }))
    );
  }, [watchlistSummaryData, initialData]);

  // 合并行情
  const allStocks = useMemo(() => {
    try {
      const baseStocks = [...holdingStocks, ...watchlistStocks].filter((stock, index, arr) =>
        arr.findIndex((item) => item.code === stock.code) === index
      );

      if (!baseStocks.length) {
        return [];
      }

      const mergedQuotes = new Map<string, any>();
      (Array.isArray(initialQuotes) ? initialQuotes : []).forEach((item: any) => {
        if (item?.code) {
          mergedQuotes.set(item.code, item);
          const normalizedCode = normalizeStockCode(item.code);
          if (normalizedCode) {
            mergedQuotes.set(normalizedCode, { ...item, code: normalizedCode });
          }
        }
      });
      quotes.forEach((item, code) => {
        if (!code && !item?.code) return;
        const normalizedKey = normalizeStockCode(code || item?.code);
        if (code) {
          mergedQuotes.set(code, item);
        }
        if (item?.code) {
          mergedQuotes.set(item.code, item);
        }
        if (normalizedKey) {
          mergedQuotes.set(normalizedKey, { ...item, code: normalizedKey });
        }
      });

      return baseStocks.map((stock: any) => {
        const normalizedStockCode = normalizeStockCode(stock.code);
        const quote = mergedQuotes.get(stock.code) || mergedQuotes.get(normalizedStockCode);
        return quote ? { ...stock, ...quote } : stock;
      });
    } catch (error) {
      console.error('Error in allStocks memo:', error);
      return [];
    }
  }, [holdingStocks, watchlistStocks, initialQuotes, quotes]);

  // 设置初始选中的股票
  useEffect(() => {
    if (allStocks.length > 0 && !selectedStockCode) {
      const firstStock = allStocks[0];
      if (firstStock && firstStock.code) {
        setSelectedStockCode(firstStock.code);
      }
    }
  }, [allStocks, selectedStockCode]);

  useEffect(() => {
    if (!selectedStockCode) return;

    queryClient.prefetchQuery({
      queryKey: ['fundamental', selectedStockCode],
      queryFn: () => fundamentalApi.analyze(selectedStockCode),
      staleTime: 60000,
    }).catch(() => undefined);
    queryClient.prefetchQuery({
      queryKey: ['valuation', selectedStockCode],
      queryFn: () => fundamentalApi.getValuation(selectedStockCode),
      staleTime: 60000,
    }).catch(() => undefined);
    queryClient.prefetchQuery({
      queryKey: ['annual-report', selectedStockCode],
      queryFn: () => fundamentalApi.getAnnualReport(selectedStockCode),
      staleTime: 120000,
    }).catch(() => undefined);
    queryClient.prefetchQuery({
      queryKey: ['quarterly-data', selectedStockCode],
      queryFn: () => fundamentalApi.getQuarterlyData(selectedStockCode, 3),
      staleTime: 120000,
    }).catch(() => undefined);
  }, [selectedStockCode, queryClient]);

  useEffect(() => {
    if (!selectedStockCode || allStocks.length < 2) return;

    const currentIndex = allStocks.findIndex((stock: any) => stock.code === selectedStockCode);
    if (currentIndex < 0) return;

    const nearbyCodes = [
      allStocks[currentIndex - 1]?.code,
      allStocks[currentIndex + 1]?.code,
    ].filter((code): code is string => !!code && code !== selectedStockCode);

    nearbyCodes.forEach((code) => {
      queryClient.prefetchQuery({
        queryKey: ['kline-quick', code],
        queryFn: async () => {
          try {
            return await klineFastApi.getKlineFast(code, 'day', 100, undefined, true, true, 12000);
          } catch {
            return {
              data: [],
              local_data_available: false,
              is_updating: false,
              task_id: null,
              last_update: null,
              last_data_date: null,
              update_reason: null,
              session_id: '',
              quick_load: true,
              actual_count: 0,
            };
          }
        },
        staleTime: 30000,
      }).catch(() => undefined);
    });
  }, [selectedStockCode, allStocks, queryClient]);

  // 键盘导航支持
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!allStocks || allStocks.length === 0) return;
      
      const currentIndex = allStocks.findIndex((s: any) => s.code === selectedStockCode);
      
      if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
        e.preventDefault();
        const prevIndex = currentIndex > 0 ? currentIndex - 1 : allStocks.length - 1;
        setSelectedStockCode(allStocks[prevIndex].code);
      } else if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
        e.preventDefault();
        const nextIndex = currentIndex < allStocks.length - 1 ? currentIndex + 1 : 0;
        setSelectedStockCode(allStocks[nextIndex].code);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [allStocks, selectedStockCode]);

  // 第一步：快速加载K线数据（最近60条）
  const { data: quickKlineData, isLoading: loadingQuickKline, isFetched: isQuickKlineFetched, isError: isQuickKlineError, error: quickKlineError } = useQuery({
    queryKey: ['kline-quick', selectedStockCode],
    queryFn: async () => {
      const sessionId = currentSessionIdRef.current;
      
      if (sessionId) {
        stockLoadingLogger.logEvent(sessionId, 'frontend_kline_quick_request_start', 'frontend', {
          stockCode: selectedStockCode
        });
      }
      
      const requestStart = Date.now();
      let result;
      try {
        result = await klineFastApi.getKlineFast(
          selectedStockCode!, 
          'day', 
          100,  // 优化：直接加载100条，减少一次请求
          sessionId || undefined,
          true,  // quickLoad = true
          true,
          15000
        );
      } catch {
        result = {
          data: [],
          local_data_available: false,
          is_updating: false,
          task_id: null,
          last_update: null,
          last_data_date: null,
          update_reason: null,
          session_id: sessionId || '',
          quick_load: true,
          actual_count: 0,
        };
      }
      const requestDuration = Date.now() - requestStart;
      
      // 更新metadata用于显示加载步骤详情
      setLoadingMetadata({
        is_updating: result.is_updating,
        actual_count: result.actual_count,
        requested_count: 100,
        last_update: result.last_update || undefined
      });
      
      if (sessionId) {
        stockLoadingLogger.logEvent(
          sessionId,
          'frontend_kline_quick_request_complete',
          'frontend',
          {
            dataCount: result.data?.length || 0,
            isUpdating: result.is_updating,
            quick_load: result.quick_load
          },
          requestDuration
        );
        
        // 如果是后台更新，记录状态
        if (result.is_updating) {
          stockLoadingLogger.logEvent(sessionId, 'frontend_background_update_started', 'frontend', {
            taskId: result.task_id,
            reason: result.update_reason
          });
        }
        
        // 结束会话
        stockLoadingLogger.endSession(sessionId, true);
        currentSessionIdRef.current = null;
      }
      
      return result; // 返回完整数据（包含data和metadata）
    },
    enabled: !!selectedStockCode && chartType === 'kline' && hasInitialSectors,
    retry: 0,
    staleTime: 30000, // 30秒内不重新请求
    placeholderData: (previousData) => previousData,
  });

  // 优先使用快速数据
  const klineData = Array.isArray(quickKlineData)
    ? quickKlineData
    : (quickKlineData?.data || []);
  const loadingKline = loadingQuickKline && klineData.length === 0;
  
  // 当股票代码改变时，开始加载追踪
  useEffect(() => {
    if (selectedStockCode && chartType === 'kline') {
      startLoading(selectedStockCode);
      updateStage('loading-kline-quick');
      setLoadingMetadata({});
    }
  }, [selectedStockCode, chartType, startLoading, updateStage]);

  useEffect(() => {
    if (
      chartType !== 'kline' ||
      loadingState.stockCode !== selectedStockCode ||
      loadingState.stage !== 'loading-kline-quick'
    ) {
      return;
    }

    const timer = setTimeout(() => {
      completeLoading();
    }, 3500);

    return () => clearTimeout(timer);
  }, [chartType, loadingState.stockCode, loadingState.stage, selectedStockCode, completeLoading]);
  
  // 追踪快速K线加载
  useEffect(() => {
    if (
      chartType === 'kline' &&
      isQuickKlineFetched &&
      loadingState.stockCode === selectedStockCode &&
      loadingState.stage !== 'complete'
    ) {
      updateStage('complete');
      setTimeout(() => completeLoading(), 500);
    }
  }, [chartType, isQuickKlineFetched, loadingState.stage, loadingState.stockCode, selectedStockCode, updateStage, completeLoading]);

  useEffect(() => {
    if (
      chartType === 'kline' &&
      isQuickKlineError &&
      loadingState.stockCode === selectedStockCode &&
      loadingState.stage !== 'complete'
    ) {
      const message = quickKlineError instanceof Error ? quickKlineError.message : '加载K线数据失败';
      setError(message);
      completeLoading();
    }
  }, [
    chartType,
    isQuickKlineError,
    quickKlineError,
    loadingState.stockCode,
    loadingState.stage,
    selectedStockCode,
    setError,
    completeLoading,
  ]);
  
  // 调试日志
  useEffect(() => {
    if (initialData) {
      console.log('📊 [DEBUG] initialData 已就绪:', {
        hasHoldings: !!initialData.holdings,
        sectorsCount: initialData.holdings?.sectors?.length || 0,
        stocksCount: initialData.holdings?.sectors?.reduce((acc: number, s: any) => acc + (s.stocks?.length || 0), 0) || 0,
        indicesCount: initialData.indices?.length || 0,
        quotesCount: initialData.quotes?.length || 0
      });
    }
  }, [initialData]);

  // 调试日志
  console.log('📊 K线数据加载状态:', {
    loadCount: quickKlineData?.data?.length || 0,
    finalCount: klineData?.length || 0,
    isLoading: loadingKline,
    metadata: loadingMetadata
  });

  // 获取选中指数的K线数据
  const { data: indexKlineData, isLoading: loadingIndexKline } = useQuery({
    queryKey: ['kline', 'index', selectedIndexCode],
    queryFn: async () => {
      const result = await klineFastApi.getKlineFast(selectedIndexCode!, 'day', 100, undefined, false, true, 2500);
      return result.data;
    },
    enabled: !!selectedIndexCode && chartType === 'kline' && hasInitialSectors,
  });

  // 获取选中股票的分时数据
  const { data: intradayData, isLoading: loadingIntraday } = useQuery({
    queryKey: ['intraday', selectedStockCode],
    queryFn: () => stocksApi.getIntraday(selectedStockCode!),
    enabled: !!selectedStockCode && chartType === 'intraday',
    refetchInterval: chartType === 'intraday' ? 30000 : false,
  });
  
  // 获取选中指数的分时数据
  const { data: indexIntradayData, isLoading: loadingIndexIntraday } = useQuery({
    queryKey: ['intraday', 'index', selectedIndexCode],
    queryFn: () => stocksApi.getIntraday(selectedIndexCode!),
    enabled: !!selectedIndexCode && chartType === 'intraday',
    refetchInterval: chartType === 'intraday' ? 30000 : false,
  });
  
  // 合并数据
  const finalKlineData = selectedIndexCode ? indexKlineData : klineData;
  const finalLoadingKline = selectedIndexCode ? loadingIndexKline : loadingKline;
  const finalIntradayData = selectedIndexCode ? indexIntradayData : intradayData;
  const finalLoadingIntraday = selectedIndexCode ? loadingIndexIntraday : loadingIntraday;

  // 获取选中股票信息
  const selectedStock = allStocks.find((s: any) => s.code === selectedStockCode);
  
  // 获取指数信息（用于显示） - 已合并到 initialData
  // const { data: indicesData } = useQuery({
  //   queryKey: ['indices-quotes'],
  //   queryFn: stocksApi.getIndicesQuotes,
  // });
  
  const selectedIndex = indicesData?.indices?.find((idx: any) => {
    if (!selectedIndexCode) return false;
    return idx.code === selectedIndexCode || idx.full_code === selectedIndexCode;
  });
  
  // 当前选中的项目（股票或指数）
  const selectedItem = useMemo(() => {
    return selectedIndexCode ? {
      code: selectedIndexCode,
      name: selectedIndex?.name || selectedIndexCode,
      change_pct: selectedIndex?.change_pct,
      price: selectedIndex?.price
    } : selectedStock;
  }, [selectedIndexCode, selectedIndex, selectedStock]);
  
  // 获取选中股票的板块
  const selectedStockSector = useMemo(() => {
    if (!selectedStockCode || !holdings?.sectors) return undefined;
    for (const sector of holdings.sectors) {
      const found = sector.stocks.find((s: any) => s.code === selectedStockCode);
      if (found) return sector.name;
    }
    return undefined;
  }, [selectedStockCode, holdings]);

  const leftPanelResizeMax = Math.max(
    MIN_PANEL_WIDTH,
    Math.min(
      MAX_PANEL_WIDTH,
      100 - layoutConfig.centerPanelMinWidth - layoutConfig.rightPanelWidth
    )
  );

  const rightPanelResizeMax = Math.max(
    MIN_PANEL_WIDTH,
    Math.min(
      MAX_PANEL_WIDTH,
      100 - layoutConfig.centerPanelMinWidth - layoutConfig.leftPanelWidth
    )
  );

  // 当选中股票的板块变化时,更新全局状态
  useEffect(() => {
    setSelectedStockSector(selectedStockSector);
  }, [selectedStockSector, setSelectedStockSector]);

  // 调整左侧面板宽度
  const handleLeftPanelResize = useCallback((newWidth: number, persist: boolean = false) => {
    if (newWidth < MIN_PANEL_WIDTH || newWidth > leftPanelResizeMax) return;
    
    // 验证中间面板最小宽度
    const centerWidth = 100 - newWidth - layoutConfig.rightPanelWidth;
    if (centerWidth < layoutConfig.centerPanelMinWidth) {
      // 只在首次触发时显示警告
      if (!resizeWarningShownRef.current.left) {
        console.warn(`左侧面板过宽，中间面板仅剩${centerWidth.toFixed(1)}%`);
        resizeWarningShownRef.current.left = true;
      }
      return;
    }
    
    // 重置警告标志
    resizeWarningShownRef.current.left = false;
    saveConfig({ leftPanelWidth: newWidth }, persist);
  }, [layoutConfig.rightPanelWidth, layoutConfig.centerPanelMinWidth, leftPanelResizeMax, saveConfig]);

  // 处理右侧面板调整
  const handleRightPanelResize = useCallback((newWidth: number, persist: boolean = false) => {
    if (newWidth < MIN_PANEL_WIDTH || newWidth > rightPanelResizeMax) return;
    
    const centerWidth = 100 - layoutConfig.leftPanelWidth - newWidth;
    if (centerWidth < layoutConfig.centerPanelMinWidth) {
      if (!resizeWarningShownRef.current.right) {
        console.warn(`右侧面板过宽，中间面板仅剩${centerWidth.toFixed(1)}%`);
        resizeWarningShownRef.current.right = true;
      }
      return;
    }
    
    resizeWarningShownRef.current.right = false;
    saveConfig({ rightPanelWidth: newWidth }, persist);
  }, [layoutConfig.leftPanelWidth, layoutConfig.centerPanelMinWidth, rightPanelResizeMax, saveConfig]);

  // 检测移动端
  const [isMobile, setIsMobile] = useState(false);
  
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 1024);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // 渲染逻辑
  if (!isReady) {
    return (
      <EnhancedLoadingScreen 
        onComplete={() => setIsReady(true)} 
        loadingStates={{
          websocket: !isConnected,
          holdings: loadingHoldings,
          quotes: loadingQuotes,
          config: false, // 布局配置在 useLayoutConfig 中同步加载
          analysis: loadingQuickKline,
          holdingsDetail: holdingsLoadingDetail
        }}
      />
    );
  }

  return (
    <div className={`flex-1 flex flex-col overflow-hidden ${
      isDark 
        ? 'bg-gradient-to-br from-[#0a0a0a] via-[#0f0f0f] to-[#0a0a0a]' 
        : 'bg-gradient-to-br from-gray-50 via-white to-gray-50'
    }`}>
      {/* MAINBODY - 主体区域 */}
      <div data-resize-container className={`flex-1 min-h-0 min-w-0 flex flex-col lg:flex-row gap-1 p-1 ${isResizing ? 'cursor-col-resize select-none' : ''}`}>
        {/* 移动端导航栏 - 仅在手机端显示 */}
        {isMobile && (
          <div className={`flex-shrink-0 flex border-b mb-1 ${isDark ? 'border-[#2a2a2a] bg-[#1a1a1a]' : 'border-gray-200 bg-white'}`}>
            <button 
              onClick={() => setMobileTab('market')}
              className={`flex-1 py-2 text-xs font-bold ${mobileTab === 'market' ? 'text-blue-500 border-b-2 border-blue-500' : 'text-gray-500'}`}
            >
              行情
            </button>
            <button 
              onClick={() => setMobileTab('chart')}
              className={`flex-1 py-2 text-xs font-bold ${mobileTab === 'chart' ? 'text-blue-500 border-b-2 border-blue-500' : 'text-gray-500'}`}
            >
              图表
            </button>
            <button 
              onClick={() => setMobileTab('analysis')}
              className={`flex-1 py-2 text-xs font-bold ${mobileTab === 'analysis' ? 'text-blue-500 border-b-2 border-blue-500' : 'text-gray-500'}`}
            >
              分析
            </button>
          </div>
        )}

        {/* 左侧：自持股票面板 */}
        {(!isMobile || mobileTab === 'market') && (
          <div className={`lg:flex-shrink-0 flex flex-col ${isResizing ? 'pointer-events-none' : ''}`} 
               style={{ 
                 width: isMobile ? '100%' : `${layoutConfig.leftPanelWidth}%`, 
                 flexBasis: isMobile ? '100%' : `${layoutConfig.leftPanelWidth}%`,
                 height: isMobile ? 'calc(100vh - 120px)' : '100%',
                 minHeight: isMobile ? '0' : '400px'
               }}>
            <LeftPanel 
              allStocks={allStocks}
              holdings={holdings}
              selectedStockCode={selectedStockCode || undefined}
              onSelectStock={handleSelectStock}
              selectedIndexCode={selectedIndexCode || undefined}
              onSelectIndex={handleSelectIndex}
              isResizing={isResizing}
            />
          </div>
        )}

        {/* 左侧分割线 - 仅在桌面端显示 */}
        <ResizableDivider 
          onResize={(val) => handleLeftPanelResize(val, false)}
          onResizeStart={() => setIsResizing(true)}
          onResizeEnd={() => {
            setIsResizing(false);
            handleLeftPanelResize(layoutConfig.leftPanelWidth, true);
          }}
          direction="left"
          currentSize={layoutConfig.leftPanelWidth}
          minSize={MIN_PANEL_WIDTH}
          maxSize={leftPanelResizeMax}
          className="hidden lg:block z-20"
        />

        {/* 中间：K线图核心区域 */}
        {(!isMobile || mobileTab === 'chart') && (
          <div className={`flex-1 min-h-0 min-w-0 lg:min-h-0 flex flex-col ${isResizing ? 'pointer-events-none' : ''}`} 
               style={{ minHeight: isMobile ? '0' : '500px', height: isMobile ? 'calc(100vh - 120px)' : '100%' }}>
            <MainGroup
              selectedStock={selectedItem}
              selectedStockCode={selectedStockCode || selectedIndexCode}
              selectedStockSector={selectedStockSector}
              chartType={chartType}
              onChartTypeChange={setChartType}
              klineData={finalKlineData}
              loadingKline={finalLoadingKline}
              intradayData={finalIntradayData}
              loadingIntraday={finalLoadingIntraday}
              isResizing={isResizing}
            />
          </div>
        )}

        {/* 右侧分割线 - 仅在桌面端显示 */}
        <ResizableDivider 
          onResize={(val) => handleRightPanelResize(val, false)}
          onResizeStart={() => setIsResizing(true)}
          onResizeEnd={() => {
            setIsResizing(false);
            handleRightPanelResize(layoutConfig.rightPanelWidth, true);
          }}
          direction="right"
          currentSize={layoutConfig.rightPanelWidth}
          minSize={MIN_PANEL_WIDTH}
          maxSize={rightPanelResizeMax}
          className="hidden lg:block z-20"
        />

        {/* 右侧：TAB面板 */}
        {(!isMobile || mobileTab === 'analysis') && (
          <div className={`lg:flex-shrink-0 flex flex-col ${isResizing ? 'pointer-events-none' : ''}`} 
               style={{ 
                 width: isMobile ? '100%' : `${layoutConfig.rightPanelWidth}%`, 
                 flexBasis: isMobile ? '100%' : `${layoutConfig.rightPanelWidth}%`,
                 height: isMobile ? 'calc(100vh - 120px)' : '100%',
                 minHeight: isMobile ? '0' : '400px'
               }}>
            <RightPanel
              activeTab={activeTab}
              onTabChange={setActiveTab}
              selectedStockCode={selectedStockCode}
              selectedStockSector={selectedStockSector}
              isResizing={isResizing}
            />
          </div>
        )}
      </div>

      {/* STATUSBAR - 底部状态栏 */}
      <StatusBar />
    </div>
  );
}
