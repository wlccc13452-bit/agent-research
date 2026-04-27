import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { stocksApi } from '../services/api';
import { useTheme } from '../contexts/ThemeContext';
import IndicesPanelHeader from './IndicesPanelHeader';
import marketNewsThemeRaw from '../config/marketNewsTheme.json?raw';

interface IndicesStyleConfig {
  darkItemCardBg?: string;
}

const parsedIndicesStyleConfig = (() => {
  try {
    return JSON.parse(marketNewsThemeRaw) as IndicesStyleConfig;
  } catch {
    return {};
  }
})();

const INDICES_DARK_ITEM_BG = parsedIndicesStyleConfig.darkItemCardBg ?? '#111827';

interface Index {
  code: string;
  name: string;
  market: string;
  full_code: string;
  description: string;
  price?: number;
  change?: number;
  change_pct?: number;
  volume?: number;
  amount?: number;
}

interface IndicesPanelProps {
  selectedIndexCode?: string;
  onSelectIndex: (code: string) => void;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

export default function IndicesPanel({ 
  selectedIndexCode, 
  onSelectIndex,
  collapsed = false,
  onToggleCollapse,
}: IndicesPanelProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  
  // 获取指数列表和行情
  const { data: indicesData, isLoading } = useQuery({
    queryKey: ['indices-quotes'],
    queryFn: stocksApi.getIndicesQuotes,
    refetchInterval: 30000, // 30秒刷新一次
  });
  
  const indices = indicesData?.indices || [];
  
  return (
    <div className={`h-full flex flex-col ${
      isDark 
        ? 'bg-[#1a1a1a]' 
        : 'bg-white'
    }`}>
      <IndicesPanelHeader
        count={indices.length}
        isDark={isDark}
        collapsed={collapsed}
        onToggleCollapse={onToggleCollapse}
      />
      
      {/* 指数列表 */}
      {!collapsed && (
        <div className="flex-1 overflow-y-auto pr-2 [scrollbar-gutter:stable]">
        {isLoading ? (
          <div className={`p-4 text-center text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
            加载中...
          </div>
        ) : indices.length === 0 ? (
          <div className={`p-4 text-center text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
            暂无指数数据
          </div>
        ) : (
          indices.map((index: Index) => {
            const selectedCode = index.full_code || index.code;
            const isSelected = selectedIndexCode === index.code || selectedIndexCode === index.full_code;
            const changePct = index.change_pct || 0;
            const isUp = changePct > 0;
            const isDown = changePct < 0;
            
            return (
              <div
                key={index.code}
                onClick={() => onSelectIndex(selectedCode)}
                className={`px-3 py-2 cursor-pointer transition-all border-b ${
                  isSelected 
                    ? isDark 
                      ? 'bg-blue-900/20 border-[#2a2a2a] hover:bg-blue-900/30' 
                      : 'bg-blue-50 border-gray-100 hover:bg-blue-100'
                    : isDark 
                      ? 'border-[#2a2a2a] hover:bg-[#2a2a2a]' 
                      : 'bg-white border-gray-100 hover:bg-gray-50'
                }`}
                style={!isSelected && isDark ? { backgroundColor: INDICES_DARK_ITEM_BG } : undefined}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 min-w-0 flex-1">
                    <span className={`text-xs font-bold truncate ${
                      isSelected 
                        ? 'text-blue-500' 
                        : isDark ? 'text-gray-300' : 'text-gray-800'
                    }`}>
                      {index.name}
                    </span>
                    <span className={`text-[10px] font-mono ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>
                      {index.code}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <span className={`text-sm font-mono font-bold ${
                      isUp ? 'text-red-500' : isDown ? 'text-green-500' : isDark ? 'text-gray-500' : 'text-gray-500'
                    }`}>
                      {index.price?.toFixed(2) || '--'}
                    </span>
                    <div className={`flex items-center gap-0.5 text-xs font-medium ${
                      isUp ? 'text-red-500' : isDown ? 'text-green-500' : isDark ? 'text-gray-600' : 'text-gray-400'
                    }`}>
                      {isUp ? <TrendingUp size={12} /> : isDown ? <TrendingDown size={12} /> : <Minus size={12} />}
                      <span>{isUp ? '+' : ''}{changePct.toFixed(2)}%</span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
        </div>
      )}
    </div>
  );
}
