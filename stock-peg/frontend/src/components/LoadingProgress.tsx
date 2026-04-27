import { useTheme } from '../contexts/ThemeContext';
import type { LoadingStage } from '../contexts/StockLoadingContext';
import { STAGE_WEIGHTS } from '../contexts/StockLoadingContext';

interface LoadingStep {
  stage: LoadingStage;
  label: string;
  detail?: string;
  completed: boolean;
  active: boolean;
  duration?: number;
  isSubStep?: boolean;
}

interface LoadingProgressProps {
  currentStage: LoadingStage;
  stockCode: string;
  stageTimes: Record<LoadingStage, number>;
  metadata?: {
    is_updating?: boolean;
    actual_count?: number;
    requested_count?: number;
    last_update?: string;
  };
  error?: string | null;
}

export default function LoadingProgress({ 
  currentStage, 
  stockCode, 
  stageTimes,
  metadata,
  error
}: LoadingProgressProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  // 定义详细的加载步骤
  const steps: LoadingStep[] = [
    // 行情数据阶段（展开子步骤）
    {
      stage: 'loading-quote',
      label: '加载行情数据',
      completed: STAGE_WEIGHTS[currentStage] > STAGE_WEIGHTS['loading-quote'],
      active: currentStage.startsWith('loading-quote'),
      duration: (stageTimes['loading-quote'] || 0) + 
                (stageTimes['loading-quote-connect'] || 0) + 
                (stageTimes['loading-quote-fetch'] || 0) + 
                (stageTimes['loading-quote-parse'] || 0)
    },
    {
      stage: 'loading-quote-connect',
      label: '连接数据源',
      detail: '建立与数据源的连接',
      completed: STAGE_WEIGHTS[currentStage] > STAGE_WEIGHTS['loading-quote-connect'],
      active: currentStage === 'loading-quote-connect',
      duration: stageTimes['loading-quote-connect'],
      isSubStep: true
    },
    {
      stage: 'loading-quote-fetch',
      label: '获取实时行情',
      detail: '从数据源获取最新股价信息',
      completed: STAGE_WEIGHTS[currentStage] > STAGE_WEIGHTS['loading-quote-fetch'],
      active: currentStage === 'loading-quote-fetch',
      duration: stageTimes['loading-quote-fetch'],
      isSubStep: true
    },
    {
      stage: 'loading-quote-parse',
      label: '解析行情数据',
      detail: '解析并验证数据格式',
      completed: STAGE_WEIGHTS[currentStage] > STAGE_WEIGHTS['loading-quote-parse'],
      active: currentStage === 'loading-quote-parse',
      duration: stageTimes['loading-quote-parse'],
      isSubStep: true
    },
    
    // K线快速加载阶段（展开子步骤）
    {
      stage: 'loading-kline-quick',
      label: '快速加载K线',
      completed: STAGE_WEIGHTS[currentStage] > STAGE_WEIGHTS['loading-kline-quick'],
      active: currentStage.startsWith('loading-kline') && !currentStage.includes('full'),
      duration: (stageTimes['loading-kline-quick'] || 0) + 
                (stageTimes['loading-kline-db-check'] || 0) + 
                (stageTimes['loading-kline-db-fetch'] || 0) + 
                (stageTimes['loading-kline-api-fetch'] || 0)
    },
    {
      stage: 'loading-kline-db-check',
      label: '检查本地数据',
      detail: '检查服务端本地数据是否可用',
      completed: STAGE_WEIGHTS[currentStage] > STAGE_WEIGHTS['loading-kline-db-check'],
      active: currentStage === 'loading-kline-db-check',
      duration: stageTimes['loading-kline-db-check'],
      isSubStep: true
    },
    {
      stage: 'loading-kline-db-fetch',
      label: '读取本地数据',
      detail: (metadata?.actual_count || 0) > 0
        ? `已读取 ${metadata?.actual_count || 60} 条K线数据`
        : '本地暂无可用数据',
      completed: STAGE_WEIGHTS[currentStage] > STAGE_WEIGHTS['loading-kline-db-fetch'],
      active: currentStage === 'loading-kline-db-fetch',
      duration: stageTimes['loading-kline-db-fetch'],
      isSubStep: true
    },
    {
      stage: 'loading-kline-api-fetch',
      label: '等待服务端更新',
      detail: metadata?.is_updating
        ? '服务端正在更新本地数据，更新后将主动推送'
        : '等待服务端触发更新任务',
      completed: STAGE_WEIGHTS[currentStage] > STAGE_WEIGHTS['loading-kline-api-fetch'],
      active: currentStage === 'loading-kline-api-fetch',
      duration: stageTimes['loading-kline-api-fetch'],
      isSubStep: true
    },
    
    // 完整K线加载
    {
      stage: 'loading-kline-full',
      label: '加载完整K线',
      detail: (metadata?.actual_count || 0) > 0
        ? `加载完整数据 (${metadata?.actual_count || 120}条)`
        : (metadata?.is_updating ? '本地完整数据更新中，完成后将自动刷新' : '本地暂无完整数据'),
      completed: STAGE_WEIGHTS[currentStage] > STAGE_WEIGHTS['loading-kline-full'],
      active: currentStage === 'loading-kline-full',
      duration: stageTimes['loading-kline-full']
    },
    
    // 技术指标阶段（展开子步骤）
    {
      stage: 'loading-technical',
      label: '计算技术指标',
      completed: currentStage === 'complete',
      active: currentStage.startsWith('loading-technical'),
      duration: (stageTimes['loading-technical'] || 0) + (stageTimes['loading-technical-calc'] || 0)
    },
    {
      stage: 'loading-technical-calc',
      label: '计算指标',
      detail: '计算MA、MACD、KDJ、RSI等指标',
      completed: currentStage === 'complete',
      active: currentStage === 'loading-technical-calc',
      duration: stageTimes['loading-technical-calc'],
      isSubStep: true
    }
  ];

  const currentProgress = STAGE_WEIGHTS[currentStage];
  
  // 计算总耗时
  const totalTime = Object.values(stageTimes).reduce((sum, t) => sum + t, 0);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      backgroundColor: isDark ? '#0a0a0a' : '#f8fafc',
      padding: '2rem'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '600px',
        backgroundColor: isDark ? '#1a1a1a' : '#ffffff',
        borderRadius: '16px',
        padding: '2rem',
        boxShadow: isDark 
          ? '0 4px 24px rgba(0, 0, 0, 0.5)' 
          : '0 4px 24px rgba(0, 0, 0, 0.1)'
      }}>
        {/* 标题 */}
        <div style={{
          textAlign: 'center',
          marginBottom: '2rem'
        }}>
          <h2 style={{
            margin: '0 0 0.5rem 0',
            fontSize: '1.5rem',
            fontWeight: '600',
            color: isDark ? '#e8e8e8' : '#0f172a'
          }}>
            正在加载 {stockCode} 数据
          </h2>
          <p style={{
            margin: 0,
            fontSize: '0.875rem',
            color: isDark ? '#808080' : '#64748b'
          }}>
            {error ? `⚠️ ${error}` : `总耗时: ${(totalTime / 1000).toFixed(2)}s`}
          </p>
        </div>

        {/* 总进度条 */}
        <div style={{ marginBottom: '2rem' }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginBottom: '0.5rem',
            fontSize: '0.875rem',
            color: isDark ? '#808080' : '#64748b'
          }}>
            <span>总进度</span>
            <span>{currentProgress}%</span>
          </div>
          <div style={{
            width: '100%',
            height: '8px',
            backgroundColor: isDark ? '#2a2a2a' : '#e2e8f0',
            borderRadius: '4px',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${currentProgress}%`,
              height: '100%',
              backgroundColor: isDark ? '#22d3ee' : '#3b82f6',
              borderRadius: '4px',
              transition: 'width 0.3s ease'
            }} />
          </div>
        </div>

        {/* 详细步骤列表 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {steps.map((step) => {
            // 子步骤的显示逻辑
            if (step.isSubStep) {
              // 找到对应的主步骤名称
              const mainStageMap: Record<string, string> = {
                'loading-quote-connect': 'loading-quote',
                'loading-quote-fetch': 'loading-quote',
                'loading-quote-parse': 'loading-quote',
                'loading-kline-db-check': 'loading-kline-quick',
                'loading-kline-db-fetch': 'loading-kline-quick',
                'loading-kline-api-fetch': 'loading-kline-quick',
                'loading-technical-calc': 'loading-technical',
              };
              
              const mainStage = mainStageMap[step.stage];
              if (!mainStage) return null;
              
              const isMainActive = currentStage.startsWith(mainStage);
              const isMainCompleted = STAGE_WEIGHTS[currentStage] > STAGE_WEIGHTS[mainStage as LoadingStage];
              
              // 只显示活跃或已完成的主步骤下的子步骤
              if (!isMainActive && !isMainCompleted) {
                return null;
              }
            }
            
            return (
              <div
                key={step.stage}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: step.isSubStep ? '0.75rem' : '1rem',
                  padding: step.isSubStep ? '0.75rem' : '1rem',
                  paddingLeft: step.isSubStep ? '2.5rem' : '1rem',
                  backgroundColor: step.active 
                    ? (isDark ? '#1e3a3a' : '#eff6ff')
                    : 'transparent',
                  borderRadius: '12px',
                  border: step.active 
                    ? `2px solid ${isDark ? '#22d3ee' : '#3b82f6'}`
                    : '2px solid transparent',
                  transition: 'all 0.3s ease',
                  opacity: step.isSubStep ? 0.9 : 1
                }}
              >
                {/* 状态图标 */}
                <div style={{
                  width: step.isSubStep ? '24px' : '32px',
                  height: step.isSubStep ? '24px' : '32px',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  backgroundColor: step.completed
                    ? (isDark ? '#22d3ee' : '#10b981')
                    : step.active
                      ? (isDark ? '#22d3ee' : '#3b82f6')
                      : (isDark ? '#2a2a2a' : '#e2e8f0'),
                  transition: 'all 0.3s ease'
                }}>
                  {step.completed ? (
                    <svg width={step.isSubStep ? 12 : 16} height={step.isSubStep ? 12 : 16} viewBox="0 0 16 16" fill="none">
                      <path d="M13.5 4.5L6 12L2.5 8.5" 
                        stroke={isDark ? '#0a0a0a' : '#ffffff'} 
                        strokeWidth="2" 
                        strokeLinecap="round" 
                        strokeLinejoin="round"/>
                    </svg>
                  ) : step.active ? (
                    <div style={{
                      width: step.isSubStep ? '12px' : '16px',
                      height: step.isSubStep ? '12px' : '16px',
                      border: `2px solid ${isDark ? '#0a0a0a' : '#ffffff'}`,
                      borderTopColor: 'transparent',
                      borderRadius: '50%',
                      animation: 'spin 1s linear infinite'
                    }} />
                  ) : (
                    <div style={{
                      width: step.isSubStep ? '6px' : '8px',
                      height: step.isSubStep ? '6px' : '8px',
                      borderRadius: '50%',
                      backgroundColor: isDark ? '#404040' : '#cbd5e1'
                    }} />
                  )}
                </div>

                {/* 步骤内容 */}
                <div style={{ flex: 1 }}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    marginBottom: '0.25rem'
                  }}>
                    <span style={{
                      fontSize: step.isSubStep ? '0.875rem' : '0.9375rem',
                      fontWeight: step.active ? '600' : step.isSubStep ? '400' : '500',
                      color: step.completed 
                        ? (isDark ? '#22d3ee' : '#10b981')
                        : step.active
                          ? (isDark ? '#e8e8e8' : '#0f172a')
                          : (isDark ? '#808080' : '#64748b')
                    }}>
                      {step.label}
                    </span>
                    {step.duration !== undefined && step.duration > 0 && (
                      <span style={{
                        fontSize: '0.75rem',
                        color: isDark ? '#808080' : '#94a3b8'
                      }}>
                        {(step.duration / 1000).toFixed(2)}s
                      </span>
                    )}
                  </div>
                  {step.detail && (
                    <p style={{
                      margin: 0,
                      fontSize: step.isSubStep ? '0.75rem' : '0.8125rem',
                      color: isDark ? '#a0a0a0' : '#64748b'
                    }}>
                      {step.detail}
                    </p>
                  )}
                  
                </div>
              </div>
            );
          })}
        </div>

        {/* 提示信息 */}
        <div style={{
          marginTop: '2rem',
          padding: '1rem',
          backgroundColor: isDark ? '#1e1e1e' : '#f1f5f9',
          borderRadius: '8px',
          fontSize: '0.8125rem',
          color: isDark ? '#a0a0a0' : '#64748b',
          textAlign: 'center'
        }}>
          <p style={{ margin: 0 }}>
            💡 提示：首次加载可能需要更长时间，服务端更新后会主动推送最新数据
          </p>
        </div>
      </div>

      {/* CSS动画 */}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
