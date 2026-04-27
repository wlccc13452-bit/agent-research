import { TrendingUp, TrendingDown, Activity } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

interface StockListProps {
  allStocks: any[];
  holdings?: any;
  selectedStockCode?: string;
  onSelectStock: (code: string) => void;
}

export default function StockList({ allStocks, holdings, selectedStockCode, onSelectStock }: StockListProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const hasHoldings = holdings?.sectors && Array.isArray(holdings.sectors) && holdings.sectors.length > 0;
  const hasStocks = Array.isArray(allStocks) && allStocks.length > 0;

  if (!hasHoldings) {
    return (
      <div className={`shadow-sm border flex flex-col h-full ${
        isDark ? 'bg-[#1a1a1a] border-[#2a2a2a]' : 'bg-white border-gray-100'
      }`}>
        <div className={`p-4 border-b ${isDark ? 'border-[#2a2a2a] bg-[#1a1a1a]' : 'border-gray-50 bg-gray-50/50'}`}>
          <h3 className={`text-sm font-semibold flex items-center gap-2 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
            <Activity size={16} className="text-blue-500" />
            持仓股票
          </h3>
        </div>
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="text-center">
            <div className={`w-12 h-12 flex items-center justify-center mx-auto mb-3 ${
              isDark ? 'bg-blue-900/30 text-blue-400' : 'bg-blue-50 text-blue-500'
            }`}>
              <Activity size={24} />
            </div>
            <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>暂无持仓数据，请在左侧面板添加自持股票</p>
          </div>
        </div>
      </div>
    );
  }

  if (!hasStocks) {
    return (
      <div className={`shadow-sm border flex flex-col h-full ${
        isDark ? 'bg-[#1a1a1a] border-[#2a2a2a]' : 'bg-white border-gray-100'
      }`}>
        <div className={`p-4 border-b ${isDark ? 'border-[#2a2a2a] bg-[#1a1a1a]' : 'border-gray-50 bg-gray-50/50'}`}>
          <h3 className={`text-sm font-semibold flex items-center gap-2 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
            <Activity size={16} className="text-blue-500" />
            自持股票
          </h3>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <div className="w-8 h-8 border-3 border-blue-500 border-t-transparent animate-spin"></div>
            <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>加载行情数据...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`shadow-sm border flex flex-col h-full overflow-hidden ${
      isDark ? 'bg-[#1a1a1a] border-[#2a2a2a]' : 'bg-white border-gray-100'
    }`}>
      <div className={`p-4 border-b ${isDark ? 'border-[#2a2a2a] bg-[#1a1a1a]' : 'border-gray-50 bg-gray-50/50'}`}>
        <h3 className={`text-sm font-semibold flex items-center gap-2 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          <Activity size={16} className="text-blue-500" />
          自持股票 ({allStocks.length})
        </h3>
      </div>
      
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {holdings.sectors.map((sector: any) => {
          if (!sector || !Array.isArray(sector.stocks)) return null;

          const sectorStocks = (allStocks || []).filter((s: any) => 
            s && s.code && sector.stocks.some((st: any) => st && st.code === s.code)
          );
          
          if (sectorStocks.length === 0) return null;

          return (
            <div key={sector.name} className="mb-2">
              <div className={`px-4 py-2 text-[10px] font-bold uppercase tracking-widest ${
                isDark ? 'bg-[#0a0a0a] text-gray-500' : 'bg-gray-50 text-gray-400'
              }`}>
                {sector.name}
              </div>
              <div className="space-y-px">
                {sectorStocks.map((stock: any) => {
                  const price = typeof stock.price === 'number' ? stock.price : 0;
                  const changePct = typeof stock.change_pct === 'number' ? stock.change_pct : 0;
                  const isUp = changePct > 0;
                  const isDown = changePct < 0;

                  return (
                    <button
                      key={stock.code}
                      onClick={() => onSelectStock(stock.code)}
                      className={`w-full px-4 py-3 flex items-center justify-between transition-colors ${
                        selectedStockCode === stock.code 
                          ? isDark 
                            ? 'bg-blue-900/30 border-r-2 border-blue-500' 
                            : 'bg-blue-50 border-r-2 border-blue-500'
                          : isDark 
                            ? 'hover:bg-[#2a2a2a]' 
                            : 'hover:bg-blue-50/50'
                      }`}
                    >
                      <div className="flex flex-col items-start min-w-0">
                        <span className={`text-sm font-bold truncate w-full ${isDark ? 'text-gray-200' : 'text-gray-900'}`}>{stock.name}</span>
                        <span className={`text-[10px] font-mono tracking-tighter uppercase ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{stock.code}</span>
                      </div>
                      <div className="text-right">
                        <div className={`text-sm font-mono font-bold ${isDark ? 'text-gray-200' : 'text-gray-900'}`}>
                          {price > 0 ? price.toFixed(2) : '--'}
                        </div>
                        <div className={`text-[10px] font-bold flex items-center justify-end gap-0.5 ${
                          isUp ? 'text-red-500' : isDown ? 'text-green-500' : isDark ? 'text-gray-500' : 'text-gray-400'
                        }`}>
                          {isUp ? <TrendingUp size={10} /> : isDown ? <TrendingDown size={10} /> : null}
                          {isUp ? '+' : ''}{changePct.toFixed(2)}%
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
