import { useTheme } from '../contexts/ThemeContext';
import KLineChart from './KLineChart';
import { BarChart2 } from 'lucide-react';

interface KLineChartPanelProps {
  loading: boolean;
  data: any[] | undefined;
  stockCode: string;
  stockName: string;
  trendMode?: boolean;
  compactLineMode?: boolean;
  goToLatestTrigger?: number;
}

export default function KLineChartPanel({ 
  loading, 
  data, 
  stockCode, 
  stockName,
  trendMode = false,
  compactLineMode = false,
  goToLatestTrigger = 0
}: KLineChartPanelProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  if (loading) {
    return (
      <div className="absolute inset-0 flex items-center justify-center" style={{ height: '100%' }}>
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-3 border-blue-500 border-t-transparent animate-spin"></div>
          <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>加载K线数据...</p>
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className={`absolute inset-0 flex flex-col items-center justify-center ${isDark ? 'text-gray-500' : 'text-gray-400'}`}
           style={{ height: '100%' }}>
        <BarChart2 size={32} className={`mb-2 ${isDark ? 'text-gray-600' : 'text-gray-300'}`} />
        <p className="text-sm">暂无K线数据</p>
        <p className={`text-xs mt-1 ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>请选择一只股票查看详情</p>
      </div>
    );
  }

  return (
    <KLineChart 
      data={data} 
      stockCode={stockCode} 
      stockName={stockName} 
      trendMode={trendMode}
      compactLineMode={compactLineMode}
      goToLatestTrigger={goToLatestTrigger}
    />
  );
}
