import { useState, useMemo } from 'react';
import { Plus, TrendingUp, TrendingDown, Minus, RefreshCw, Target, Eye, EyeOff, Trash2 } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { holdingsApi } from '../services/api';
import { useTheme } from '../contexts/ThemeContext';
import HoldingsPanelHeader from './HoldingsPanelHeader';
import marketNewsThemeRaw from '../config/marketNewsTheme.json?raw';

interface HoldingsStyleConfig {
  darkItemCardBg?: string;
}

const parsedHoldingsStyleConfig = (() => {
  try {
    return JSON.parse(marketNewsThemeRaw) as HoldingsStyleConfig;
  } catch {
    return {};
  }
})();

const HOLDINGS_DARK_ITEM_BG = parsedHoldingsStyleConfig.darkItemCardBg ?? '#111827';

interface Stock {
  code: string;
  name: string;
  price?: number;
  current_price?: number;
  change_pct?: number;
  sector?: string;
  target_price?: number | null;
  change_up_pct?: number | null;
  change_down_pct?: number | null;
  stop_loss_price?: number | null;
  notes?: string | null;
}

interface Sector {
  name: string;
  stocks: Stock[];
}

interface HoldingsPanelProps {
  allStocks: any[];
  holdings: { sectors: Sector[] };
  selectedStockCode?: string;
  onSelectStock: (code: string) => void;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

export default function HoldingsPanel({ 
  allStocks, 
  holdings, 
  selectedStockCode, 
  onSelectStock,
  collapsed = false,
  onToggleCollapse,
}: HoldingsPanelProps) {
  const queryClient = useQueryClient();
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [addForm, setAddForm] = useState({ sectorName: '', stockName: '', stockCode: '' });
  const [expandedSector, setExpandedSector] = useState<string | null>(null);
  const [showSecondLine, setShowSecondLine] = useState(true);
  const [showTargetDialog, setShowTargetDialog] = useState(false);
  const [targetForm, setTargetForm] = useState({
    sectorName: '',
    stockName: '',
    stockCode: '',
    currentPrice: 0,
    targetPrice: '',
    changeUpPct: '',
    changeDownPct: '',
    notes: ''
  });

  const addStockMutation = useMutation({
    mutationFn: () => holdingsApi.addStock(addForm.sectorName, addForm.stockName, addForm.stockCode || undefined),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['holdings'] });
      setShowAddDialog(false);
      setAddForm({ sectorName: '', stockName: '', stockCode: '' });
    },
  });

  const refreshMutation = useMutation({
    mutationFn: holdingsApi.refreshHoldings,
    onSuccess: () => {
      // 必须使 initial-data 失效，因为 Dashboard 使用它来显示股票列表
      queryClient.invalidateQueries({ queryKey: ['initial-data'] });
      // 同时使 holdings 失效以防万一其他地方也用了
      queryClient.invalidateQueries({ queryKey: ['holdings'] });
    },
  });

  const updateTargetMutation = useMutation({
    mutationFn: () => {
      // 如果目标价为空，使用当前股价
      const finalTargetPrice = targetForm.targetPrice || targetForm.currentPrice?.toString() || '';
      
      const data = {
        sector_name: targetForm.sectorName,
        stock_name: targetForm.stockName,
        target_price: finalTargetPrice ? parseFloat(finalTargetPrice) : null,
        change_up_pct: targetForm.changeUpPct ? parseFloat(targetForm.changeUpPct) : null,
        change_down_pct: targetForm.changeDownPct ? parseFloat(targetForm.changeDownPct) : null,
        notes: targetForm.notes || null,
      };
      
      console.log('📤 发送目标价数据:', data);
      return holdingsApi.updateStockTarget(data);
    },
    onSuccess: () => {
      console.log('✅ 目标价保存成功');
      queryClient.invalidateQueries({ queryKey: ['initial-data'] });
      queryClient.invalidateQueries({ queryKey: ['holdings'] });
      setShowTargetDialog(false);
      setTargetForm({ 
        sectorName: '', 
        stockName: '', 
        stockCode: '', 
        currentPrice: 0,
        targetPrice: '', 
        changeUpPct: '', 
        changeDownPct: '',
        notes: ''
      });
      alert('目标价设置成功！');
    },
    onError: (error: any) => {
      console.error('❌ 目标价保存失败:', error);
      const errorMsg = error?.message || error?.detail || '保存失败，请重试';
      alert(`保存失败: ${errorMsg}`);
    },
  });

  // 删除基准价的mutation
  const deleteTargetMutation = useMutation({
    mutationFn: () => {
      const data = {
        sector_name: targetForm.sectorName,
        stock_name: targetForm.stockName,
        target_price: null,
        change_up_pct: null,
        change_down_pct: null,
      };
      return holdingsApi.updateStockTarget(data);
    },
    onSuccess: () => {
      console.log('✅ 基准价删除成功');
      queryClient.invalidateQueries({ queryKey: ['initial-data'] });
      queryClient.invalidateQueries({ queryKey: ['holdings'] });
      setShowTargetDialog(false);
      setTargetForm({ 
        sectorName: '', 
        stockName: '', 
        stockCode: '', 
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

  const getStockQuote = (code: string) => {
    return allStocks.find(s => s.code === code);
  };

  // 实时计算控制区间
  const controlRange = useMemo(() => {
    const targetPrice = parseFloat(targetForm.targetPrice) || targetForm.currentPrice;
    const changeUpPct = parseFloat(targetForm.changeUpPct) || 0;
    const changeDownPct = parseFloat(targetForm.changeDownPct) || 0;
    
    if (!targetPrice) return null;
    if (changeUpPct === 0 && changeDownPct === 0) return null;
    
    return {
      upper: targetPrice * (1 + changeUpPct / 100),
      lower: targetPrice * (1 - changeDownPct / 100),
      targetPrice
    };
  }, [targetForm.targetPrice, targetForm.changeUpPct, targetForm.changeDownPct, targetForm.currentPrice]);

  // 判断当前价格状态
  const priceStatus = useMemo(() => {
    if (!controlRange || !targetForm.currentPrice) return null;
    if (targetForm.currentPrice > controlRange.upper) return 'above_upper';
    if (targetForm.currentPrice < controlRange.lower) return 'below_lower';
    return 'in_range';
  }, [controlRange, targetForm.currentPrice]);

  const openTargetDialog = (stock: Stock, sectorName: string) => {
    const quote = getStockQuote(stock.code);
    const currentPrice = stock.current_price || stock.price || quote?.price || 0;
    
    setTargetForm({
      sectorName,
      stockName: stock.name,
      stockCode: stock.code,
      currentPrice,
      targetPrice: stock.target_price?.toString() || '',
      changeUpPct: stock.change_up_pct?.toString() || '',
      changeDownPct: stock.change_down_pct?.toString() || '',
      notes: stock.notes || ''
    });
    setShowTargetDialog(true);
  };

  return (
    <div className={`h-full flex flex-col ${
      isDark 
        ? 'bg-[#1a1a1a]' 
        : 'bg-white'
    }`}>
      <HoldingsPanelHeader
        count={allStocks.length}
        isDark={isDark}
        collapsed={collapsed}
        onToggleCollapse={onToggleCollapse}
        actions={<div className="flex gap-1">
          <button 
            onClick={() => setShowSecondLine(!showSecondLine)}
            className={`p-1 transition-colors ${
              isDark 
                ? 'hover:bg-purple-900/30 text-gray-500 hover:text-purple-400' 
                : 'hover:bg-purple-50 text-gray-400 hover:text-purple-500'
            } ${showSecondLine ? (isDark ? 'text-purple-400' : 'text-purple-500') : ''}`}
            title={showSecondLine ? "隐藏目标价信息" : "显示目标价信息"}
          >
            {showSecondLine ? <Eye size={16} /> : <EyeOff size={16} />}
          </button>
          <button 
            onClick={() => refreshMutation.mutate()}
            disabled={refreshMutation.isPending}
            className={`p-1 transition-colors ${
              isDark 
                ? 'hover:bg-green-900/30 text-gray-500 hover:text-green-400' 
                : 'hover:bg-green-50 text-gray-400 hover:text-green-500'
            }`}
            title="手动刷新"
          >
            <RefreshCw size={16} className={refreshMutation.isPending ? 'animate-spin' : ''} />
          </button>
          <button 
            onClick={() => setShowAddDialog(true)}
            className={`p-1 transition-colors ${
              isDark 
                ? 'hover:bg-blue-900/30 text-gray-500 hover:text-blue-400' 
                : 'hover:bg-blue-50 text-gray-400 hover:text-blue-500'
            }`}
            title="快速添加"
          >
            <Plus size={16} />
          </button>
        </div>}
      />

      {/* 自持列表 */}
      {!collapsed && (
        <div className="flex-1 overflow-y-auto pr-2 [scrollbar-gutter:stable]">
        {holdings?.sectors?.map((sector: Sector) => (
          <div key={sector.name} className={`border-b last:border-0 ${
            isDark ? 'border-[#2a2a2a]' : 'border-gray-100'
          }`}>
            {/* 板块头部 */}
            <div 
              className={`flex items-center justify-between px-3 py-2 cursor-pointer transition-colors ${
                isDark ? 'hover:bg-[#2a2a2a]' : 'hover:bg-gray-50'
              }`}
              onClick={() => setExpandedSector(expandedSector === sector.name ? null : sector.name)}
            >
              <div className="flex items-center gap-2">
                <span className={`text-xs font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>{sector.name}</span>
                <span className={`text-xs px-1 py-0.5 ${
                  isDark ? 'text-gray-500 bg-[#2a2a2a]' : 'text-gray-500 bg-gray-100'
                }`}>
                  {sector.stocks.length}
                </span>
              </div>
              <svg 
                className={`w-4 h-4 text-gray-500 transition-transform ${expandedSector === sector.name ? 'rotate-180' : ''}`} 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>

            {/* 股票列表 */}
            {(expandedSector === sector.name || expandedSector === null) && sector.stocks.map((stock: Stock, index: number) => {
              const quote = getStockQuote(stock.code);
              const isSelected = selectedStockCode === stock.code;
              const changePct = quote?.change_pct || 0;
              const isUp = changePct > 0;
              const isDown = changePct < 0;
              const hasQuote = typeof quote?.price === 'number' && typeof quote?.change_pct === 'number';
              const denominator = 1 + changePct / 100;
              const changeAmount = hasQuote && denominator !== 0 ? quote.price - quote.price / denominator : null;
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
                  key={stock.code === 'UNKNOWN' ? `UNKNOWN-${index}` : stock.code}
                  onClick={() => onSelectStock(stock.code)}
                  className={`px-3 py-2 cursor-pointer transition-all border-b last:border-0 ${
                    isSelected
                      ? isDark
                        ? 'bg-blue-900/20 border-[#2a2a2a] hover:bg-blue-900/30'
                        : 'bg-blue-50 border-gray-100 hover:bg-blue-100'
                      : isDark 
                        ? 'border-[#2a2a2a] hover:bg-[#2a2a2a]' 
                        : 'bg-white border-gray-100 hover:bg-gray-50'
                  }`}
                  style={!isSelected && isDark ? { backgroundColor: HOLDINGS_DARK_ITEM_BG } : undefined}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 min-w-0 flex-1">
                      <span className={`text-xs font-bold truncate ${
                        isSelected 
                          ? 'text-blue-500' 
                          : isDark ? 'text-gray-300' : 'text-gray-800'
                      }`}>
                        {stock.name}
                      </span>
                      <span className={`text-[10px] font-mono ${isDark ? 'text-[#ffff00]' : 'text-gray-400'}`}>{stock.code}</span>
                    </div>
                    <div className="flex items-center gap-2.5 flex-shrink-0">
                      <div className={`px-2 py-1 rounded-md ${
                        isSelected
                          ? isDark ? 'bg-blue-900/20' : 'bg-blue-50'
                          : isDark ? '' : 'bg-white'
                      }`} style={!isSelected && isDark ? { backgroundColor: HOLDINGS_DARK_ITEM_BG } : undefined}>
                        <div className={`text-sm font-mono font-bold text-right ${quoteValueClass}`}>
                          {hasQuote ? quote.price.toFixed(2) : '--'}
                        </div>
                        <div className={`flex items-center justify-end gap-1 text-[10px] font-semibold ${quoteToneClass}`}>
                          {isUp ? <TrendingUp size={11} /> : isDown ? <TrendingDown size={11} /> : <Minus size={11} />}
                          <span>{hasQuote ? `${isUp ? '+' : ''}${changePct.toFixed(2)}%` : '--'}</span>
                          <span className={isDark ? 'text-gray-500' : 'text-gray-400'}>/</span>
                          <span>{hasQuote ? changeAmountText : '--'}</span>
                        </div>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          openTargetDialog(stock, sector.name);
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
                    </div>
                  </div>
                  {/* 第二行：基准价信息 */}
                  {showSecondLine && (
                    <div className={`mt-1 text-[10px] ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                      {hasTarget ? (
                        <>
                          {(() => {
                            // 计算控制区间
                            const basePrice = stock.target_price!;
                            const upper = basePrice * (1 + (stock.change_up_pct || 0) / 100);
                            const lower = basePrice * (1 - (stock.change_down_pct || 0) / 100);
                            const currentPrice = quote?.price;
                            
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
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ))}
        </div>
      )}

      {/* 快速添加对话框 */}
      {showAddDialog && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50" onClick={() => setShowAddDialog(false)}>
          <div 
            className={`p-4 w-80 shadow-xl border ${
              isDark 
                ? 'bg-[#1a1a1a] border-[#2a2a2a]' 
                : 'bg-white border-gray-200'
            }`}
            onClick={e => e.stopPropagation()}
          >
            <h4 className={`font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>快速添加股票</h4>
            <div className="space-y-3">
              <div>
                <label className={`text-xs mb-1 block ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>板块名称</label>
                <select 
                  className={`w-full px-3 py-2 border text-sm focus:outline-none ${
                    isDark 
                      ? 'border-[#3a3a3a] bg-[#0a0a0a] text-white focus:border-blue-500' 
                      : 'border-gray-300 bg-white text-gray-900 focus:border-blue-500'
                  }`}
                  value={addForm.sectorName}
                  onChange={e => setAddForm({ ...addForm, sectorName: e.target.value })}
                >
                  <option value="">选择板块</option>
                  {holdings?.sectors?.map((s: Sector) => (
                    <option key={s.name} value={s.name}>{s.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className={`text-xs mb-1 block ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>股票名称</label>
                <input 
                  type="text"
                  className={`w-full px-3 py-2 border text-sm focus:outline-none ${
                    isDark 
                      ? 'border-[#3a3a3a] bg-[#0a0a0a] text-white focus:border-blue-500' 
                      : 'border-gray-300 bg-white text-gray-900 focus:border-blue-500'
                  }`}
                  placeholder="如：贵州茅台"
                  value={addForm.stockName}
                  onChange={e => setAddForm({ ...addForm, stockName: e.target.value })}
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
                  placeholder="如：600519"
                  value={addForm.stockCode}
                  onChange={e => setAddForm({ ...addForm, stockCode: e.target.value })}
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
                onClick={() => addStockMutation.mutate()}
                disabled={!addForm.sectorName || !addForm.stockName || addStockMutation.isPending}
                className="flex-1 px-3 py-2 bg-blue-600 text-white text-sm hover:bg-blue-700 disabled:opacity-50"
              >
                {addStockMutation.isPending ? '添加中...' : '添加'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 目标价设置对话框 */}
      {showTargetDialog && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50" onClick={() => setShowTargetDialog(false)}>
          <div 
            className={`p-4 w-96 shadow-xl border max-h-[90vh] overflow-y-auto ${
              isDark 
                ? 'bg-[#1a1a1a] border-[#2a2a2a]' 
                : 'bg-white border-gray-200'
            }`}
            onClick={e => e.stopPropagation()}
          >
            <h4 className={`font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              设置基准价 - {targetForm.stockName}
            </h4>
            
            {/* 当前股价显示 */}
            <div className={`mb-3 p-2 rounded ${isDark ? 'bg-[#2a2a2a]' : 'bg-gray-50'}`}>
              <div className="text-xs text-gray-500">当前股价</div>
              <div className={`text-lg font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                ¥{targetForm.currentPrice?.toFixed(2) || '--'}
              </div>
            </div>
            
            <div className="space-y-3">
              {/* 目标价格 */}
              <div>
                <label className={`text-xs mb-1 block ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  基准价格（基准价格）
                </label>
                <input 
                  type="number"
                  step="0.01"
                  className={`w-full px-3 py-2 border text-sm focus:outline-none ${
                    isDark 
                      ? 'border-[#3a3a3a] bg-[#0a0a0a] text-white focus:border-blue-500' 
                      : 'border-gray-300 bg-white text-gray-900 focus:border-blue-500'
                  }`}
                  placeholder={`默认: ${targetForm.currentPrice?.toFixed(2)}`}
                  value={targetForm.targetPrice}
                  onChange={e => setTargetForm({ ...targetForm, targetPrice: e.target.value })}
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
                    value={targetForm.changeUpPct}
                    onChange={e => setTargetForm({ ...targetForm, changeUpPct: e.target.value })}
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
                    value={targetForm.changeDownPct}
                    onChange={e => setTargetForm({ ...targetForm, changeDownPct: e.target.value })}
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
                        目标价 × (1 + {targetForm.changeUpPct}%)
                      </div>
                    </div>
                    
                    <div className={`p-2 rounded ${isDark ? 'bg-[#1a1a1a]' : 'bg-white'}`}>
                      <div className={isDark ? 'text-gray-400' : 'text-gray-500'}>下限</div>
                      <div className={`font-bold ${isDark ? 'text-green-400' : 'text-green-500'}`}>
                        ¥{controlRange.lower.toFixed(2)}
                      </div>
                      <div className={`text-[10px] ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                        目标价 × (1 - {targetForm.changeDownPct}%)
                      </div>
                    </div>
                  </div>
                  
                  {/* 当前价格状态 */}
                  {targetForm.currentPrice > 0 && (
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
                  value={targetForm.notes}
                  onChange={e => setTargetForm({ ...targetForm, notes: e.target.value })}
                />
              </div>
            </div>
            
            <div className="flex gap-3 mt-4 justify-center">
              <button
                onClick={() => setShowTargetDialog(false)}
                className={`min-w-[100px] px-4 py-2 border text-sm transition-colors ${
                  isDark
                    ? 'border-[#3a3a3a] text-gray-300 hover:bg-[#2a2a2a]'
                    : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                }`}
              >
                取消
              </button>
              <button
                onClick={() => updateTargetMutation.mutate()}
                disabled={updateTargetMutation.isPending}
                className="min-w-[100px] px-4 py-2 bg-blue-600 text-white text-sm hover:bg-blue-700 disabled:opacity-50"
              >
                {updateTargetMutation.isPending ? '保存中...' : '保存'}
              </button>
              <button
                onClick={() => {
                  if (confirm('确定要删除该股票的基准价设置吗？')) {
                    deleteTargetMutation.mutate();
                  }
                }}
                disabled={deleteTargetMutation.isPending}
                className={`min-w-[100px] px-4 py-2 border text-sm transition-colors flex items-center justify-center gap-1 ${
                  isDark
                    ? 'border-red-800 text-red-400 hover:bg-red-900/30'
                    : 'border-red-300 text-red-600 hover:bg-red-50'
                } disabled:opacity-50`}
              >
                <Trash2 className="w-3 h-3" />
                {deleteTargetMutation.isPending ? '删除中...' : '删除'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
