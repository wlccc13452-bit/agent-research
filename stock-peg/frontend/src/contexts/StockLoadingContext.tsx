import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import { clientLogger } from '../services/clientLogger';

// 加载阶段定义
export type LoadingStage = 
  | 'idle'
  | 'loading-quote'
  | 'loading-quote-connect'
  | 'loading-quote-fetch'
  | 'loading-quote-parse'
  | 'loading-kline-quick'
  | 'loading-kline-db-check'
  | 'loading-kline-db-fetch'
  | 'loading-kline-api-fetch'
  | 'loading-kline-full'
  | 'loading-technical'
  | 'loading-technical-calc'
  | 'complete';

// 阶段显示名称
export const STAGE_LABELS: Record<LoadingStage, string> = {
  'idle': '空闲',
  'loading-quote': '同步本地行情',
  'loading-quote-connect': '连接推送服务',
  'loading-quote-fetch': '同步行情缓存',
  'loading-quote-parse': '处理行情数据',
  'loading-kline-quick': '快速加载K线',
  'loading-kline-db-check': '检查本地数据',
  'loading-kline-db-fetch': '读取本地数据',
  'loading-kline-api-fetch': '等待后台推送',
  'loading-kline-full': '加载完整K线',
  'loading-technical': '计算技术指标',
  'loading-technical-calc': '计算MA、MACD、KDJ...',
  'complete': '加载完成',
};

// 阶段进度权重（用于计算总体进度）
export const STAGE_WEIGHTS: Record<LoadingStage, number> = {
  'idle': 0,
  'loading-quote': 5,
  'loading-quote-connect': 8,
  'loading-quote-fetch': 12,
  'loading-quote-parse': 15,
  'loading-kline-quick': 20,
  'loading-kline-db-check': 25,
  'loading-kline-db-fetch': 35,
  'loading-kline-api-fetch': 45,
  'loading-kline-full': 60,
  'loading-technical': 80,
  'loading-technical-calc': 90,
  'complete': 100,
};

interface StockLoadingState {
  stockCode: string | null;
  stage: LoadingStage;
  progress: number; // 0-100
  startTime: number | null;
  stageTimes: Record<LoadingStage, number>; // 每个阶段的耗时
  currentStageStart: number | null; // 当前阶段开始时间
  error: string | null; // 错误信息
  metadata?: {
    is_updating?: boolean;
    actual_count?: number;
    requested_count?: number;
    last_update?: string;
  };
}

interface StockLoadingContextType {
  loadingState: StockLoadingState;
  startLoading: (stockCode: string) => void;
  updateStage: (stage: LoadingStage, metadata?: any) => void;
  completeLoading: () => void;
  resetLoading: () => void;
  setError: (error: string) => void;
}

const defaultState: StockLoadingState = {
  stockCode: null,
  stage: 'idle',
  progress: 0,
  startTime: null,
  stageTimes: {
    'idle': 0,
    'loading-quote': 0,
    'loading-quote-connect': 0,
    'loading-quote-fetch': 0,
    'loading-quote-parse': 0,
    'loading-kline-quick': 0,
    'loading-kline-db-check': 0,
    'loading-kline-db-fetch': 0,
    'loading-kline-api-fetch': 0,
    'loading-kline-full': 0,
    'loading-technical': 0,
    'loading-technical-calc': 0,
    'complete': 0,
  },
  currentStageStart: null,
  error: null,
  metadata: undefined,
};

const StockLoadingContext = createContext<StockLoadingContextType | undefined>(undefined);

export function StockLoadingProvider({ children }: { children: ReactNode }) {
  const [loadingState, setLoadingState] = useState<StockLoadingState>(defaultState);

  const startLoading = useCallback((stockCode: string) => {
    const now = Date.now();
    setLoadingState({
      stockCode,
      stage: 'loading-quote',
      progress: 0,
      startTime: now,
      currentStageStart: now,
      stageTimes: { ...defaultState.stageTimes },
      error: null,
      metadata: undefined,
    });
    clientLogger.info('loading', `开始加载 ${stockCode} 数据`, {
      stage: 'loading-quote',
      progress: STAGE_WEIGHTS['loading-quote'],
      stageLabel: STAGE_LABELS['loading-quote'],
    }, undefined, stockCode);
  }, []);

  const updateStage = useCallback((stage: LoadingStage, metadata?: any) => {
    let stockCodeForLog: string | undefined;
    let prevStage: LoadingStage = 'idle';
    let prevStageDuration: number | undefined;

    setLoadingState(prev => {
      const now = Date.now();
      const stageTimes = { ...prev.stageTimes };
      stockCodeForLog = prev.stockCode || undefined;
      prevStage = prev.stage;
      
      if (prev.currentStageStart && prev.stage !== 'idle') {
        prevStageDuration = now - prev.currentStageStart;
        stageTimes[prev.stage] = prevStageDuration;
      }
      
      return {
        ...prev,
        stage,
        progress: STAGE_WEIGHTS[stage],
        currentStageStart: now,
        stageTimes,
        metadata: metadata || prev.metadata,
      };
    });
    clientLogger.info('loading', `加载阶段: ${STAGE_LABELS[stage]}`, {
      stage,
      stageLabel: STAGE_LABELS[stage],
      progress: STAGE_WEIGHTS[stage],
      previousStage: prevStage,
      previousStageLabel: STAGE_LABELS[prevStage],
      previousStageDurationMs: prevStageDuration,
      ...metadata,
    }, undefined, stockCodeForLog);
  }, []);

  const completeLoading = useCallback(() => {
    let stockCodeForLog: string | undefined;
    let totalDuration: number | undefined;
    let stageTimesForLog: Record<LoadingStage, number> = { ...defaultState.stageTimes };

    setLoadingState(prev => {
      const now = Date.now();
      const stageTimes = { ...prev.stageTimes };
      stockCodeForLog = prev.stockCode || undefined;
      totalDuration = prev.startTime ? now - prev.startTime : undefined;
      
      if (prev.currentStageStart && prev.stage !== 'idle' && prev.stage !== 'complete') {
        stageTimes[prev.stage] = now - prev.currentStageStart;
      }
      stageTimesForLog = stageTimes;
      
      return {
        ...prev,
        stage: 'complete',
        progress: 100,
        stageTimes,
        currentStageStart: null,
      };
    });
    clientLogger.logLoadingComplete('股票详情加载', totalDuration || 0, true, stockCodeForLog, {
      stage: 'complete',
      stageLabel: STAGE_LABELS.complete,
      stageTimes: stageTimesForLog,
    });
    
    setTimeout(() => {
      setLoadingState(prev => {
        if (prev.stage === 'complete') {
          return defaultState;
        }
        return prev;
      });
    }, 3000);
  }, []);

  const resetLoading = useCallback(() => {
    setLoadingState(defaultState);
  }, []);

  const setError = useCallback((error: string) => {
    let stockCodeForLog: string | undefined;
    setLoadingState(prev => {
      stockCodeForLog = prev.stockCode || undefined;
      return {
        ...prev,
        error,
      };
    });
    clientLogger.error('loading', '股票详情加载失败', { error }, undefined, stockCodeForLog);
  }, []);

  return (
    <StockLoadingContext.Provider value={{
      loadingState,
      startLoading,
      updateStage,
      completeLoading,
      resetLoading,
      setError,
    }}>
      {children}
    </StockLoadingContext.Provider>
  );
}

export function useStockLoading() {
  const context = useContext(StockLoadingContext);
  if (!context) {
    throw new Error('useStockLoading must be used within StockLoadingProvider');
  }
  return context;
}
