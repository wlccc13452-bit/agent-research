import { useStockLoading, STAGE_LABELS } from '../contexts/StockLoadingContext';
import { Loader2, CheckCircle, TrendingUp } from 'lucide-react';
import { useState, useEffect } from 'react';

export default function StockLoadingIndicator() {
  const { loadingState } = useStockLoading();
  const { stockCode, stage, progress, startTime } = loadingState;
  const [elapsedTime, setElapsedTime] = useState(0);

  // 更新已用时间
  useEffect(() => {
    if (stage !== 'idle' && stage !== 'complete' && startTime) {
      const timer = setInterval(() => {
        setElapsedTime(Math.floor((Date.now() - startTime) / 1000));
      }, 1000);
      return () => clearInterval(timer);
    } else {
      setElapsedTime(0);
    }
  }, [stage, startTime]);

  // 如果是空闲或完成状态超过3秒，不显示
  if (stage === 'idle' || !stockCode) {
    return null;
  }

  const isComplete = stage === 'complete';
  const stageLabel = STAGE_LABELS[stage];

  return (
    <div 
      className="flex items-center gap-2 px-3 py-1.5 min-w-0"
      style={{ 
        backgroundColor: isComplete ? 'rgba(34, 197, 94, 0.1)' : 'var(--bg-hover)',
        border: `1px solid ${isComplete ? 'rgba(34, 197, 94, 0.3)' : 'var(--border-color)'}`,
        maxWidth: '320px',
        transition: 'all 0.3s ease'
      }}
    >
      {/* 状态图标 */}
      <div className="flex-shrink-0">
        {isComplete ? (
          <CheckCircle size={14} style={{ color: 'var(--success-color)' }} />
        ) : (
          <Loader2 size={14} className="animate-spin" style={{ color: 'var(--primary-color)' }} />
        )}
      </div>

      {/* 内容区域 */}
      <div className="flex-1 min-w-0">
        {/* 股票代码和耗时 */}
        <div className="flex items-center justify-between gap-1.5 mb-1">
          <div className="flex items-center gap-1.5 min-w-0">
            <TrendingUp size={10} style={{ color: 'var(--text-muted)' }} />
            <span 
              className="text-xs font-bold truncate" 
              style={{ color: 'var(--text-primary)' }}
            >
              {stockCode}
            </span>
          </div>
          {elapsedTime > 0 && !isComplete && (
            <span 
              className="text-xs font-mono flex-shrink-0"
              style={{ color: 'var(--text-muted)' }}
            >
              {elapsedTime}s
            </span>
          )}
        </div>

        {/* 进度条 */}
        <div 
          className="h-1 rounded-full overflow-hidden"
          style={{ backgroundColor: 'var(--border-color)' }}
        >
          <div 
            className={`h-full transition-all duration-300 ${isComplete ? 'bg-green-500' : 'bg-blue-500'}`}
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* 当前阶段 */}
        <div 
          className="text-xs mt-0.5 truncate"
          style={{ color: isComplete ? 'var(--success-color)' : 'var(--text-muted)' }}
        >
          {isComplete ? '加载完成' : stageLabel}
        </div>
      </div>
    </div>
  );
}
