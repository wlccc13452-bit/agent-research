import { useTheme } from '../contexts/ThemeContext';
import IntradayChart from './IntradayChart';
import { LineChart } from 'lucide-react';

interface IntradayChartPanelProps {
  loading: boolean;
  data: any[] | undefined;
  stockCode: string;
  stockName: string;
  avgPrice?: number;
  preClose?: number;
}

export default function IntradayChartPanel({ 
  loading, 
  data, 
  stockCode, 
  stockName,
  avgPrice,
  preClose
}: IntradayChartPanelProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  if (loading) {
    return (
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-3 border-blue-500 border-t-transparent animate-spin"></div>
          <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>加载分时数据...</p>
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className={`absolute inset-0 flex flex-col items-center justify-center ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
        <LineChart size={32} className={`mb-2 ${isDark ? 'text-gray-600' : 'text-gray-300'}`} />
        <p className="text-sm">暂无分时数据</p>
        <p className={`text-xs mt-1 ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>请选择一只股票查看详情</p>
      </div>
    );
  }

  return (
    <IntradayChart 
      data={data}
      stockCode={stockCode} 
      stockName={stockName}
      avgPrice={avgPrice ?? 0}
      preClose={preClose ?? 0}
    />
  );
}
