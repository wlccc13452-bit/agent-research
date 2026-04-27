import { useQuery } from '@tanstack/react-query';
import { Database, Clock, RefreshCw, AlertCircle, CheckCircle, X, Info } from 'lucide-react';
import { stocksApi } from '../services/api';

interface DataStatusItem {
  data_type: string;
  data_type_name: string;
  stock_code: string | null;
  read_time: string | null;
  last_update_time: string | null;
  source_location: string | null;
  is_updating: boolean;
}

interface DataSourceStatusProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function DataSourceStatus({ isOpen, onClose }: DataSourceStatusProps) {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['data-source-status'],
    queryFn: stocksApi.getDataSourceStatus,
    enabled: isOpen,
    refetchInterval: 5000, // 每5秒刷新一次
  });

  if (!isOpen) return null;

  const status = data?.status || {};

  const getStatusIcon = (isUpdating: boolean) => {
    if (isUpdating) return <RefreshCw size={16} className="text-orange-500" />;
    return <Database size={16} className="text-blue-500" />;
  };

  const getUpdatingIcon = (isUpdating: boolean) => {
    if (isUpdating) {
      return <RefreshCw size={14} className="text-orange-500 animate-spin" />;
    }
    return <CheckCircle size={14} className="text-green-500" />;
  };

  const formatTime = (time: string | null) => {
    if (!time) return '未知';
    try {
      const date = new Date(time);
      return date.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return time;
    }
  };

  const statusArray = Object.values(status) as DataStatusItem[];

  return (
    <>
      {/* 背景遮罩 */}
      <div 
        className="fixed inset-0 z-50 bg-black/50"
        onClick={onClose}
      />
      
      {/* 弹出框 */}
      <div 
        className="fixed z-50 bg-white dark:bg-gray-800 rounded-lg shadow-2xl"
        style={{
          top: '60px',
          right: '20px',
          width: '450px',
          maxHeight: '70vh',
          overflow: 'hidden',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* 标题栏 */}
        <div 
          className="flex items-center justify-between px-4 py-3 border-b"
          style={{ borderColor: 'var(--border-color)' }}
        >
          <div className="flex items-center gap-2">
            <Info size={18} style={{ color: 'var(--primary-color)' }} />
            <h3 className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>
              本地数据状态
            </h3>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => refetch()}
              className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
              title="刷新"
            >
              <RefreshCw size={14} style={{ color: 'var(--text-secondary)' }} />
            </button>
            <button
              onClick={onClose}
              className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
            >
              <X size={14} style={{ color: 'var(--text-secondary)' }} />
            </button>
          </div>
        </div>

        {/* 内容区域 */}
        <div className="overflow-y-auto" style={{ maxHeight: 'calc(70vh - 50px)' }}>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <RefreshCw size={24} className="animate-spin text-blue-500" />
              <span className="ml-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
                加载中...
              </span>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center py-8 text-red-500">
              <AlertCircle size={20} />
              <span className="ml-2 text-sm">加载失败</span>
            </div>
          ) : (
            <div className="p-4 space-y-3">
              {statusArray.map((item) => (
                <div
                  key={item.data_type}
                  className="border rounded-lg p-3"
                  style={{ 
                    borderColor: 'var(--border-color)',
                    backgroundColor: 'var(--bg-hover)'
                  }}
                >
                  {/* 数据类型标题 */}
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(item.is_updating)}
                      <span className="font-medium text-sm" style={{ color: 'var(--text-primary)' }}>
                        {item.data_type_name}
                      </span>
                    </div>
                    <div className="flex items-center gap-1">
                      {getUpdatingIcon(item.is_updating)}
                      <span className="text-xs" style={{ color: 'var(--text-secondary)' }}>
                        {item.is_updating ? '更新中' : '已就绪'}
                      </span>
                    </div>
                  </div>

                  {/* 详细信息 */}
                  <div className="space-y-1 text-xs" style={{ color: 'var(--text-secondary)' }}>
                    {item.stock_code && (
                      <div className="flex items-center gap-2">
                        <span className="w-16">代码:</span>
                        <span className="font-mono">{item.stock_code}</span>
                      </div>
                    )}
                    <div className="flex items-center gap-2">
                      <span className="w-16">位置:</span>
                      <span>{item.source_location || '未知'}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="w-16">读取时间:</span>
                      <div className="flex items-center gap-1">
                        <Clock size={10} />
                        <span>{formatTime(item.read_time)}</span>
                      </div>
                    </div>
                    {item.last_update_time && (
                      <div className="flex items-center gap-2">
                        <span className="w-16">数据时间:</span>
                        <div className="flex items-center gap-1">
                          <Clock size={10} />
                          <span>{formatTime(item.last_update_time)}</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {statusArray.length === 0 && (
                <div className="text-center py-8 text-gray-500 text-sm">
                  暂无数据读取记录
                </div>
              )}
            </div>
          )}
        </div>

        {/* 底部说明 */}
        <div 
          className="px-4 py-2 border-t text-xs"
          style={{ 
            borderColor: 'var(--border-color)',
            color: 'var(--text-secondary)',
            backgroundColor: 'var(--bg-card)'
          }}
        >
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1">
              <Database size={12} className="text-blue-500" />
              <span>本地数据可用</span>
            </div>
            <div className="flex items-center gap-1">
              <AlertCircle size={12} className="text-orange-500" />
              <span>后台更新中</span>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
