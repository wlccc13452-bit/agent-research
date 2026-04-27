import { useEffect, useMemo, useRef, useState } from 'react';
import { useMutation, useQueries, useQuery, useQueryClient } from '@tanstack/react-query';
import { Plus, Trash2, TrendingUp, TrendingDown, Minus, Loader2, Target, Eye, EyeOff, Archive, ArchiveRestore, Settings, Clock, Bell, RefreshCw, Save, AlertCircle } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import HoldingsPanel from './HoldingsPanel';
import IndicesPanel from './IndicesPanel';
import WatchlistPanelHeader from './WatchlistPanelHeader';
import { dailyWatchlistApi, stocksApi, settingsApi } from '../services/api';
import marketNewsThemeRaw from '../config/marketNewsTheme.json?raw';

interface LeftPanelStyleConfig {
  darkItemCardBg?: string;
}

const parsedLeftPanelStyleConfig = (() => {
  try {
    return JSON.parse(marketNewsThemeRaw) as LeftPanelStyleConfig;
  } catch {
    return {};
  }
})();

const LEFT_PANEL_DARK_ITEM_BG = parsedLeftPanelStyleConfig.darkItemCardBg ?? '#111827';

// 交易日配置接口
interface TradingHoursConfig {
  morning_session_start: string;
  morning_session_end: string;
  afternoon_session_start: string;
  afternoon_session_end: string;
  trading_days: string;
  trading_days_list: number[];
  price_alert_check_interval: number;
  enable_price_alert_monitoring: boolean;
  auto_stop_after_trigger: boolean;
  market_sentiment_update_interval: number;
}

const WEEKDAYS = [
  { value: 1, label: '周一' },
  { value: 2, label: '周二' },
  { value: 3, label: '周三' },
  { value: 4, label: '周四' },
  { value: 5, label: '周五' },
  { value: 6, label: '周六' },
  { value: 7, label: '周日' },
];

interface LeftPanelProps {
  allStocks: any[];
  holdings: any;
  selectedStockCode: string | undefined;
  onSelectStock: (code: string) => void;
  selectedIndexCode?: string;
  onSelectIndex: (code: string) => void;
  isResizing?: boolean;
}

