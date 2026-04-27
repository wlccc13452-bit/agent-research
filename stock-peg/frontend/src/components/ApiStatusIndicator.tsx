import { useQuery } from '@tanstack/react-query';
import { statusApi } from '../services/api';
import { Wifi, WifiOff, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useState } from 'react';

interface ApiStatus {
  status: 'ok' | 'error' | 'degraded' | 'not_configured' | 'timeout';
  message: string;
}

interface StatusData {
  tushare: ApiStatus;
  alphavantage: ApiStatus;
  finnhub: ApiStatus;
  tencent: ApiStatus;
  timestamp: string;
}

export default function ApiStatusIndicator() {
  const [showDetails, setShowDetails] = useState(false);

  const { data: status, isLoading } = useQuery({
    queryKey: ['api-status'],
    queryFn: statusApi.getApiStatus,
    refetchInterval: 60000, // 每分钟刷新一次
  });

  // 状态颜色 - 使用CSS变量
  const colors = {
    ok: 'var(--success-color)',
    error: 'var(--danger-color)',
    timeout: 'var(--danger-color)',
    degraded: 'var(--warning-color)',
    not_configured: 'var(--text-muted)',
    unknown: 'var(--text-muted)',
  };

  if (isLoading || !status) {
    return (
      <div 
        className="flex items-center gap-2 px-3 py-1.5"
        style={{ backgroundColor: 'var(--bg-hover)' }}
      >
        <div 
          className="w-2 h-2 animate-pulse"
          style={{ backgroundColor: 'var(--text-muted)' }}
        ></div>
        <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>检查中...</span>
      </div>
    );
  }

  const statusData = status as StatusData;

  // 计算总体状态
  const getOverallStatus = () => {
    const apis = [statusData.tencent, statusData.tushare];
    const hasOk = apis.some(api => api.status === 'ok');
    const hasError = apis.some(api => api.status === 'error' || api.status === 'timeout');
    
    if (hasError && !hasOk) return 'error';
    if (hasOk) return 'ok';
    return 'degraded';
  };

  const overallStatus = getOverallStatus();

  const getStatusColor = (apiStatus: string): string => {
    return colors[apiStatus as keyof typeof colors] || colors.unknown;
  };

  const getStatusIcon = (apiStatus: string) => {
    const color = getStatusColor(apiStatus);
    switch (apiStatus) {
      case 'ok':
        return <CheckCircle2 size={12} style={{ color }} />;
      case 'error':
      case 'timeout':
        return <WifiOff size={12} style={{ color }} />;
      case 'degraded':
        return <AlertCircle size={12} style={{ color }} />;
      default:
        return <Wifi size={12} style={{ color }} />;
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setShowDetails(!showDetails)}
        className="flex items-center gap-2 px-3 py-1.5 transition-colors"
        style={{ 
          backgroundColor: 'var(--bg-hover)',
          color: 'var(--text-primary)'
        }}
        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--border-color)'}
        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'var(--bg-hover)'}
      >
        {overallStatus === 'ok' ? (
          <Wifi size={14} style={{ color: colors.ok }} />
        ) : overallStatus === 'error' ? (
          <WifiOff size={14} style={{ color: colors.error }} />
        ) : (
          <AlertCircle size={14} style={{ color: colors.degraded }} />
        )}
        <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
          {overallStatus === 'ok' ? 'API正常' : overallStatus === 'error' ? 'API异常' : '部分可用'}
        </span>
      </button>

      {showDetails && (
        <div 
          className="absolute top-full right-0 mt-2 w-72 shadow-xl z-50"
          style={{ 
            backgroundColor: 'var(--bg-card)',
            border: '1px solid var(--border-color)'
          }}
        >
          <div 
            className="p-3"
            style={{ borderBottom: '1px solid var(--border-color)' }}
          >
            <h3 className="text-sm font-bold" style={{ color: 'var(--text-primary)' }}>数据源状态</h3>
            <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
              最近更新: {new Date(statusData.timestamp).toLocaleTimeString()}
            </p>
          </div>
          
          <div className="p-2 space-y-1">
            {/* 腾讯API */}
            <div 
              className="flex items-center justify-between p-2"
              style={{ backgroundColor: 'var(--bg-dark)' }}
            >
              <div className="flex items-center gap-2">
                {getStatusIcon(statusData.tencent.status)}
                <div>
                  <div className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>腾讯行情</div>
                  <div className="text-xs" style={{ color: 'var(--text-muted)' }}>{statusData.tencent.message}</div>
                </div>
              </div>
              <div className="w-2 h-2" style={{ backgroundColor: getStatusColor(statusData.tencent.status) }}></div>
            </div>

            {/* Tushare */}
            <div 
              className="flex items-center justify-between p-2"
              style={{ backgroundColor: 'var(--bg-dark)' }}
            >
              <div className="flex items-center gap-2">
                {getStatusIcon(statusData.tushare.status)}
                <div>
                  <div className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>Tushare</div>
                  <div className="text-xs" style={{ color: 'var(--text-muted)' }}>{statusData.tushare.message}</div>
                </div>
              </div>
              <div className="w-2 h-2" style={{ backgroundColor: getStatusColor(statusData.tushare.status) }}></div>
            </div>

            {/* Alpha Vantage */}
            <div 
              className="flex items-center justify-between p-2"
              style={{ backgroundColor: 'var(--bg-dark)' }}
            >
              <div className="flex items-center gap-2">
                {getStatusIcon(statusData.alphavantage.status)}
                <div>
                  <div className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>Alpha Vantage</div>
                  <div className="text-xs" style={{ color: 'var(--text-muted)' }}>{statusData.alphavantage.message}</div>
                </div>
              </div>
              <div className="w-2 h-2" style={{ backgroundColor: getStatusColor(statusData.alphavantage.status) }}></div>
            </div>

            {/* Finnhub */}
            <div 
              className="flex items-center justify-between p-2"
              style={{ backgroundColor: 'var(--bg-dark)' }}
            >
              <div className="flex items-center gap-2">
                {getStatusIcon(statusData.finnhub.status)}
                <div>
                  <div className="text-xs font-medium" style={{ color: 'var(--text-primary)' }}>Finnhub</div>
                  <div className="text-xs" style={{ color: 'var(--text-muted)' }}>{statusData.finnhub.message}</div>
                </div>
              </div>
              <div className="w-2 h-2" style={{ backgroundColor: getStatusColor(statusData.finnhub.status) }}></div>
            </div>
          </div>

          <div 
            className="p-2"
            style={{ borderTop: '1px solid var(--border-color)' }}
          >
            <div className="flex items-center gap-2 text-xs" style={{ color: 'var(--text-muted)' }}>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2" style={{ backgroundColor: colors.ok }}></div>
                <span>正常</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2" style={{ backgroundColor: colors.degraded }}></div>
                <span>降级</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2" style={{ backgroundColor: colors.error }}></div>
                <span>异常</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2" style={{ backgroundColor: colors.not_configured }}></div>
                <span>未配置</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
