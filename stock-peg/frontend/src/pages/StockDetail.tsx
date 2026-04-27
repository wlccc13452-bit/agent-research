import { useState, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import { stocksApi, fundamentalApi } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import { useStockLoading } from '../contexts/StockLoadingContext';
import { clientLogger } from '../services/clientLogger';
import KLineChart from '../components/KLineChart';
import LoadingProgress from '../components/LoadingProgress';

type PeriodType = 'm1' | 'm5' | 'm15' | 'm30' | 'm60' | 'day' | 'week' | 'month';
type KlineQueryData = {
  data: any[];
  metadata?: any;
};

export default function StockDetail() {
  const queryClient = useQueryClient();
  const { stockCode } = useParams<{ stockCode: string }>();
  const [period, setPeriod] = useState<PeriodType>('day');
  const { isConnected, quotes, subscribe } = useWebSocket();
  const { startLoading, updateStage, completeLoading, loadingState, setError } = useStockLoading();
  
  // 存储metadata信息用于显示详细的加载步骤
  const [loadingMetadata, setLoadingMetadata] = useState<{
    is_updating?: boolean;
    actual_count?: number;
    requested_count?: number;
    last_update?: string;
  }>({});

  // 当股票代码改变时，开始加载追踪
  useEffect(() => {
    if (stockCode) {
      console.log('📊 开始加载股票:', stockCode);
      clientLogger.info('loading', `开始加载股票详情页`, { stockCode }, undefined, stockCode);
      startLoading(stockCode);
      setLoadingMetadata({}); // 重置metadata
    }
  }, [stockCode, startLoading]);

  // 获取初始行情
  const { data: initialQuote, isFetched: isQuoteFetched } = useQuery({
    queryKey: ['quote', stockCode],
    queryFn: async () => {
      console.log('📡 开始获取行情数据:', stockCode);
      const startTime = Date.now();
      
      // 更新为连接数据源阶段
      updateStage('loading-quote-connect');
      clientLogger.info('loading', '连接数据源', undefined, undefined, stockCode);
      console.log('  → 连接数据源');
      
      // 更新为获取行情阶段
      updateStage('loading-quote-fetch');
      clientLogger.logApiRequest('/api/stocks/quote/' + stockCode, 'GET', undefined, stockCode);
      console.log('  → 获取实时行情');
      
      try {
        const quote = await stocksApi.getQuote(stockCode!);
        const duration = Date.now() - startTime;
        
        // 如果返回数据，说明数据库中有数据
        if (quote) {
          console.log(`  ✅ 行情获取成功 (${duration}ms):`, quote);
          clientLogger.logApiResponse('/api/stocks/quote/' + stockCode, duration, true, JSON.stringify(quote).length, stockCode);
          
          // 更新为解析数据阶段
          updateStage('loading-quote-parse');
          clientLogger.info('loading', '解析行情数据', undefined, undefined, stockCode);
          console.log('  → 解析行情数据');
          
          // 模拟解析延迟
          await new Promise(resolve => setTimeout(resolve, 50));
          
          console.log('  ✅ 行情数据解析完成');
          clientLogger.logLoadingComplete('行情数据加载', duration, true, stockCode);
          
          return quote;
        } else {
          // 数据库无数据
          console.log('  ⚠️ 数据库无行情数据');
          clientLogger.info('loading', '数据库无行情数据', undefined, undefined, stockCode);
          return null;
        }
      } catch (error) {
        const duration = Date.now() - startTime;
        const errorMsg = error instanceof Error ? error.message : '获取行情数据失败';
        
        // 如果是404错误，说明数据库无数据
        const is404 = errorMsg.includes('404') || errorMsg.includes('未找到');
        
        if (is404) {
          console.log('  ⚠️ 数据库中无此股票的行情数据');
          clientLogger.info('loading', '数据库中无此股票的行情数据', { stockCode }, undefined, stockCode);
          updateStage('loading-quote-parse', { skipped: true, reason: 'quote_not_found_in_db' });
          clientLogger.logLoadingComplete('行情数据加载', duration, true, stockCode, {
            skipped: true,
            reason: 'quote_not_found_in_db'
          });
          return null;
        }
        
        console.error('  ❌ 获取行情失败:', errorMsg, error);
        
        clientLogger.logApiResponse('/api/stocks/quote/' + stockCode, duration, false, undefined, stockCode);
        clientLogger.error('loading', '获取行情数据失败', { error: errorMsg }, duration, stockCode);
        
        setError(errorMsg);
        throw error;
      }
    },
    enabled: !!stockCode && !stockCode.startsWith('UNKNOWN'),
    retry: 0,
    staleTime: 10000, // 10秒内不重新请求
  });

  // 订阅实时行情
  useEffect(() => {
    if (isConnected && stockCode) {
      subscribe([stockCode]);
    }
  }, [isConnected, stockCode, subscribe]);

  useEffect(() => {
    const handleWebSocketUpdate = (event: Event) => {
      const customEvent = event as CustomEvent;
      const message = customEvent.detail;
      if (!message) return;

      // 检查股票代码是否匹配
      if (stockCode && message.stock_code && message.stock_code !== stockCode) return;

      // 处理 K 线更新
      if (message.type === 'kline_updated') {
        console.log('📡 收到 K 线数据更新推送:', message.stock_code);

        const pushedKline = Array.isArray(message.data?.kline) ? message.data.kline : [];
        
        if (pushedKline.length > 0) {
          const payload = {
            data: pushedKline.map((k: any) => ({
              date: k.date,
              open: k.open,
              close: k.close,
              high: k.high,
              low: k.low,
              volume: k.volume
            })),
            metadata: {
              stock_code: stockCode,
              period,
              count: pushedKline.length,
              quick_load: false,
              requested_count: pushedKline.length,
              actual_count: pushedKline.length,
              local_data_available: true,
              is_updating: false,
              last_update: message.timestamp,
              needs_update: false,
              update_reason: null
            }
          };

          queryClient.setQueryData(['kline-full', stockCode, period], payload);
          queryClient.setQueryData(['kline-quick', stockCode, period], payload);
          setLoadingMetadata((prev) => ({
            ...prev,
            is_updating: false,
            actual_count: pushedKline.length,
            requested_count: pushedKline.length,
            last_update: message.timestamp
          }));
        } else {
          // 如果推送的消息中没有数据，则触发重新获取
          queryClient.invalidateQueries({ queryKey: ['kline-quick', stockCode, period] });
          queryClient.invalidateQueries({ queryKey: ['kline-full', stockCode, period] });
        }
        
        // 同时触发 PMR 刷新
        queryClient.invalidateQueries({ queryKey: ['pmr', stockCode] });
      }
      
      // 处理行情更新 (用于实时价格同步)
      else if (message.type === 'quote_updated' || message.type === 'quote') {
        const quoteData = message.data || message.quote;
        if (!quoteData) return;
        
        console.log('📡 收到实时行情推送:', message.stock_code, quoteData.last_price || quoteData.price);
        
        // 更新 React Query 中的行情缓存
        queryClient.setQueryData(['quote', stockCode], (oldData: any) => {
          if (!oldData) return quoteData;
          return { ...oldData, ...quoteData };
        });
      }
      
      // 处理财务数据更新
      else if (message.type === 'financial_updated' || message.type === 'financial-updated') {
        if (message.stock_code && !message.stock_code.startsWith('UNKNOWN')) {
          console.log('📡 收到财务数据更新推送:', message.stock_code);
          
          // 使财务数据相关的查询失效，触发重新获取
          queryClient.invalidateQueries({ queryKey: ['fundamental', stockCode] });
          queryClient.invalidateQueries({ queryKey: ['valuation', stockCode] });
          queryClient.invalidateQueries({ queryKey: ['annual-report', stockCode] });
          queryClient.invalidateQueries({ queryKey: ['quarterly-data', stockCode] });
        }
      }

      // 处理美股指数更新
      else if (message.type === 'us_index_updated') {
        console.log('📡 收到美股指数更新推送:', message.symbol);
        // 这里可以触发相关指数数据的刷新，如果页面有显示的话
        queryClient.invalidateQueries({ queryKey: ['us-indices'] });
      }

      // 处理后台更新进度
      else if (message.type === 'background_update_progress') {
        if (message.progress && message.progress.current_code === stockCode) {
          console.log('📡 收到当前股票后台更新进度:', message.progress);
          setLoadingMetadata(prev => ({
            ...prev,
            is_updating: true,
            progress: message.progress
          }));
        }
      }
    };

    window.addEventListener('websocket-message', handleWebSocketUpdate);
    return () => window.removeEventListener('websocket-message', handleWebSocketUpdate);
  }, [stockCode, period, queryClient]);

  // 合并实时行情
  const realtimeQuote = stockCode ? quotes.get(stockCode) : null;
  const quote = realtimeQuote ? { ...initialQuote, ...realtimeQuote } : initialQuote;

  // 第一步：快速加载最近60条数据
  const { data: quickKlineData, isLoading: quickLoading } = useQuery<KlineQueryData>({
    queryKey: ['kline-quick', stockCode, period],
    queryFn: async () => {
      // 更新为检查数据库阶段
      updateStage('loading-kline-db-check');
      
      // 模拟检查延迟
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // 更新为获取数据阶段
      updateStage('loading-kline-db-fetch');
      
      try {
        const response = await stocksApi.getKlineFromDB(stockCode!, period, 60, true);
        const metadata = response.metadata;
        const klines = response.data || response;
        
        // 更新metadata用于显示加载步骤详情
        if (metadata) {
          setLoadingMetadata(prev => ({
            ...prev,
            ...metadata
          }));
          
          if (metadata.is_updating) {
            updateStage('loading-kline-api-fetch', metadata);
          }
        }
        
        return {
          data: klines.map((k: any) => ({
            date: k.date,
            open: k.open,
            close: k.close,
            high: k.high,
            low: k.low,
            volume: k.volume
          })),
          metadata
        };
      } catch (error) {
        setError('获取K线数据失败');
        throw error;
      }
    },
    enabled: !!stockCode && !stockCode.startsWith('UNKNOWN'),
    staleTime: 30000, // 30秒内不重新请求
  });

  // 第二步：后台加载完整数据（120条）
  const { data: fullKlineData } = useQuery<KlineQueryData>({
    queryKey: ['kline-full', stockCode, period],
    queryFn: async () => {
      const response = await stocksApi.getKlineFromDB(stockCode!, period, 120, false);
      const metadata = response.metadata;
      const klines = response.data || response;
      
      // 更新metadata用于显示加载步骤详情
      if (metadata) {
        setLoadingMetadata(prev => ({
          ...prev,
          ...metadata
        }));
      }
      
      return {
        data: klines.map((k: any) => ({
          date: k.date,
          open: k.open,
          close: k.close,
          high: k.high,
          low: k.low,
          volume: k.volume
        })),
        metadata
      };
    },
    enabled: !!stockCode && !stockCode.startsWith('UNKNOWN') && !!quickKlineData, // 等快速加载完成后才开始
    staleTime: 60000, // 1分钟内不重新请求
  });

  // 追踪行情数据加载
  useEffect(() => {
    if (isQuoteFetched && loadingState.stage === 'loading-quote-parse' && loadingState.stockCode === stockCode) {
      console.log('📊 行情加载完成，开始加载K线');
      clientLogger.info('loading', '行情加载完成，开始加载K线', undefined, undefined, stockCode);
      updateStage('loading-kline-quick');
    }
  }, [isQuoteFetched, loadingState.stage, loadingState.stockCode, stockCode, updateStage]);

  // 追踪快速K线加载
  useEffect(() => {
    if (quickKlineData && loadingState.stage === 'loading-kline-quick' && loadingState.stockCode === stockCode) {
      updateStage('loading-kline-full');
    }
  }, [quickKlineData, loadingState.stage, loadingState.stockCode, stockCode, updateStage]);

  // 追踪完整K线加载
  useEffect(() => {
    if (fullKlineData && loadingState.stage === 'loading-kline-full' && loadingState.stockCode === stockCode) {
      updateStage('loading-technical');
    }
  }, [fullKlineData, loadingState.stage, loadingState.stockCode, stockCode, updateStage]);

  // 获取技术指标
  const { data: technical } = useQuery({
    queryKey: ['technical', stockCode],
    queryFn: async () => {
      // 更新为计算阶段
      updateStage('loading-technical-calc');
      
      try {
        const tech = await stocksApi.getTechnical(stockCode!);
        return tech;
      } catch (error) {
        setError('计算技术指标失败');
        throw error;
      }
    },
    enabled: !!stockCode && !stockCode.startsWith('UNKNOWN'),
  });

  // 追踪技术指标加载
  useEffect(() => {
    if (technical && loadingState.stage === 'loading-technical-calc' && loadingState.stockCode === stockCode) {
      updateStage('loading-fundamental');
    }
  }, [technical, loadingState.stage, loadingState.stockCode, stockCode, updateStage]);

  // 获取基本面分析数据
  const { data: fundamental } = useQuery({
    queryKey: ['fundamental', stockCode],
    queryFn: async () => {
      try {
        const data = await fundamentalApi.analyze(stockCode!);
        return data;
      } catch (error) {
        console.error('获取基本面数据失败:', error);
        return null;
      }
    },
    enabled: !!stockCode && !stockCode.startsWith('UNKNOWN') && !!technical,
    staleTime: 300000, // 5分钟内不重新请求
  });

  // 追踪基本面加载
  useEffect(() => {
    if (fundamental && loadingState.stage === 'loading-fundamental' && loadingState.stockCode === stockCode) {
      completeLoading();
    }
  }, [fundamental, loadingState.stage, loadingState.stockCode, stockCode, completeLoading]);

  // 优先使用完整数据，如果没有则使用快速数据
  const quickKlinePayload = quickKlineData as KlineQueryData | undefined;
  const fullKlinePayload = fullKlineData as KlineQueryData | undefined;
  const klineData = fullKlinePayload?.data || quickKlinePayload?.data || [];
  const isLoading = quickLoading && !quickKlinePayload?.data?.length;

  // 显示详细的加载进度
  if (isLoading || (loadingState.stage !== 'idle' && loadingState.stage !== 'complete')) {
    return (
      <LoadingProgress
        currentStage={loadingState.stage}
        stockCode={stockCode || ''}
        stageTimes={loadingState.stageTimes}
        metadata={loadingMetadata}
        error={loadingState.error}
      />
    );
  }

  return (
    <div className="stock-detail">
      <div className="page-header">
        <div className="flex items-center gap-2">
          <h2>{quote?.name || '股票详情'}</h2>
          <div className={`status-badge ${isConnected ? 'connected' : 'disconnected'}`}>
            <div className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`} />
            {isConnected ? '实时行情已连接' : '行情连接已断开'}
          </div>
        </div>
        <span className="stock-code">{stockCode}</span>
      </div>

      {/* 实时行情卡片 */}
      {quote && (
        <div className="quote-card">
          <div className="quote-price">
            <span className={`price ${quote.change_pct > 0 ? 'up' : quote.change_pct < 0 ? 'down' : ''}`}>
              {quote.price.toFixed(2)}
            </span>
            <span className={`change ${quote.change_pct > 0 ? 'up' : quote.change_pct < 0 ? 'down' : ''}`}>
              {quote.change.toFixed(2)} ({quote.change_pct.toFixed(2)}%)
            </span>
          </div>
          <div className="quote-details">
            <div className="detail-row">
              <span>开盘: {quote.open.toFixed(2)}</span>
              <span>最高: {quote.high.toFixed(2)}</span>
              <span>最低: {quote.low.toFixed(2)}</span>
            </div>
            <div className="detail-row">
              <span>成交量: {(quote.volume / 10000).toFixed(2)}万</span>
              <span>换手率: {quote.turnover_rate?.toFixed(2) || '-'}%</span>
            </div>
          </div>
        </div>
      )}

      {/* K线周期选择 */}
      <div className="period-selector">
        <div className="period-group">
          <span className="period-label">分钟线：</span>
          <button 
            className={`period-btn ${period === 'm1' ? 'active' : ''}`}
            onClick={() => setPeriod('m1')}
          >
            1分钟
          </button>
          <button 
            className={`period-btn ${period === 'm5' ? 'active' : ''}`}
            onClick={() => setPeriod('m5')}
          >
            5分钟
          </button>
          <button 
            className={`period-btn ${period === 'm15' ? 'active' : ''}`}
            onClick={() => setPeriod('m15')}
          >
            15分钟
          </button>
          <button 
            className={`period-btn ${period === 'm30' ? 'active' : ''}`}
            onClick={() => setPeriod('m30')}
          >
            30分钟
          </button>
          <button 
            className={`period-btn ${period === 'm60' ? 'active' : ''}`}
            onClick={() => setPeriod('m60')}
          >
            60分钟
          </button>
        </div>
        <div className="period-group">
          <span className="period-label">K线：</span>
          <button 
            className={`period-btn ${period === 'day' ? 'active' : ''}`}
            onClick={() => setPeriod('day')}
          >
            日K
          </button>
          <button 
            className={`period-btn ${period === 'week' ? 'active' : ''}`}
            onClick={() => setPeriod('week')}
          >
            周K
          </button>
          <button 
            className={`period-btn ${period === 'month' ? 'active' : ''}`}
            onClick={() => setPeriod('month')}
          >
            月K
          </button>
        </div>
      </div>

      {/* K线图表 */}
      {klineData && klineData.length > 0 && (
        <div className="chart-container">
          <KLineChart 
            data={klineData} 
            stockCode={stockCode!} 
            stockName={quote?.name || stockCode!}
            height="600px"
          />
        </div>
      )}

      {/* 技术指标 */}
      {technical && (
        <div className="technical-indicators">
          <h3>技术指标</h3>
          <div className="indicators-grid">
            <div className="indicator-item">
              <span className="label">MA5</span>
              <span className="value">{technical.ma5?.toFixed(2) || '-'}</span>
            </div>
            <div className="indicator-item">
              <span className="label">MA10</span>
              <span className="value">{technical.ma10?.toFixed(2) || '-'}</span>
            </div>
            <div className="indicator-item">
              <span className="label">MA20</span>
              <span className="value">{technical.ma20?.toFixed(2) || '-'}</span>
            </div>
            <div className="indicator-item">
              <span className="label">MACD</span>
              <span className="value">{technical.macd?.toFixed(4) || '-'}</span>
            </div>
            <div className="indicator-item">
              <span className="label">RSI</span>
              <span className="value">{technical.rsi?.toFixed(2) || '-'}</span>
            </div>
            <div className="indicator-item">
              <span className="label">KDJ-K</span>
              <span className="value">{technical.kdj_k?.toFixed(2) || '-'}</span>
            </div>
            <div className="indicator-item">
              <span className="label">KDJ-D</span>
              <span className="value">{technical.kdj_d?.toFixed(2) || '-'}</span>
            </div>
            <div className="indicator-item">
              <span className="label">KDJ-J</span>
              <span className="value">{technical.kdj_j?.toFixed(2) || '-'}</span>
            </div>
          </div>
        </div>
      )}

      {/* 基本面分析 */}
      {fundamental && (
        <div className="fundamental-analysis">
          <h3>基本面分析</h3>
          {fundamental.is_updating && (
            <div className="updating-notice">
              <span className="loading-spinner"></span>
              <span>财务数据正在更新中...</span>
            </div>
          )}
          
          {/* 估值指标 */}
          {fundamental.valuation && Object.keys(fundamental.valuation).length > 0 && (
            <div className="analysis-section">
              <h4>估值指标 {fundamental.valuation.score && <span className={`score score-${Math.round(fundamental.valuation.score)}`}>{fundamental.valuation.score.toFixed(1)}分</span>}</h4>
              <div className="indicators-grid">
                <div className="indicator-item">
                  <span className="label">PE(TTM)</span>
                  <span className="value">{fundamental.valuation.pe_ttm?.toFixed(2) || '-'}</span>
                </div>
                <div className="indicator-item">
                  <span className="label">PE(LYR)</span>
                  <span className="value">{fundamental.valuation.pe_lyr?.toFixed(2) || '-'}</span>
                </div>
                <div className="indicator-item">
                  <span className="label">PB</span>
                  <span className="value">{fundamental.valuation.pb?.toFixed(2) || '-'}</span>
                </div>
                <div className="indicator-item">
                  <span className="label">PS(TTM)</span>
                  <span className="value">{fundamental.valuation.ps_ttm?.toFixed(2) || '-'}</span>
                </div>
                <div className="indicator-item">
                  <span className="label">PEG</span>
                  <span className="value">{fundamental.valuation.peg?.toFixed(2) || '-'}</span>
                </div>
              </div>
            </div>
          )}

          {/* 成长性 */}
          {fundamental.growth && Object.keys(fundamental.growth).length > 0 && (
            <div className="analysis-section">
              <h4>成长性 {fundamental.growth.score && <span className={`score score-${Math.round(fundamental.growth.score)}`}>{fundamental.growth.score.toFixed(1)}分</span>}</h4>
              <div className="indicators-grid">
                <div className="indicator-item">
                  <span className="label">营收CAGR(3年)</span>
                  <span className={`value ${fundamental.growth.revenue_cagr_3y > 0 ? 'up' : fundamental.growth.revenue_cagr_3y < 0 ? 'down' : ''}`}>
                    {fundamental.growth.revenue_cagr_3y ? `${(fundamental.growth.revenue_cagr_3y * 100).toFixed(2)}%` : '-'}
                  </span>
                </div>
                <div className="indicator-item">
                  <span className="label">营收CAGR(5年)</span>
                  <span className={`value ${fundamental.growth.revenue_cagr_5y > 0 ? 'up' : fundamental.growth.revenue_cagr_5y < 0 ? 'down' : ''}`}>
                    {fundamental.growth.revenue_cagr_5y ? `${(fundamental.growth.revenue_cagr_5y * 100).toFixed(2)}%` : '-'}
                  </span>
                </div>
                <div className="indicator-item">
                  <span className="label">利润CAGR(3年)</span>
                  <span className={`value ${fundamental.growth.profit_cagr_3y > 0 ? 'up' : fundamental.growth.profit_cagr_3y < 0 ? 'down' : ''}`}>
                    {fundamental.growth.profit_cagr_3y ? `${(fundamental.growth.profit_cagr_3y * 100).toFixed(2)}%` : '-'}
                  </span>
                </div>
                <div className="indicator-item">
                  <span className="label">ROE</span>
                  <span className="value">{fundamental.growth.roe ? `${(fundamental.growth.roe * 100).toFixed(2)}%` : '-'}</span>
                </div>
                <div className="indicator-item">
                  <span className="label">ROA</span>
                  <span className="value">{fundamental.growth.roa ? `${(fundamental.growth.roa * 100).toFixed(2)}%` : '-'}</span>
                </div>
              </div>
            </div>
          )}

          {/* 财务健康度 */}
          {fundamental.financial_health && Object.keys(fundamental.financial_health).length > 0 && (
            <div className="analysis-section">
              <h4>财务健康度 {fundamental.financial_health.score && <span className={`score score-${Math.round(fundamental.financial_health.score)}`}>{fundamental.financial_health.score.toFixed(1)}分</span>}</h4>
              <div className="indicators-grid">
                <div className="indicator-item">
                  <span className="label">资产负债率</span>
                  <span className={`value ${fundamental.financial_health.debt_ratio > 0.7 ? 'down' : ''}`}>
                    {fundamental.financial_health.debt_ratio ? `${(fundamental.financial_health.debt_ratio * 100).toFixed(2)}%` : '-'}
                  </span>
                </div>
                <div className="indicator-item">
                  <span className="label">流动比率</span>
                  <span className="value">{fundamental.financial_health.current_ratio?.toFixed(2) || '-'}</span>
                </div>
                <div className="indicator-item">
                  <span className="label">现金流/利润</span>
                  <span className="value">{fundamental.financial_health.ocf_to_profit?.toFixed(2) || '-'}</span>
                </div>
                <div className="indicator-item">
                  <span className="label">Z-Score</span>
                  <span className={`value ${fundamental.financial_health.altman_z_score && fundamental.financial_health.altman_z_score < 1.8 ? 'down' : ''}`}>
                    {fundamental.financial_health.altman_z_score?.toFixed(2) || '-'}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* 综合评分 */}
          {fundamental.overall_score && (
            <div className="overall-score">
              <span className="score-label">综合评分</span>
              <span className={`score-value score-${Math.round(fundamental.overall_score)}`}>
                {fundamental.overall_score.toFixed(1)}
              </span>
              {fundamental.recommendation && (
                <div className="recommendation">
                  <span className="rating">{fundamental.recommendation.rating}</span>
                  <span className="reason">{fundamental.recommendation.reason}</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
