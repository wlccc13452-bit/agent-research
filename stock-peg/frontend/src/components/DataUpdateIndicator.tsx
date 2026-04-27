/**
 * 数据更新指示器组件
 * 显示全局数据更新状态，提供强制更新功能
 */
import React, { useState, useEffect } from 'react';
import { Clock, CheckCircle, AlertTriangle } from 'lucide-react';
import { dataUpdateApi } from '../services/api';

interface DataUpdateIndicatorProps {
  className?: string;
}

interface UpdateStatus {
  needs_update_count: number;
  last_global_update: string | null;
  stocks: Array<{
    stock_code: string;
    needs_update: boolean;
    last_update: string | null;
    reason: string;
  }>;
  us_indices?: Array<{
    symbol: string;
    needs_update: boolean;
    last_update: string | null;
    reason: string;
  }>;
}

const DataUpdateIndicator: React.FC<DataUpdateIndicatorProps> = ({ className = '' }) => {
  const [updateStatus, setUpdateStatus] = useState<UpdateStatus | null>(null);
  const [showTooltip, setShowTooltip] = useState(false);
  const [timeSinceUpdate, setTimeSinceUpdate] = useState<string>('');
  const [retryCount, setRetryCount] = useState(0);
  const maxRetries = 3;

  // 获取更新状态
  const fetchUpdateStatus = async (): Promise<UpdateStatus | null> => {
    try {
      const status = await dataUpdateApi.getStatusAll();
      setUpdateStatus(status);
      updateTimeSinceUpdate(status.last_global_update);
      setRetryCount(0); // 成功后重置重试计数
      return status;
    } catch (error) {
      // 静默处理超时错误，只在多次失败后显示警告
      const errorMessage = error instanceof Error ? error.message : String(error);
      const isTimeout = errorMessage.includes('超时') || errorMessage.includes('timeout');
      
      if (isTimeout && retryCount < maxRetries) {
        if (retryCount === 0) {
          console.log(`📡 数据状态获取超时，将在下次轮询重试 (${retryCount + 1}/${maxRetries})`);
        }
        setRetryCount(prev => prev + 1);
      } else if (!isTimeout || retryCount >= maxRetries) {
        console.warn('获取更新状态失败:', error);
      }
      return null;
    }
  };

  // 计算距离上次更新的时间
  const updateTimeSinceUpdate = (lastUpdate: string | null) => {
    if (!lastUpdate) {
      setTimeSinceUpdate('从未更新');
      return;
    }

    const now = new Date();
    const lastUpdateTime = new Date(lastUpdate);
    const diffMs = now.getTime() - lastUpdateTime.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) {
      setTimeSinceUpdate('刚刚');
    } else if (diffMins < 60) {
      setTimeSinceUpdate(`${diffMins}分钟前`);
    } else if (diffHours < 24) {
      setTimeSinceUpdate(`${diffHours}小时前`);
    } else {
      setTimeSinceUpdate(`${diffDays}天前`);
    }
  };

  // 初始化和定时刷新
  useEffect(() => {
    fetchUpdateStatus();
    const interval = setInterval(fetchUpdateStatus, 60000); // 每分钟刷新
    return () => clearInterval(interval);
  }, []);

  // 更新时间显示
  useEffect(() => {
    if (updateStatus?.last_global_update) {
      const interval = setInterval(() => {
        updateTimeSinceUpdate(updateStatus.last_global_update);
      }, 60000); // 每分钟更新时间显示
      return () => clearInterval(interval);
    }
  }, [updateStatus?.last_global_update]);

  // 获取状态图标和颜色
  const getStatusIcon = () => {
    if (!updateStatus) {
      return <Clock className="w-4 h-4" style={{ color: 'var(--text-secondary)' }} />;
    }
    if (updateStatus.needs_update_count > 0) {
      return <AlertTriangle className="w-4 h-4" style={{ color: 'var(--warning-color)' }} />;
    }
    return <CheckCircle className="w-4 h-4" style={{ color: 'var(--success-color)' }} />;
  };

  const getStatusText = () => {
    if (!updateStatus) return '加载中...';
    if (updateStatus.needs_update_count > 0) return `${updateStatus.needs_update_count}项待同步`;
    return '本地数据最新';
  };

  const getStatusColor = () => {
    if (!updateStatus) return { color: 'var(--text-secondary)' };
    if (updateStatus.needs_update_count > 0) return { color: 'var(--warning-color)' };
    return { color: 'var(--success-color)' };
  };

  return (
    <div
      className={`relative flex items-center gap-2 px-2.5 py-1 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-all ${className}`}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      {getStatusIcon()}

      <div className="flex items-center gap-1.5 min-w-0">
        <span className="text-xs font-medium" style={getStatusColor()}>
          {getStatusText()}
        </span>
        <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
          {timeSinceUpdate}
        </span>
      </div>

      {showTooltip && updateStatus && (
        <div className="absolute top-full right-0 mt-2 w-80 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl z-50 p-4">
          <h3 className="text-sm font-semibold mb-3 text-gray-900 dark:text-white">
            数据更新状态
          </h3>
          
          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">最后更新:</span>
              <span className="text-gray-900 dark:text-white">{timeSinceUpdate}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">需更新:</span>
              <span style={{ color: updateStatus.needs_update_count > 0 ? 'var(--warning-color)' : 'var(--success-color)' }}>
                {updateStatus.needs_update_count} 项
              </span>
            </div>
          </div>
          
          {updateStatus.needs_update_count > 0 && (
            <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
              <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">需更新的项目:</p>
              <div className="max-h-32 overflow-y-auto space-y-1">
                {/* 股票更新列表 */}
                {updateStatus.stocks
                  .filter(s => s.needs_update)
                  .map((stock) => (
                    <div key={stock.stock_code} className="text-xs text-gray-700 dark:text-gray-300">
                      [股票] {stock.stock_code}: {stock.reason}
                    </div>
                  ))}
                
                {/* 美股指数更新列表 */}
                {(updateStatus.us_indices || [])
                  .filter(s => s.needs_update)
                  .map((index) => (
                    <div key={index.symbol} className="text-xs text-gray-700 dark:text-gray-300">
                      [美股指数] {index.symbol}: {index.reason}
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DataUpdateIndicator;