export default function LeftPanel({ 
  allStocks, 
  holdings, 
  selectedStockCode, 
  onSelectStock,
  selectedIndexCode,
  onSelectIndex,
  isResizing = false
}: LeftPanelProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const queryClient = useQueryClient();
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [watchlistStockName, setWatchlistStockName] = useState('');
  const [watchlistStockCode, setWatchlistStockCode] = useState('');
  const [watchlistReason, setWatchlistReason] = useState('');
  const [watchlistDate, setWatchlistDate] = useState(new Date().toISOString().split('T')[0]);
  const [indicesCollapsed, setIndicesCollapsed] = useState(false);
  const [holdingsCollapsed, setHoldingsCollapsed] = useState(false);
  const [watchlistCollapsed, setWatchlistCollapsed] = useState(false);
  const [holdingsRatio, setHoldingsRatio] = useState(0.55);
  const [draggingSplitter, setDraggingSplitter] = useState(false);
  const stockPanelsRef = useRef<HTMLDivElement>(null);
  const [showWatchlistSecondLine, setShowWatchlistSecondLine] = useState(true);
  const [showArchived, setShowArchived] = useState(false);
  const [showWatchlistTargetDialog, setShowWatchlistTargetDialog] = useState(false);
  const [watchlistTargetForm, setWatchlistTargetForm] = useState({
    stockId: 0,
    stockCode: '',
    stockName: '',
    currentPrice: 0,
    targetPrice: '',
    changeUpPct: '',
    changeDownPct: '',
    notes: ''
  });

  // 设置对话框相关状态
  const [showSettingsDialog, setShowSettingsDialog] = useState(false);
  const [settingsFormData, setSettingsFormData] = useState<TradingHoursConfig | null>(null);
  const [hasSettingsChanges, setHasSettingsChanges] = useState(false);
  const [settingsSaveMessage, setSettingsSaveMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const { data: watchlistSummary, isLoading: watchlistLoading } = useQuery({
    queryKey: ['daily-watchlist', showArchived],
    queryFn: () => dailyWatchlistApi.getSummary(showArchived, 10),
  });

  const addWatchlistMutation = useMutation({
    mutationFn: () =>
      dailyWatchlistApi.addStock({
        stock_name: watchlistStockName.trim(),
        stock_code: watchlistStockCode.trim() || undefined,
        watch_date: watchlistDate,
        reason: watchlistReason.trim() || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['daily-watchlist'] });
      setShowAddDialog(false);
      setWatchlistStockName('');
      setWatchlistStockCode('');
      setWatchlistReason('');
    },
  });

  const deleteWatchlistMutation = useMutation({
    mutationFn: (stockId: number) => dailyWatchlistApi.deleteStocks({ stock_ids: [stockId] }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['daily-watchlist'] });
    },
  });

  const unarchiveMutation = useMutation({
    mutationFn: (stockIds: number[]) => dailyWatchlistApi.unarchiveStocks(stockIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['daily-watchlist'] });
    },
  });

  const updateWatchlistTargetMutation = useMutation({
    mutationFn: () => {
      // 如果目标价为空，使用当前股价
      const finalTargetPrice = watchlistTargetForm.targetPrice || watchlistTargetForm.currentPrice?.toString() || '';
      
      const data = {
        target_price: finalTargetPrice ? parseFloat(finalTargetPrice) : undefined,
        change_up_pct: watchlistTargetForm.changeUpPct ? parseFloat(watchlistTargetForm.changeUpPct) : undefined,
        change_down_pct: watchlistTargetForm.changeDownPct ? parseFloat(watchlistTargetForm.changeDownPct) : undefined,
        notes: watchlistTargetForm.notes || undefined,
      };
      
      console.log('📤 发送关注股票目标价数据:', { stockId: watchlistTargetForm.stockId, data });
      return dailyWatchlistApi.updateStock(watchlistTargetForm.stockId, data);
    },
    onSuccess: () => {
      console.log('✅ 关注股票目标价保存成功');
      queryClient.invalidateQueries({ queryKey: ['daily-watchlist'] });
      setShowWatchlistTargetDialog(false);
      setWatchlistTargetForm({ 
        stockId: 0, 
        stockCode: '', 
        stockName: '', 
        currentPrice: 0,
        targetPrice: '', 
        changeUpPct: '', 
        changeDownPct: '',
        notes: ''
      });
      alert('目标价设置成功！');
    },
    onError: (error: any) => {
      console.error('❌ 关注股票目标价保存失败:', error);
      const errorMsg = error?.message || error?.detail || '保存失败，请重试';
      alert(`保存失败: ${errorMsg}`);
    },
  });

  // 删除基准价的mutation
  const deleteTargetPriceMutation = useMutation({
    mutationFn: () => {
      // 通过传null来清空基准价相关字段
      const data = {
        target_price: null as unknown as undefined,
        change_up_pct: null as unknown as undefined,
        change_down_pct: null as unknown as undefined,
      };
      return dailyWatchlistApi.updateStock(watchlistTargetForm.stockId, data);
    },
    onSuccess: () => {
      console.log('✅ 基准价删除成功');
      queryClient.invalidateQueries({ queryKey: ['daily-watchlist'] });
      setShowWatchlistTargetDialog(false);
      setWatchlistTargetForm({ 
        stockId: 0, 
        stockCode: '', 
        stockName: '', 
        currentPrice: 0,
        targetPrice: '', 
        changeUpPct: '', 
        changeDownPct: '',
        notes: ''
      });
      alert('基准价已删除！');
    },
    onError: (error: any) => {
      console.error('❌ 基准价删除失败:', error);
      const errorMsg = error?.message || error?.detail || '删除失败，请重试';
      alert(`删除失败: ${errorMsg}`);
    },
  });

  const watchlistCount = watchlistSummary?.total_stocks || 0;
  const watchlistStocks = useMemo(
    () => watchlistSummary?.dates?.flatMap((dateGroup: any) => dateGroup.stocks || []) || [],
    [watchlistSummary]
  );

  const watchlistQuoteQueries = useQueries({
    queries: watchlistStocks.map((stock: any) => {
      const validCode = stock?.stock_code && !stock.stock_code.startsWith('UNKNOWN');
      const hasSummaryQuote = typeof stock?.price === 'number' && typeof stock?.change_pct === 'number';
      return {
        queryKey: ['watchlist-live-quote', stock.stock_code],
        queryFn: () => stocksApi.getQuote(stock.stock_code),
        enabled: !!validCode && !hasSummaryQuote,
        refetchInterval: 30000,
        staleTime: 10000,
      };
    }),
  });

  const watchlistQuoteMap = useMemo(() => {
    const quoteMap = new Map<string, { price?: number; change_pct?: number; isFetching: boolean }>();
    watchlistStocks.forEach((stock: any, index: number) => {
      const code = stock?.stock_code;
      if (!code) return;
      const query = watchlistQuoteQueries[index];
      quoteMap.set(code, {
        price: query?.data?.price,
        change_pct: query?.data?.change_pct,
        isFetching: !!query?.isFetching
      });
    });
    return quoteMap;
  }, [watchlistStocks, watchlistQuoteQueries]);

  // 实时计算控制区间
  const controlRange = useMemo(() => {
    const targetPrice = parseFloat(watchlistTargetForm.targetPrice) || watchlistTargetForm.currentPrice;
    const changeUpPct = parseFloat(watchlistTargetForm.changeUpPct) || 0;
    const changeDownPct = parseFloat(watchlistTargetForm.changeDownPct) || 0;
    
    if (!targetPrice) return null;
    if (changeUpPct === 0 && changeDownPct === 0) return null;
    
    return {
      upper: targetPrice * (1 + changeUpPct / 100),
      lower: targetPrice * (1 - changeDownPct / 100),
      targetPrice
    };
  }, [watchlistTargetForm.targetPrice, watchlistTargetForm.changeUpPct, watchlistTargetForm.changeDownPct, watchlistTargetForm.currentPrice]);

  // 判断当前价格状态
  const priceStatus = useMemo(() => {
    if (!controlRange || !watchlistTargetForm.currentPrice) return null;
    if (watchlistTargetForm.currentPrice > controlRange.upper) return 'above_upper';
    if (watchlistTargetForm.currentPrice < controlRange.lower) return 'below_lower';
    return 'in_range';
  }, [controlRange, watchlistTargetForm.currentPrice]);

  const openWatchlistTargetDialog = (stock: any) => {
    const currentPrice = stock.price || 0;
    
    setWatchlistTargetForm({
      stockId: stock.id,
      stockCode: stock.stock_code,
      stockName: stock.stock_name,
      currentPrice,
      targetPrice: stock.target_price?.toString() || '',
      changeUpPct: stock.change_up_pct?.toString() || '',
      changeDownPct: stock.change_down_pct?.toString() || '',
      notes: stock.notes || ''
    });
    setShowWatchlistTargetDialog(true);
  };

  // ===== 设置对话框相关 =====
  
  // 查询交易时段配置
  const { data: tradingHoursConfig } = useQuery<TradingHoursConfig>({
    queryKey: ['trading-hours-config'],
    queryFn: async () => {
      return await settingsApi.getTradingHours();
    },
  });

  // 更新交易时段配置mutation
  const updateTradingHoursMutation = useMutation({
    mutationFn: async (newConfig: TradingHoursConfig) => {
      return await settingsApi.updateTradingHours(newConfig);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trading-hours-config'] });
      setHasSettingsChanges(false);
      setSettingsSaveMessage({ type: 'success', text: '配置已保存成功！' });
      setTimeout(() => setSettingsSaveMessage(null), 3000);
    },
    onError: (error: any) => {
      setSettingsSaveMessage({
        type: 'error',
        text: error?.response?.data?.detail || '保存失败，请重试'
      });
    },
  });

  // 重新加载配置mutation
  const reloadTradingHoursMutation = useMutation({
    mutationFn: async () => {
      return await settingsApi.reloadTradingHours();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trading-hours-config'] });
      setSettingsSaveMessage({ type: 'success', text: '配置已重新加载！' });
      setTimeout(() => setSettingsSaveMessage(null), 3000);
    },
  });

  // 初始化设置表单数据
  useEffect(() => {
    if (tradingHoursConfig && !settingsFormData) {
      setSettingsFormData(tradingHoursConfig);
    }
  }, [tradingHoursConfig, settingsFormData]);

  // 跟踪设置表单变化
  useEffect(() => {
    if (tradingHoursConfig && settingsFormData) {
      const changed = JSON.stringify(tradingHoursConfig) !== JSON.stringify(settingsFormData);
      setHasSettingsChanges(changed);
    }
  }, [tradingHoursConfig, settingsFormData]);

  const handleSettingsInputChange = (field: keyof TradingHoursConfig, value: any) => {
    if (!settingsFormData) return;
    setSettingsFormData({ ...settingsFormData, [field]: value });
  };

  const handleTradingDayToggle = (day: number) => {
    if (!settingsFormData) return;
    const currentDays = settingsFormData.trading_days_list;
    const newDays = currentDays.includes(day)
      ? currentDays.filter(d => d !== day)
      : [...currentDays, day].sort();
    
    setSettingsFormData({
      ...settingsFormData,
      trading_days_list: newDays,
      trading_days: newDays.join(','),
    });
  };

  const handleSaveSettings = () => {
    if (!settingsFormData) return;
    updateTradingHoursMutation.mutate(settingsFormData);
  };

  const handleReloadSettings = () => {
    reloadTradingHoursMutation.mutate();
  };

  const openSettingsDialog = () => {
    // 重置表单数据为当前配置
    if (tradingHoursConfig) {
      setSettingsFormData(tradingHoursConfig);
    }
    setHasSettingsChanges(false);
    setSettingsSaveMessage(null);
    setShowSettingsDialog(true);
  };



  useEffect(() => {
    if (!draggingSplitter) return;
    const onMouseMove = (event: MouseEvent) => {
      if (!stockPanelsRef.current) return;
      const rect = stockPanelsRef.current.getBoundingClientRect();
      if (rect.height <= 0) return;
      const nextRatio = (event.clientY - rect.top) / rect.height;
      const clamped = Math.min(0.8, Math.max(0.2, nextRatio));
      setHoldingsRatio(clamped);
    };
    const onMouseUp = () => setDraggingSplitter(false);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };
  }, [draggingSplitter]);

  return (
    <div className={`h-full w-full overflow-hidden flex flex-col border transition-colors duration-300 ${isResizing ? 'transition-none duration-0' : ''} ${
      isDark ? 'border-[#2a2a2a] bg-[#1a1a1a]' : 'border-gray-200 bg-white'
    } shadow-sm rounded-lg`}>
      {/* 指数部分 - 弹性高度但有最小值 */}
      <div className="flex-shrink-0">
        <IndicesPanel 
          selectedIndexCode={selectedIndexCode}
          onSelectIndex={onSelectIndex}
          collapsed={indicesCollapsed}
          onToggleCollapse={() => setIndicesCollapsed((prev) => !prev)}
        />
      </div>
      
      <div
        ref={stockPanelsRef}
        className={`flex-1 min-h-0 flex flex-col ${draggingSplitter ? 'select-none' : ''}`}
      >
        <div
          className={`min-h-0 overflow-hidden border-t ${isDark ? 'border-[#2a2a2a]' : 'border-gray-200'}`}
          style={
            !holdingsCollapsed && !watchlistCollapsed
              ? { flex: `0 0 ${holdingsRatio * 100}%` }
              : holdingsCollapsed
                ? undefined
                : { flex: '1 1 0%' }
          }
        >
          <HoldingsPanel
            allStocks={allStocks}
            holdings={holdings}
            selectedStockCode={selectedStockCode}
            onSelectStock={onSelectStock}
            collapsed={holdingsCollapsed}
            onToggleCollapse={() => setHoldingsCollapsed((prev) => !prev)}
          />
        </div>

        {!holdingsCollapsed && !watchlistCollapsed && (
          <div
            onMouseDown={(e) => {
              e.preventDefault();
              setDraggingSplitter(true);
            }}
            className={`h-2 cursor-row-resize border-t border-b ${
              isDark ? 'border-[#2a2a2a] bg-[#141414] hover:bg-[#1f2937]' : 'border-gray-200 bg-gray-50 hover:bg-gray-100'
            }`}
            title="拖动调整自持股票和动态关注股票高度"
          />
        )}

        <div
          className={`min-h-0 overflow-hidden border-t ${isDark ? 'border-[#2a2a2a]' : 'border-gray-200'}`}
          style={
            !holdingsCollapsed && !watchlistCollapsed
              ? { flex: `0 0 ${(1 - holdingsRatio) * 100}%` }
              : watchlistCollapsed
                ? undefined
                : { flex: '1 1 0%' }
          }
        >
          <div className={`h-full flex flex-col ${isDark ? 'bg-[#1a1a1a]' : 'bg-white'}`}>
            <WatchlistPanelHeader
              count={watchlistCount}
              isDark={isDark}
              collapsed={watchlistCollapsed}
              onToggleCollapse={() => setWatchlistCollapsed((prev) => !prev)}
              actions={
                <div className="flex gap-1">
                  <button
                    onClick={() => setShowArchived(!showArchived)}
                    className={`p-1 transition-colors ${
                      showArchived
                        ? isDark ? 'text-purple-400 bg-purple-900/30' : 'text-purple-500 bg-purple-50'
                        : isDark ? 'hover:bg-purple-900/30 text-gray-500 hover:text-purple-400' : 'hover:bg-purple-50 text-gray-400 hover:text-purple-500'
                    }`}
                    title={showArchived ? "查看当前关注" : "查看归档记录"}
                  >
                    <Archive size={16} />
                  </button>
                  <button
                    onClick={() => setShowWatchlistSecondLine(!showWatchlistSecondLine)}
                    className={`p-1 transition-colors ${
                      isDark
                        ? 'hover:bg-purple-900/30 text-gray-500 hover:text-purple-400'
                        : 'hover:bg-purple-50 text-gray-400 hover:text-purple-500'
                    } ${showWatchlistSecondLine ? (isDark ? 'text-purple-400' : 'text-purple-500') : ''}`}
                    title={showWatchlistSecondLine ? "隐藏目标价信息" : "显示目标价信息"}
                  >
                    {showWatchlistSecondLine ? <Eye size={16} /> : <EyeOff size={16} />}
                  </button>
                  <button
                    onClick={() => setShowAddDialog(true)}
                    className={`p-1 transition-colors ${
                      isDark
                        ? 'hover:bg-blue-900/30 text-gray-500 hover:text-blue-400'
                        : 'hover:bg-blue-50 text-gray-400 hover:text-blue-500'
                    }`}
                    title="添加动态关注股票"
                  >
                    <Plus size={16} />
                  </button>
                </div>
              }
            />

            {!watchlistCollapsed && (
              <div className="flex-1 min-h-0 overflow-y-auto pr-2 [scrollbar-gutter:stable]">
                {watchlistLoading ? (
                  <div className={`h-full flex items-center justify-center text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                    加载中...
                  </div>
                ) : watchlistSummary?.dates?.length ? (
                  watchlistSummary.dates.map((dateGroup: any) => (
                    <div key={dateGroup.watch_date} className={`border-b ${isDark ? 'border-[#2a2a2a]' : 'border-gray-100'}`}>
                      <div className={`px-3 py-1 text-[11px] font-semibold ${
                        isDark ? 'bg-[#141414] text-gray-400' : 'bg-gray-50 text-gray-500'
                      }`}>
                        {dateGroup.watch_date}
                      </div>
                      {dateGroup.stocks.map((stock: any) => {
                        const fallbackQuote = watchlistQuoteMap.get(stock.stock_code);
                        const displayPrice = typeof stock.price === 'number' ? stock.price : fallbackQuote?.price;
                        const displayChangePct = typeof stock.change_pct === 'number' ? stock.change_pct : fallbackQuote?.change_pct;
                        const hasQuote = typeof displayPrice === 'number' && typeof displayChangePct === 'number';
                        const isUpdating = stock.quote_is_updating || fallbackQuote?.isFetching;
                        const isSelected = selectedStockCode === stock.stock_code;
                        const changePct = displayChangePct ?? 0;
                        const isUp = changePct > 0;
                        const isDown = changePct < 0;
                        const denominator = 1 + changePct / 100;
                        const changeAmount = hasQuote && denominator !== 0 ? displayPrice - displayPrice / denominator : null;
                        const changeAmountText = changeAmount !== null
                          ? `${changeAmount >= 0 ? '+' : ''}${changeAmount.toFixed(2)}`
                          : '--';
                        const quoteToneClass = isUp
                          ? isDark ? 'text-red-400' : 'text-red-500'
                          : isDown ? isDark ? 'text-green-400' : 'text-green-500'
                          : isDark ? 'text-gray-300' : 'text-gray-600';
                        const quoteValueClass = isUp
                          ? isDark ? 'text-red-400' : 'text-red-500'
                          : isDown ? isDark ? 'text-green-400' : 'text-green-500'
                          : isDark ? 'text-gray-400' : 'text-gray-500';
                        
                        // 计算目标价相关信息
                        const hasTarget = stock.target_price || stock.change_up_pct || stock.change_down_pct;
                        
                        return (
                          <div
                            key={stock.id}
                            onClick={() => stock.stock_code && !stock.stock_code.startsWith('UNKNOWN') && onSelectStock(stock.stock_code)}
                            className={`px-3 py-2 border-t transition-colors ${
                              isSelected
                                ? isDark
                                  ? 'bg-blue-900/20 border-[#2a2a2a] hover:bg-blue-900/30'
                                  : 'bg-blue-50 border-gray-100 hover:bg-blue-100'
                                : isDark
                                  ? 'border-[#2a2a2a] hover:bg-[#2a2a2a]'
                                  : 'bg-white border-gray-100 hover:bg-gray-50'
                            }`}
                            style={!isSelected && isDark ? { backgroundColor: LEFT_PANEL_DARK_ITEM_BG } : undefined}
                          >
                            <div className="flex items-center justify-between">
                              <div className="min-w-0 flex-1">
                                <div className="flex items-center gap-2">
                                  <span className={`text-xs font-bold truncate ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
                                    {stock.stock_name}
                                  </span>
                                  <span className={`text-[10px] font-mono ${isDark ? 'text-[#ffff00]' : 'text-gray-400'}`}>
                                    {stock.stock_code}
                                  </span>
                                </div>
                                {stock.reason && (
                                  <div className={`text-[10px] mt-1 truncate ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
                                    {stock.reason}
                                  </div>
                                )}
                              </div>
                              <div className="flex items-center gap-2.5 flex-shrink-0">
                                <div className={`px-2 py-1 rounded-md ${
                                  isSelected
                                    ? isDark ? 'bg-blue-900/20' : 'bg-blue-50'
                                    : isDark ? '' : 'bg-white'
                                }`} style={!isSelected && isDark ? { backgroundColor: LEFT_PANEL_DARK_ITEM_BG } : undefined}>
                                  <div className={`text-sm font-mono font-bold text-right ${quoteValueClass}`}>
                                    {hasQuote ? displayPrice.toFixed(2) : isUpdating ? '更新中' : '--'}
                                  </div>
                                  <div className={`flex items-center justify-end gap-1 text-[10px] font-semibold ${quoteToneClass}`}>
                                    {isUpdating && !hasQuote ? (
                                      <Loader2 size={11} className="animate-spin" />
                                    ) : hasQuote && isUp ? (
                                      <TrendingUp size={11} />
                                    ) : hasQuote && isDown ? (
                                      <TrendingDown size={11} />
                                    ) : (
                                      <Minus size={11} />
                                    )}
                                    <span>{hasQuote ? `${isUp ? '+' : ''}${changePct.toFixed(2)}%` : '--'}</span>
                                    <span className={isDark ? 'text-gray-500' : 'text-gray-400'}>/</span>
                                    <span>{hasQuote ? changeAmountText : '--'}</span>
                                  </div>
                                </div>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    openWatchlistTargetDialog(stock);
                                  }}
                                  className={`p-1 transition-colors ${
                                    hasTarget
                                      ? isDark ? 'text-yellow-400 hover:text-yellow-300' : 'text-yellow-500 hover:text-yellow-600'
                                      : isDark ? 'text-gray-500 hover:text-gray-300' : 'text-gray-400 hover:text-gray-600'
                                  }`}
                                  title="设置目标价"
                                >
                                  <Target size={14} />
                                </button>
                                {stock.is_archived ? (
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      unarchiveMutation.mutate([stock.id]);
                                    }}
                                    className={`p-1 transition-colors ${
                                      isDark
                                        ? 'text-gray-500 hover:text-green-400 hover:bg-green-900/20'
                                        : 'text-gray-400 hover:text-green-500 hover:bg-green-50'
                                    }`}
                                    title="恢复关注"
                                  >
                                    <ArchiveRestore size={14} />
                                  </button>
                                ) : (
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      deleteWatchlistMutation.mutate(stock.id);
                                    }}
                                    className={`p-1 transition-colors ${
                                      isDark
                                        ? 'text-gray-500 hover:text-red-400 hover:bg-red-900/20'
                                        : 'text-gray-400 hover:text-red-500 hover:bg-red-50'
                                    }`}
                                    title="删除关注"
                                  >
                                    <Trash2 size={14} />
                                  </button>
                                )}
                              </div>
                            </div>
                            {/* 第二行：基准价信息 */}
                            {showWatchlistSecondLine && (
                              <div className={`mt-1 text-[10px] ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                                {hasTarget ? (
                                  <>
                                    {(() => {
                                      // 计算控制区间
                                      const basePrice = stock.target_price;
                                      const upper = basePrice * (1 + (stock.change_up_pct || 0) / 100);
                                      const lower = basePrice * (1 - (stock.change_down_pct || 0) / 100);
                                      const currentPrice = displayPrice;
                                      
                                      // 计算涨跌百分比例（当前股价相对于基准价）
                                      const changePct = currentPrice ? ((currentPrice - basePrice) / basePrice) * 100 : null;
                                      
                                      // 判断当前价格状态
                                      let priceStatus = 'in_range';
                                      if (currentPrice) {
                                        if (currentPrice > upper) priceStatus = 'above_upper';
                                        else if (currentPrice < lower) priceStatus = 'below_lower';
                                      }
                                      
                                      return (
                                        <>
                                          {/* 基准价和控制区间 */}
                                          <div className="flex items-center gap-2 mb-1">
                                            <span>
                                              基准价: <span className={isDark ? 'text-yellow-400' : 'text-yellow-600'}>
                                                {basePrice.toFixed(2)}
                                              </span>
                                            </span>
                                            <span className={isDark ? 'text-gray-500' : 'text-gray-400'}>|</span>
                                            <span>
                                              区间: 
                                              <span className={isDark ? 'text-green-400' : 'text-green-500'}> {lower.toFixed(2)}</span>
                                              <span className={isDark ? 'text-gray-500' : 'text-gray-400'}> ~ </span>
                                              <span className={isDark ? 'text-red-400' : 'text-red-500'}>{upper.toFixed(2)}</span>
                                            </span>
                                          </div>
                                          
                                          {/* 涨跌比例和控制比例 */}
                                          {currentPrice && (
                                            <div className="flex items-center gap-2 mb-1">
                                              {changePct !== null && (
                                                <span>
                                                  涨跌: <span className={
                                                    changePct > 0 
                                                      ? (isDark ? 'text-red-400' : 'text-red-500')
                                                      : changePct < 0 
                                                        ? (isDark ? 'text-green-400' : 'text-green-500')
                                                        : (isDark ? 'text-gray-400' : 'text-gray-500')
                                                  }>
                                                    {changePct > 0 ? '+' : ''}{changePct.toFixed(2)}%
                                                  </span>
                                                </span>
                                              )}
                                              
                                              <span className={isDark ? 'text-gray-500' : 'text-gray-400'}>|</span>
                                              
                                              <span>
                                                控制比例: 
                                                <span className={isDark ? 'text-red-400' : 'text-red-500'}> +{stock.change_up_pct || 0}%</span>
                                                <span className={isDark ? 'text-gray-400' : 'text-gray-500'}> / </span>
                                                <span className={isDark ? 'text-green-400' : 'text-green-500'}>-{stock.change_down_pct || 0}%</span>
                                              </span>
                                            </div>
                                          )}
                                          
                                          {/* 当前状态 */}
                                          {currentPrice && (
                                            <div className={`flex items-center gap-2 ${
                                              priceStatus === 'above_upper' ? (isDark ? 'text-red-400' : 'text-red-600') :
                                              priceStatus === 'below_lower' ? (isDark ? 'text-green-400' : 'text-green-600') :
                                              (isDark ? 'text-blue-400' : 'text-blue-600')
                                            }`}>
                                              {priceStatus === 'above_upper' && '⚠️ 超出上限'}
                                              {priceStatus === 'below_lower' && '⚠️ 跌破下限'}
                                              {priceStatus === 'in_range' && '✓ 正常'}
                                              
                                              {stock.stop_loss_price && (
                                                <span className="text-gray-500 ml-2">
                                                  硬止损: {stock.stop_loss_price.toFixed(2)}
                                                </span>
                                              )}
                                            </div>
                                          )}
                                          
                                          {/* 备注 */}
                                          {stock.notes && (
                                            <div className="mt-1 truncate italic opacity-75">
                                              📝 {stock.notes}
                                            </div>
                                          )}
                                        </>
                                      );
                                    })()}
                                  </>
                                ) : (
                                  <span className="italic opacity-50">点击 🎯 图标设置基准价</span>
                                )}
                                
                                {/* 归档标记 */}
                                {stock.is_archived && (
                                  <div className={`text-[10px] mt-1 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                                    📦 已归档 {stock.archived_at ? `(${new Date(stock.archived_at).toLocaleDateString()})` : ''}
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  ))
                ) : (
                  <div className={`h-full flex items-center justify-center text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                    暂无动态关注股票
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 底部设置按钮 */}
      <div className={`flex-shrink-0 border-t ${isDark ? 'border-[#2a2a2a]' : 'border-gray-200'}`}>
        <button
          onClick={openSettingsDialog}
          className={`w-full px-4 py-3 flex items-center justify-center gap-2 transition-colors ${
            isDark 
              ? 'bg-[#1a1a1a] hover:bg-[#2a2a2a] text-gray-400 hover:text-gray-200' 
              : 'bg-white hover:bg-gray-50 text-gray-600 hover:text-gray-900'
          }`}
          title="系统设置"
        >
          <Settings size={16} />
          <span className="text-xs font-medium">系统设置</span>
        </button>
      </div>

      {showAddDialog && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50" onClick={() => setShowAddDialog(false)}>
          <div
            className={`p-4 w-80 shadow-xl border ${
              isDark ? 'bg-[#1a1a1a] border-[#2a2a2a]' : 'bg-white border-gray-200'
            }`}
            onClick={(e) => e.stopPropagation()}
          >
            <h4 className={`font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>添加动态关注股票</h4>
            <div className="space-y-3">
              <div>
                <label className={`text-xs mb-1 block ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>股票名称</label>
                <input
                  type="text"
                  className={`w-full px-3 py-2 border text-sm focus:outline-none ${
                    isDark
                      ? 'border-[#3a3a3a] bg-[#0a0a0a] text-white focus:border-blue-500'
                      : 'border-gray-300 bg-white text-gray-900 focus:border-blue-500'
                  }`}
                  value={watchlistStockName}
                  onChange={(e) => setWatchlistStockName(e.target.value)}
                  placeholder="如：中煤能源"
                />
              </div>
              <div>
                <label className={`text-xs mb-1 block ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>股票代码（可选）</label>
                <input
                  type="text"
                  className={`w-full px-3 py-2 border text-sm focus:outline-none ${
                    isDark
                      ? 'border-[#3a3a3a] bg-[#0a0a0a] text-white focus:border-blue-500'
                      : 'border-gray-300 bg-white text-gray-900 focus:border-blue-500'
                  }`}
                  value={watchlistStockCode}
                  onChange={(e) => setWatchlistStockCode(e.target.value)}
                  placeholder="如：601898"
                />
              </div>
              <div>
                <label className={`text-xs mb-1 block ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>关注日期</label>
                <input
                  type="date"
                  className={`w-full px-3 py-2 border text-sm focus:outline-none ${
                    isDark
                      ? 'border-[#3a3a3a] bg-[#0a0a0a] text-white focus:border-blue-500'
                      : 'border-gray-300 bg-white text-gray-900 focus:border-blue-500'
                  }`}
                  value={watchlistDate}
                  onChange={(e) => setWatchlistDate(e.target.value)}
                />
              </div>
              <div>
                <label className={`text-xs mb-1 block ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>关注理由（可选）</label>
                <input
                  type="text"
                  className={`w-full px-3 py-2 border text-sm focus:outline-none ${
                    isDark
                      ? 'border-[#3a3a3a] bg-[#0a0a0a] text-white focus:border-blue-500'
                      : 'border-gray-300 bg-white text-gray-900 focus:border-blue-500'
                  }`}
                  value={watchlistReason}
                  onChange={(e) => setWatchlistReason(e.target.value)}
                  placeholder="如：突破关键位"
                />
              </div>
            </div>
            <div className="flex gap-2 mt-4">
              <button
                onClick={() => setShowAddDialog(false)}
                className={`flex-1 px-3 py-2 border text-sm transition-colors ${
                  isDark
                    ? 'border-[#3a3a3a] text-gray-300 hover:bg-[#2a2a2a]'
                    : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                }`}
              >
                取消
              </button>
              <button
                onClick={() => addWatchlistMutation.mutate()}
                disabled={!watchlistStockName.trim() || !watchlistDate || addWatchlistMutation.isPending}
                className="flex-1 px-3 py-2 bg-blue-600 text-white text-sm hover:bg-blue-700 disabled:opacity-50"
              >
                {addWatchlistMutation.isPending ? '添加中...' : '添加'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 目标价设置对话框 */}
      {showWatchlistTargetDialog && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50" onClick={() => setShowWatchlistTargetDialog(false)}>
          <div
            className={`p-4 w-96 shadow-xl border max-h-[90vh] overflow-y-auto ${
              isDark ? 'bg-[#1a1a1a] border-[#2a2a2a]' : 'bg-white border-gray-200'
            }`}
            onClick={(e) => e.stopPropagation()}
          >
            <h4 className={`font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              设置基准价 - {watchlistTargetForm.stockName}
            </h4>
            
            {/* 当前股价显示 */}
            <div className={`mb-3 p-2 rounded ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-50'}`}>
              <div className="text-xs text-gray-500">当前股价</div>
              <div className={`text-lg font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                ¥{watchlistTargetForm.currentPrice?.toFixed(2) || '--'}
              </div>
            </div>
            
            <div className="space-y-3">
              {/* 目标价格 */}
              <div>
                <label className={`text-xs mb-1 block ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  基准价格
                </label>
                <input
                  type="number"
                  step="0.01"
                  className={`w-full px-3 py-2 border text-sm focus:outline-none ${
                    isDark
                      ? 'border-[#3a3a3a] bg-[#0a0a0a] text-white focus:border-blue-500'
                      : 'border-gray-300 bg-white text-gray-900 focus:border-blue-500'
                  }`}
                  placeholder={`默认: ${watchlistTargetForm.currentPrice?.toFixed(2)}`}
                  value={watchlistTargetForm.targetPrice}
                  onChange={(e) => setWatchlistTargetForm({ ...watchlistTargetForm, targetPrice: e.target.value })}
                />
                <div className="text-xs text-gray-500 mt-1">
                  留空则使用当前股价
                </div>
              </div>
              
              {/* 涨跌控制 */}
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className={`text-xs mb-1 block ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    上涨控制 (%)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    className={`w-full px-3 py-2 border text-sm focus:outline-none ${
                      isDark
                        ? 'border-[#3a3a3a] bg-[#0a0a0a] text-white focus:border-blue-500'
                        : 'border-gray-300 bg-white text-gray-900 focus:border-blue-500'
                    }`}
                    placeholder="如: 20"
                    value={watchlistTargetForm.changeUpPct}
                    onChange={(e) => setWatchlistTargetForm({ ...watchlistTargetForm, changeUpPct: e.target.value })}
                  />
                </div>
                <div>
                  <label className={`text-xs mb-1 block ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    下跌控制 (%)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    className={`w-full px-3 py-2 border text-sm focus:outline-none ${
                      isDark
                        ? 'border-[#3a3a3a] bg-[#0a0a0a] text-white focus:border-blue-500'
                        : 'border-gray-300 bg-white text-gray-900 focus:border-blue-500'
                    }`}
                    placeholder="如: 10"
                    value={watchlistTargetForm.changeDownPct}
                    onChange={(e) => setWatchlistTargetForm({ ...watchlistTargetForm, changeDownPct: e.target.value })}
                  />
                </div>
              </div>
              
              {/* 实时控制区间显示 */}
              {controlRange && (
                <div className={`p-3 rounded-lg border ${
                  isDark ? 'bg-blue-900/20 border-blue-800' : 'bg-blue-50 border-blue-200'
                }`}>
                  <div className="text-xs font-semibold mb-2">
                    <span className={isDark ? 'text-blue-400' : 'text-blue-600'}>📊 控制区间</span>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className={`p-2 rounded ${isDark ? 'bg-[#1a1a1a]' : 'bg-white'}`}>
                      <div className={isDark ? 'text-gray-400' : 'text-gray-500'}>上限</div>
                      <div className={`font-bold ${isDark ? 'text-red-400' : 'text-red-500'}`}>
                        ¥{controlRange.upper.toFixed(2)}
                      </div>
                      <div className={`text-[10px] ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                        目标价 × (1 + {watchlistTargetForm.changeUpPct}%)
                      </div>
                    </div>
                    
                    <div className={`p-2 rounded ${isDark ? 'bg-[#1a1a1a]' : 'bg-white'}`}>
                      <div className={isDark ? 'text-gray-400' : 'text-gray-500'}>下限</div>
                      <div className={`font-bold ${isDark ? 'text-green-400' : 'text-green-500'}`}>
                        ¥{controlRange.lower.toFixed(2)}
                      </div>
                      <div className={`text-[10px] ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                        目标价 × (1 - {watchlistTargetForm.changeDownPct}%)
                      </div>
                    </div>
                  </div>
                  
                  {/* 当前价格状态 */}
                  {watchlistTargetForm.currentPrice > 0 && (
                    <div className={`mt-2 pt-2 border-t ${isDark ? 'border-blue-800' : 'border-blue-200'}`}>
                      <div className="flex items-center justify-between text-xs">
                        <span className={isDark ? 'text-gray-400' : 'text-gray-500'}>当前状态</span>
                        <span className={`font-bold ${
                          priceStatus === 'in_range' ? (isDark ? 'text-blue-400' : 'text-blue-600') :
                          priceStatus === 'above_upper' ? (isDark ? 'text-red-400' : 'text-red-600') :
                          (isDark ? 'text-green-400' : 'text-green-600')
                        }`}>
                          {priceStatus === 'in_range' && '✓ 在控制范围内'}
                          {priceStatus === 'above_upper' && '⚠️ 超出上限'}
                          {priceStatus === 'below_lower' && '⚠️ 跌破下限'}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              )}
              
              {/* 备注 */}
              <div>
                <label className={`text-xs mb-1 block ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  备注说明
                </label>
                <textarea
                  className={`w-full px-3 py-2 border text-sm focus:outline-none ${
                    isDark
                      ? 'border-[#3a3a3a] bg-[#0a0a0a] text-white focus:border-blue-500'
                      : 'border-gray-300 bg-white text-gray-900 focus:border-blue-500'
                  }`}
                  placeholder="如：技术面突破，关注回踩支撑"
                  rows={2}
                  value={watchlistTargetForm.notes}
                  onChange={(e) => setWatchlistTargetForm({ ...watchlistTargetForm, notes: e.target.value })}
                />
              </div>
            </div>
            
            <div className="flex gap-3 mt-4 justify-center">
              <button
                onClick={() => setShowWatchlistTargetDialog(false)}
                className={`min-w-[100px] px-4 py-2 border text-sm transition-colors ${
                  isDark
                    ? 'border-[#3a3a3a] text-gray-300 hover:bg-[#2a2a2a]'
                    : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                }`}
              >
                取消
              </button>
              <button
                onClick={() => updateWatchlistTargetMutation.mutate()}
                disabled={updateWatchlistTargetMutation.isPending}
                className="min-w-[100px] px-4 py-2 bg-blue-600 text-white text-sm hover:bg-blue-700 disabled:opacity-50"
              >
                {updateWatchlistTargetMutation.isPending ? '保存中...' : '保存'}
              </button>
              <button
                onClick={() => {
                  if (confirm('确定要删除该股票的基准价设置吗？')) {
                    deleteTargetPriceMutation.mutate();
                  }
                }}
                disabled={deleteTargetPriceMutation.isPending}
                className={`min-w-[100px] px-4 py-2 border text-sm transition-colors flex items-center justify-center gap-1 ${
                  isDark
                    ? 'border-red-800 text-red-400 hover:bg-red-900/30'
                    : 'border-red-300 text-red-600 hover:bg-red-50'
                } disabled:opacity-50`}
              >
                <Trash2 className="w-3 h-3" />
                {deleteTargetPriceMutation.isPending ? '删除中...' : '删除'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 系统设置对话框 */}
      {showSettingsDialog && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50" onClick={() => setShowSettingsDialog(false)}>
          <div
            className={`p-6 w-[600px] max-h-[90vh] overflow-y-auto shadow-xl border ${
              isDark ? 'bg-[#1a1a1a] border-[#2a2a2a]' : 'bg-white border-gray-200'
            }`}
            onClick={(e) => e.stopPropagation()}
          >
            {/* 标题栏 */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Settings size={20} className={isDark ? 'text-blue-400' : 'text-blue-600'} />
                <h3 className={`text-lg font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                  系统设置
                </h3>
              </div>
              <div className="flex items-center gap-2">
                {hasSettingsChanges && (
                  <span className={`text-xs ${isDark ? 'text-yellow-400' : 'text-yellow-600'}`}>
                    有未保存的更改
                  </span>
                )}
                <button
                  onClick={handleReloadSettings}
                  disabled={reloadTradingHoursMutation.isPending}
                  className={`flex items-center gap-1 px-3 py-1.5 text-xs border transition-colors ${
                    isDark
                      ? 'border-[#3a3a3a] text-gray-300 hover:bg-[#2a2a2a]'
                      : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <RefreshCw size={14} className={reloadTradingHoursMutation.isPending ? 'animate-spin' : ''} />
                  <span>重新加载</span>
                </button>
                <button
                  onClick={handleSaveSettings}
                  disabled={!hasSettingsChanges || updateTradingHoursMutation.isPending}
                  className={`flex items-center gap-1 px-3 py-1.5 text-xs border transition-colors ${
                    hasSettingsChanges
                      ? 'bg-blue-600 text-white hover:bg-blue-700 border-blue-600'
                      : isDark
                        ? 'border-[#3a3a3a] text-gray-500 cursor-not-allowed'
                        : 'border-gray-300 text-gray-400 cursor-not-allowed'
                  }`}
                >
                  <Save size={14} />
                  <span>{updateTradingHoursMutation.isPending ? '保存中...' : '保存'}</span>
                </button>
              </div>
            </div>

            {/* 保存消息 */}
            {settingsSaveMessage && (
              <div className={`mb-4 px-3 py-2 rounded text-sm ${
                settingsSaveMessage.type === 'success'
                  ? isDark ? 'bg-green-900/30 text-green-400' : 'bg-green-50 text-green-700'
                  : isDark ? 'bg-red-900/30 text-red-400' : 'bg-red-50 text-red-700'
              }`}>
                {settingsSaveMessage.text}
              </div>
            )}

            {!settingsFormData ? (
              <div className="flex items-center justify-center py-12">
                <RefreshCw size={24} className={`animate-spin ${isDark ? 'text-blue-400' : 'text-blue-600'}`} />
              </div>
            ) : (
              <div className="space-y-6">
                {/* 交易时段设置 */}
                <div className={`p-4 rounded ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-50'}`}>
                  <div className="flex items-center gap-2 mb-3">
                    <Clock size={16} className={isDark ? 'text-blue-400' : 'text-blue-600'} />
                    <h4 className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                      交易时段设置
                    </h4>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    {/* 上午盘 */}
                    <div>
                      <label className={`block text-xs mb-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                        上午盘时段
                      </label>
                      <div className="flex items-center gap-2">
                        <input
                          type="time"
                          value={settingsFormData.morning_session_start}
                          onChange={(e) => handleSettingsInputChange('morning_session_start', e.target.value)}
                          className={`flex-1 px-2 py-1 text-xs border ${
                            isDark
                              ? 'border-[#3a3a3a] bg-[#1a1a1a] text-white'
                              : 'border-gray-300 bg-white text-gray-900'
                          }`}
                        />
                        <span className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>至</span>
                        <input
                          type="time"
                          value={settingsFormData.morning_session_end}
                          onChange={(e) => handleSettingsInputChange('morning_session_end', e.target.value)}
                          className={`flex-1 px-2 py-1 text-xs border ${
                            isDark
                              ? 'border-[#3a3a3a] bg-[#1a1a1a] text-white'
                              : 'border-gray-300 bg-white text-gray-900'
                          }`}
                        />
                      </div>
                    </div>

                    {/* 下午盘 */}
                    <div>
                      <label className={`block text-xs mb-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                        下午盘时段
                      </label>
                      <div className="flex items-center gap-2">
                        <input
                          type="time"
                          value={settingsFormData.afternoon_session_start}
                          onChange={(e) => handleSettingsInputChange('afternoon_session_start', e.target.value)}
                          className={`flex-1 px-2 py-1 text-xs border ${
                            isDark
                              ? 'border-[#3a3a3a] bg-[#1a1a1a] text-white'
                              : 'border-gray-300 bg-white text-gray-900'
                          }`}
                        />
                        <span className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>至</span>
                        <input
                          type="time"
                          value={settingsFormData.afternoon_session_end}
                          onChange={(e) => handleSettingsInputChange('afternoon_session_end', e.target.value)}
                          className={`flex-1 px-2 py-1 text-xs border ${
                            isDark
                              ? 'border-[#3a3a3a] bg-[#1a1a1a] text-white'
                              : 'border-gray-300 bg-white text-gray-900'
                          }`}
                        />
                      </div>
                    </div>
                  </div>

                  {/* 交易日 */}
                  <div className="mt-4">
                    <label className={`block text-xs mb-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                      交易日
                    </label>
                    <div className="flex flex-wrap gap-1">
                      {WEEKDAYS.map((day) => {
                        const isSelected = settingsFormData.trading_days_list.includes(day.value);
                        return (
                          <button
                            key={day.value}
                            onClick={() => handleTradingDayToggle(day.value)}
                            className={`px-2 py-1 text-xs transition-colors ${
                              isSelected
                                ? 'bg-blue-600 text-white'
                                : isDark
                                  ? 'bg-[#1a1a1a] text-gray-400 hover:bg-[#3a3a3a]'
                                  : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
                            }`}
                          >
                            {day.label}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </div>

                {/* 监控设置 */}
                <div className={`p-4 rounded ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-50'}`}>
                  <div className="flex items-center gap-2 mb-3">
                    <Bell size={16} className={isDark ? 'text-blue-400' : 'text-blue-600'} />
                    <h4 className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                      监控设置
                    </h4>
                  </div>

                  <div className="space-y-3">
                    {/* 启用价格提醒监控 */}
                    <div className="flex items-center justify-between">
                      <div>
                        <label className={`block text-xs font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                          启用价格提醒监控
                        </label>
                        <p className={`text-[10px] ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
                          在交易时段内自动监控价格提醒
                        </p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={settingsFormData.enable_price_alert_monitoring}
                          onChange={(e) => handleSettingsInputChange('enable_price_alert_monitoring', e.target.checked)}
                          className="sr-only peer"
                        />
                        <div className="w-9 h-5 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-green-600"></div>
                      </label>
                    </div>

                    {/* 触发后自动停止 */}
                    <div className="flex items-center justify-between">
                      <div>
                        <label className={`block text-xs font-medium ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                          触发后自动停止
                        </label>
                        <p className={`text-[10px] ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
                          预警触发后自动停止监控，避免重复推送
                        </p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={settingsFormData.auto_stop_after_trigger}
                          onChange={(e) => handleSettingsInputChange('auto_stop_after_trigger', e.target.checked)}
                          className="sr-only peer"
                        />
                        <div className="w-9 h-5 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-green-600"></div>
                      </label>
                    </div>

                    {/* 检查频率 */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className={`block text-xs mb-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                          价格提醒检查频率（分钟）
                        </label>
                        <input
                          type="number"
                          min="1"
                          max="60"
                          value={settingsFormData.price_alert_check_interval}
                          onChange={(e) => handleSettingsInputChange('price_alert_check_interval', parseInt(e.target.value) || 1)}
                          className={`w-full px-2 py-1 text-xs border ${
                            isDark
                              ? 'border-[#3a3a3a] bg-[#1a1a1a] text-white'
                              : 'border-gray-300 bg-white text-gray-900'
                          }`}
                        />
                        <p className={`text-[10px] mt-1 ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
                          建议值：1-5分钟
                        </p>
                      </div>

                      <div>
                        <label className={`block text-xs mb-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                          市场情绪更新频率（分钟）
                        </label>
                        <input
                          type="number"
                          min="1"
                          max="60"
                          value={settingsFormData.market_sentiment_update_interval}
                          onChange={(e) => handleSettingsInputChange('market_sentiment_update_interval', parseInt(e.target.value) || 5)}
                          className={`w-full px-2 py-1 text-xs border ${
                            isDark
                              ? 'border-[#3a3a3a] bg-[#1a1a1a] text-white'
                              : 'border-gray-300 bg-white text-gray-900'
                          }`}
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* 说明 */}
                <div className={`p-3 rounded border ${
                  isDark ? 'bg-blue-900/20 border-blue-800' : 'bg-blue-50 border-blue-200'
                }`}>
                  <div className="flex items-start gap-2">
                    <AlertCircle size={14} className={`mt-0.5 flex-shrink-0 ${isDark ? 'text-blue-400' : 'text-blue-600'}`} />
                    <div className={`text-xs ${isDark ? 'text-blue-300' : 'text-blue-700'}`}>
                      <p className="font-medium mb-1">配置说明</p>
                      <ul className="list-disc list-inside space-y-0.5 text-[10px]">
                        <li>配置修改后需点击"保存"按钮生效</li>
                        <li>时间格式：24小时制（HH:MM）</li>
                        <li>配置存储在 backend/config/trading_hours.ini</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* 关闭按钮 */}
            <div className="mt-4 flex justify-end">
              <button
                onClick={() => setShowSettingsDialog(false)}
                className={`px-4 py-2 text-sm border transition-colors ${
                  isDark
                    ? 'border-[#3a3a3a] text-gray-300 hover:bg-[#2a2a2a]'
                    : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                }`}
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
