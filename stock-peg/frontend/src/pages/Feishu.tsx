import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useFeishu } from '../hooks/useFeishu';
import { stocksApi } from '../services/api';
import { Search, X, ExternalLink, Smartphone, Monitor } from 'lucide-react';

interface StockQuote {
  code: string;
  name: string;
  price: number;
  change: number;
  change_pct: number;
  volume: number;
  amount: number;
  high: number;
  low: number;
  open: number;
  prev_close: number;
}

export default function Feishu() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { isFeishuEnv, isSDKReady, closeWindow, isLoading: sdkLoading } = useFeishu();
  
  const [searchInput, setSearchInput] = useState('');
  const [selectedStock, setSelectedStock] = useState<StockQuote | null>(null);
  const [searchHistory, setSearchHistory] = useState<string[]>([]);
  
  // 从 URL 参数获取股票代码
  useEffect(() => {
    const stockCode = searchParams.get('code');
    if (stockCode) {
      setSearchInput(stockCode);
      handleSearch(stockCode);
    }
  }, [searchParams]);
  
  // 加载搜索历史
  useEffect(() => {
    const history = localStorage.getItem('feishu_search_history');
    if (history) {
      setSearchHistory(JSON.parse(history));
    }
  }, []);
  
  // 保存搜索历史
  const saveSearchHistory = (keyword: string) => {
    const newHistory = [keyword, ...searchHistory.filter(h => h !== keyword)].slice(0, 10);
    setSearchHistory(newHistory);
    localStorage.setItem('feishu_search_history', JSON.stringify(newHistory));
  };
  
  // 搜索股票
  const { refetch: searchStock, isLoading: isSearching } = useQuery({
    queryKey: ['search-stock', searchInput],
    queryFn: async () => {
      if (!searchInput.trim()) return null;

      const quote = await stocksApi.getQuote(searchInput);
      return quote as StockQuote;
    },
    enabled: false,
  });
  
  const handleSearch = async (keyword?: string) => {
    const searchKeyword = keyword || searchInput;
    if (!searchKeyword.trim()) return;
    
    setSearchInput(searchKeyword);
    saveSearchHistory(searchKeyword);
    
    const result = await searchStock();
    if (result.data) {
      setSelectedStock(result.data);
    }
  };
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };
  
  // 格式化数字
  const formatNumber = (num: number, decimals: number = 2) => {
    if (num === null || num === undefined) return '-';
    return num.toFixed(decimals);
  };
  
  const formatVolume = (vol: number) => {
    if (vol >= 100000000) return `${(vol / 100000000).toFixed(2)}亿`;
    if (vol >= 10000) return `${(vol / 10000).toFixed(2)}万`;
    return vol.toString();
  };
  
  // 跳转到详细页面
  const handleViewDetail = () => {
    if (selectedStock) {
      navigate(`/stock/${selectedStock.code}`);
    }
  };
  
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* 顶部栏 */}
      <div className="bg-blue-600 text-white p-4 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-between mb-3">
            <h1 className="text-xl font-bold flex items-center gap-2">
              📊 股票查询
            </h1>
            <div className="flex items-center gap-2">
              {isFeishuEnv ? (
                <span className="flex items-center gap-1 text-xs bg-blue-500 px-2 py-1 rounded">
                  <Smartphone className="w-3 h-3" />
                  飞书环境
                </span>
              ) : (
                <span className="flex items-center gap-1 text-xs bg-gray-500 px-2 py-1 rounded">
                  <Monitor className="w-3 h-3" />
                  浏览器
                </span>
              )}
            </div>
          </div>
          
          {/* 搜索框 */}
          <div className="relative">
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="输入股票代码或名称，如 600519 或 贵州茅台"
              className="w-full px-4 py-3 pr-24 rounded-lg text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-300"
            />
            <div className="absolute right-2 top-1/2 -translate-y-1/2 flex gap-2">
              {searchInput && (
                <button
                  onClick={() => {
                    setSearchInput('');
                    setSelectedStock(null);
                  }}
                  className="p-2 text-gray-500 hover:text-gray-700"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
              <button
                onClick={() => handleSearch()}
                disabled={isSearching}
                className="px-4 py-1 bg-blue-700 text-white rounded hover:bg-blue-800 disabled:bg-blue-400 flex items-center gap-1"
              >
                <Search className="w-4 h-4" />
                搜索
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <div className="max-w-4xl mx-auto p-4">
        {/* 搜索历史 */}
        {searchHistory.length > 0 && !selectedStock && (
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 mb-4 shadow-sm">
            <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-300 mb-2">
              搜索历史
            </h3>
            <div className="flex flex-wrap gap-2">
              {searchHistory.slice(0, 5).map((item) => (
                <button
                  key={item}
                  onClick={() => handleSearch(item)}
                  className="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full text-sm hover:bg-gray-200 dark:hover:bg-gray-600"
                >
                  {item}
                </button>
              ))}
            </div>
          </div>
        )}
        
        {/* 搜索结果 */}
        {selectedStock && (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden">
            {/* 股票基本信息 */}
            <div className="p-4 border-b dark:border-gray-700">
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                    {selectedStock.name}
                  </h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {selectedStock.code}
                  </p>
                </div>
                <button
                  onClick={handleViewDetail}
                  className="flex items-center gap-1 px-3 py-1 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded"
                >
                  <ExternalLink className="w-4 h-4" />
                  详细页面
                </button>
              </div>
            </div>
            
            {/* 价格信息 */}
            <div className="p-4 bg-gradient-to-r from-gray-50 to-white dark:from-gray-800 dark:to-gray-750">
              <div className="flex items-baseline gap-2 mb-3">
                <span className="text-4xl font-bold text-gray-900 dark:text-white">
                  {formatNumber(selectedStock.price)}
                </span>
                <span className={`text-lg font-semibold ${
                  selectedStock.change >= 0 ? 'text-red-600' : 'text-green-600'
                }`}>
                  {selectedStock.change >= 0 ? '+' : ''}{formatNumber(selectedStock.change)}
                </span>
                <span className={`text-sm px-2 py-1 rounded ${
                  selectedStock.change >= 0 
                    ? 'bg-red-100 text-red-600 dark:bg-red-900/20' 
                    : 'bg-green-100 text-green-600 dark:bg-green-900/20'
                }`}>
                  {selectedStock.change >= 0 ? '↑' : '↓'} 
                  {selectedStock.change_pct >= 0 ? '+' : ''}{formatNumber(selectedStock.change_pct)}%
                </span>
              </div>
              
              {/* 详细数据 */}
              <div className="grid grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-500 dark:text-gray-400">今开</span>
                  <p className="font-semibold text-gray-900 dark:text-white">
                    {formatNumber(selectedStock.open)}
                  </p>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">最高</span>
                  <p className="font-semibold text-red-600">
                    {formatNumber(selectedStock.high)}
                  </p>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">最低</span>
                  <p className="font-semibold text-green-600">
                    {formatNumber(selectedStock.low)}
                  </p>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">昨收</span>
                  <p className="font-semibold text-gray-900 dark:text-white">
                    {formatNumber(selectedStock.prev_close)}
                  </p>
                </div>
              </div>
            </div>
            
            {/* 成交信息 */}
            <div className="p-4 grid grid-cols-2 gap-4 bg-gray-50 dark:bg-gray-800/50">
              <div>
                <span className="text-sm text-gray-500 dark:text-gray-400">成交量</span>
                <p className="font-semibold text-gray-900 dark:text-white">
                  {formatVolume(selectedStock.volume)}手
                </p>
              </div>
              <div>
                <span className="text-sm text-gray-500 dark:text-gray-400">成交额</span>
                <p className="font-semibold text-gray-900 dark:text-white">
                  {formatVolume(selectedStock.amount)}元
                </p>
              </div>
            </div>
          </div>
        )}
        
        {/* 空状态 */}
        {!selectedStock && !isSearching && (
          <div className="bg-white dark:bg-gray-800 rounded-lg p-12 text-center">
            <div className="text-6xl mb-4">📈</div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              开始查询股票
            </h3>
            <p className="text-gray-500 dark:text-gray-400">
              输入股票代码或名称，查看实时行情
            </p>
          </div>
        )}
        
        {/* 加载状态 */}
        {isSearching && (
          <div className="bg-white dark:bg-gray-800 rounded-lg p-12 text-center">
            <div className="animate-spin text-4xl mb-4">⏳</div>
            <p className="text-gray-500 dark:text-gray-400">正在查询...</p>
          </div>
        )}
        
        {/* 飞书 SDK 状态（调试用） */}
        {isFeishuEnv && (
          <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded text-xs text-gray-600 dark:text-gray-400">
            <p>SDK 状态: {sdkLoading ? '加载中...' : isSDKReady ? '✅ 就绪' : '❌ 未就绪'}</p>
          </div>
        )}
      </div>
      
      {/* 底部操作栏 */}
      {isFeishuEnv && (
        <div className="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t dark:border-gray-700 p-4">
          <div className="max-w-4xl mx-auto flex gap-2">
            <button
              onClick={handleViewDetail}
              disabled={!selectedStock}
              className="flex-1 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <ExternalLink className="w-4 h-4" />
              查看详细分析
            </button>
            <button
              onClick={closeWindow}
              className="px-6 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600"
            >
              关闭
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
