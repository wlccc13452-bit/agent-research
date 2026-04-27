/**
 * API 服务封装
 */

// 使用相对路径，通过 Vite 代理访问后端（避免 CORS 问题）
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

class ApiError extends Error {
  status: number;
  detail?: string;

  constructor(status: number, message: string, detail?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

/**
 * 通用请求方法
 */
type RequestOptions = RequestInit & {
  timeoutMs?: number;
};

async function request<T>(
  endpoint: string,
  options?: RequestOptions
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const { timeoutMs = 15000, signal: externalSignal, ...restOptions } = options || {};
  const headers = new Headers(restOptions.headers || {});

  if (restOptions.body !== undefined && restOptions.body !== null && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const controller = new AbortController();
  let abortHandler: (() => void) | undefined;
  if (externalSignal) {
    if (externalSignal.aborted) {
      controller.abort();
    } else {
      abortHandler = () => controller.abort();
      externalSignal.addEventListener('abort', abortHandler, { once: true });
    }
  }
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  let response: Response;
  try {
    response = await fetch(url, {
      headers,
      ...restOptions,
      signal: controller.signal,
    });
  } catch (error) {
    if ((error as Error)?.name === 'AbortError') {
      throw new Error(`请求超时: ${endpoint}`);
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
    if (externalSignal && abortHandler) {
      externalSignal.removeEventListener('abort', abortHandler);
    }
  }

  if (!response.ok) {
    let detail: string | undefined;
    try {
      const errorData = await response.json();
      detail = errorData?.detail;
    } catch {
      detail = undefined;
    }

    throw new ApiError(
      response.status,
      `API Error: ${response.status} ${response.statusText}`,
      detail
    );
  }

  return response.json();
}

/**
 * 自持管理 API
 */
export const holdingsApi = {
  // 获取自持列表
  getHoldings: () => request<any>('/api/holdings/'),

  // 刷新自持列表 (从文件重新加载)
  refreshHoldings: () => request<any>('/api/holdings/refresh', { method: 'POST' }),

  // 添加股票
  addStock: (sectorName: string, stockName: string, stockCode?: string) =>
    request('/api/holdings/stock', {
      method: 'POST',
      body: JSON.stringify({ sector_name: sectorName, stock_name: stockName, stock_code: stockCode }),
    }),

  // 删除股票
  removeStock: (sectorName: string, stockName: string) =>
    request('/api/holdings/stock', {
      method: 'DELETE',
      body: JSON.stringify({ sector_name: sectorName, stock_name: stockName }),
    }),

  // 更新股票
  updateStock: (data: {
    sector_name: string;
    old_name: string;
    new_name?: string;
    new_code?: string;
    new_sector?: string;
  }) =>
    request('/api/holdings/stock', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  // 更新股票目标价
  updateStockTarget: (data: {
    sector_name: string;
    stock_name: string;
    target_price?: number | null;
    change_up_pct?: number | null;
    change_down_pct?: number | null;
  }) =>
    request('/api/holdings/stock/target', {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  // 添加板块
  addSector: (sectorName: string) =>
    request('/api/holdings/sector', {
      method: 'POST',
      body: JSON.stringify({ sector_name: sectorName }),
    }),

  // 删除板块
  removeSector: (sectorName: string) =>
    request(`/api/holdings/sector/${sectorName}`, { method: 'DELETE' }),
};

export const initialDataApi = {
  getInitialData: (timeoutMs = 20000) =>
    request<{
      holdings: { sectors: any[]; last_updated: string | null };
      sync_status: 'pending' | 'syncing' | 'ready';
      sync_progress: number;
      sync_message: string;
      sync_error: string | null;
    }>('/api/initial_data', { timeoutMs }),
};

/**
 * 校验股票代码是否有效
 * @param stockCode 股票代码
 * @returns 是否有效
 */
const isValidStockCode = (stockCode: string): boolean => {
  return !!stockCode && !stockCode.startsWith('UNKNOWN_');
};

/**
 * 股票行情 API
 */
export const stocksApi = {
  // 获取实时行情
  getQuote: (stockCode: string) => {
    if (!isValidStockCode(stockCode)) return Promise.reject(new Error(`无效的股票代码: ${stockCode}`));
    return request<any>(`/api/stocks/quote/${stockCode}`);
  },

  // 批量获取行情
  getQuotes: (stockCodes: string[]) => {
    const validCodes = stockCodes.filter(isValidStockCode);
    if (validCodes.length === 0) return Promise.resolve([]);
    return request('/api/stocks/quotes', {
      method: 'POST',
      body: JSON.stringify(validCodes),
      timeoutMs: 20000, // 增加超时到20秒
    });
  },

  // 获取K线数据
  getKline: (stockCode: string, period = 'day', count = 100) => {
    if (!isValidStockCode(stockCode)) return Promise.resolve([]);
    return request<any[]>(`/api/stocks/kline/${stockCode}?period=${period}&count=${count}`);
  },
  
  // 获取分时数据
  getIntraday: (stockCode: string) => {
    if (!isValidStockCode(stockCode)) return Promise.resolve(null);
    return request<any>(`/api/stocks/intraday/${stockCode}`);
  },

  // 获取技术指标
  getTechnical: (stockCode: string) => {
    if (!isValidStockCode(stockCode)) return Promise.resolve(null);
    return request<any>(`/api/stocks/technical/${stockCode}`);
  },

  getPMR: async (stockCode: string, days: number = 120) => {
    // 如果是 UNKNOWN 占位符，直接返回空数据，不请求后端
    if (!isValidStockCode(stockCode)) {
      console.warn(`[API] 跳过获取 PMR 数据: 股票代码无效 (${stockCode})`);
      return {
        dates: [],
        pmr5: [],
        pmr10: [],
        pmr20: [],
        pmr30: [],
        pmr60: [],
      };
    }

    const endpoint = `/api/stocks/pmr/${encodeURIComponent(stockCode)}?days=${days}`;

    try {
      const result = await request<any>(endpoint, { timeoutMs: 30000 });
      // 如果后端返回了带 metadata 的结构，提取 data 部分
      if (result && result.data !== undefined && result.metadata !== undefined) {
        return result.data;
      }
      return result;
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        console.error(`[API] 未找到股票 ${stockCode} 的 PMR 数据 (404)`);
      } else {
        console.error(`[API] 获取 PMR 数据失败:`, error);
      }
      
      return {
        dates: [],
        pmr5: [],
        pmr10: [],
        pmr20: [],
        pmr30: [],
        pmr60: [],
      };
    }
  },

  // 获取Force Index数据
  getForceIndex: async (stockCodeOrName: string, period: string = 'day', count: number = 100) => {
    if (!stockCodeOrName) {
      console.warn('[API] 跳过获取 Force Index 数据: 股票代码或名称为空');
      return null;
    }

    const endpoint = `/api/indicators/force-index/${encodeURIComponent(stockCodeOrName)}?period=${period}&count=${count}&use_cache=true&local_only=true`;

    try {
      const result = await request<any>(endpoint, { timeoutMs: 30000 });
      return result;
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        console.error(`[API] 未找到股票 ${stockCodeOrName} 的 Force Index 数据 (404)`);
      } else {
        console.error(`[API] 获取 Force Index 数据失败:`, error);
      }
      return null;
    }
  },

  // 获取A股主要指数
  getCNIndices: () => request<any>('/api/stocks/cn-indices'),

  // 获取行业指数
  getSectorIndex: (sectorName: string) =>
    request<any>(`/api/stocks/sector-index/${encodeURIComponent(sectorName)}`),
  
  // 获取配置的指数列表
  getIndices: () => request<any>('/api/stocks/indices'),
  
  // 获取指数实时行情
  getIndicesQuotes: () => request<any>('/api/stocks/indices/quotes'),
  
  // 从数据库获取K线数据（优先从数据库）
  getKlineFromDB: (stockCode: string, period = 'day', count = 100, quickLoad = false) => {
    if (!isValidStockCode(stockCode)) {
      return Promise.resolve({
        data: [],
        metadata: {
          stock_code: stockCode,
          period,
          count,
          local_data_available: false,
          is_updating: false,
          needs_update: false,
          quick_load: quickLoad,
          requested_count: count,
          actual_count: 0,
        }
      });
    }
    return request<{
      data: any[];
      metadata: {
        stock_code: string;
        period: string;
        count: number;
        local_data_available: boolean;
        is_updating: boolean;
        last_update?: string;
        needs_update: boolean;
        update_reason?: string;
        quick_load: boolean;
        requested_count: number;
        actual_count: number;
      };
    }>(`/api/stocks/kline-db/${stockCode}?period=${period}&count=${count}&quick_load=${quickLoad}`);
  },
  
  // 更新股票数据到数据库
  updateStockDB: (stockCode: string, period = 'day', forceFull = false) =>
    request<any>(`/api/stocks/update-db/${stockCode}?period=${period}&force_full=${forceFull}`, { method: 'POST' }),
  
  // 获取数据来源状态
  getDataSourceStatus: () =>
    request<{
      success: boolean;
      status: Record<string, {
        data_type: string;
        data_type_name: string;
        stock_code: string | null;
        data_source: string | null;
        read_time: string | null;
        last_update_time: string | null;
        source_location: string | null;
        is_updating: boolean;
      }>;
      timestamp: string;
    }>('/api/stocks/data-source/status'),
};

/**
 * 基本面分析 API
 */
export const fundamentalApi = {
  // 获取基本面分析
  analyze: (stockCode: string) => request<any>(`/api/fundamental/${stockCode}`),

  // 获取估值指标
  getValuation: (stockCode: string) =>
    request<any>(`/api/fundamental/${stockCode}/valuation`),

  // 获取成长性指标
  getGrowth: (stockCode: string) =>
    request<any>(`/api/fundamental/${stockCode}/growth`),

  // 获取财务健康度
  getFinancialHealth: (stockCode: string) =>
    request<any>(`/api/fundamental/${stockCode}/financial-health`),

  // 获取最新年报数据（带metadata）
  getAnnualReport: (stockCode: string) =>
    request<{
      data: any;
      metadata: {
        data_type: string;
        data_type_name: string;
        stock_code: string;
        data_source: string;
        read_time: string;
        last_update_time: string | null;
        source_location: string;
        is_updating: boolean;
      };
    }>(`/api/fundamental/${stockCode}/annual-report`),

  // 获取季度财务数据（带metadata）
  getQuarterlyData: (stockCode: string, years: number = 3) =>
    request<{
      data: any;
      metadata: {
        data_type: string;
        data_type_name: string;
        stock_code: string;
        data_source: string;
        read_time: string;
        last_update_time: string | null;
        source_location: string;
        is_updating: boolean;
        years: number;
      };
    }>(`/api/fundamental/${stockCode}/quarterly?years=${years}`),
};

/**
 * 美股市场 API
 */
export const usMarketApi = {
  // 获取美股指数（带metadata）
  getIndices: () =>
    request<{
      data: any;
      metadata: {
        data_type: string;
        data_type_name: string;
        stock_code: string;
        data_source: string;
        read_time: string;
        last_update_time: string | null;
        source_location: string;
        is_updating: boolean;
        updating_indices: string[];
      };
    }>('/api/us-market/indices'),

  // 获取美股个股数据
  getStock: (symbol: string) => request<any>(`/api/us-market/stock/${symbol}`),

  // 获取相关美股
  getRelatedStocks: (stockCode: string) =>
    request<any>(`/api/us-market/related-stocks/${stockCode}`),

  // 获取美股影响分析
  getAnalysis: async (stockCode: string) => {
    if (!stockCode || stockCode.startsWith('UNKNOWN')) {
      return null;
    }
    try {
      return await request<any>(`/api/us-market/analysis/${stockCode}`, { timeoutMs: 45000 });
    } catch (error) {
      console.warn(`[API] 获取美股联动分析失败: ${stockCode}`, error);
      return null;
    }
  },

  // 获取每日美股报告
  getDailyReport: () => request<any>('/api/us-market/daily-report'),

  // 获取VIX恐慌指数
  getVIX: () => request<any>('/api/us-market/vix'),
};

/**
 * 预测分析 API
 */
export const predictionApi = {
  // 预测单只股票
  predict: async (stockCode: string) => {
    if (!stockCode || stockCode.startsWith('UNKNOWN')) {
      return null;
    }
    try {
      return await request<any>(`/api/predictions/${stockCode}`, { timeoutMs: 45000 });
    } catch (error) {
      console.warn(`[API] 获取个股预测失败: ${stockCode}`, error);
      return null;
    }
  },

  // 预测所有持仓
  predictAll: () => request<any>('/api/predictions/all'),

  // 板块轮动分析
  analyzeSectorRotation: () => request<any>('/api/predictions/sector-rotation'),

  // 技术指标分析
  analyzeTechnical: (stockCode: string) =>
    request<any>(`/api/predictions/${stockCode}/technical`),
};

/**
 * 每日报告 API
 */
export const reportApi = {
  // 获取报告列表
  getList: (params?: { start_date?: string; end_date?: string; stock_code?: string }) => {
    const query = new URLSearchParams(params as any).toString();
    return request<any>(`/api/reports/list${query ? `?${query}` : ''}`);
  },

  // 获取报告详情
  getDetail: (stockCode: string, reportDate: string) =>
    request<any>(`/api/reports/detail/${stockCode}/${reportDate}`),

  // 生成报告
  generate: (data: { stock_code: string; stock_name: string; sector: string; report_date: string }) =>
    request('/api/reports/generate', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // 生成所有报告
  generateAll: () =>
    request('/api/reports/generate-all', { method: 'POST' }),

  // ========== LLM智能评估报告API ==========
  
  // 生成LLM智能评估报告
  generateLLM: (data: { stock_code: string; stock_name: string; days?: number }) =>
    request('/api/reports/llm/generate', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // 获取LLM报告列表
  getLLMList: (stockCode?: string) => {
    const query = stockCode ? `?stock_code=${stockCode}` : '';
    return request<any>(`/api/reports/llm/list${query}`);
  },

  // 获取LLM报告内容
  getLLMContent: (fileName: string) =>
    request<any>(`/api/reports/llm/content/${fileName}`),

  // 导出报告
  export: (stockCode: string, reportDate: string) =>
    request<any>(`/api/reports/export/${stockCode}/${reportDate}`),

  // 验证预测
  verify: (stockCode: string, reportDate: string) =>
    request(`/api/reports/verify/${stockCode}/${reportDate}`, { method: 'POST' }),
};

/**
 * 预警管理 API
 */
export const alertApi = {
  // 获取预警列表
  getList: () => request<any>('/api/alerts/'),

  // 设置预警
  setAlert: (data: {
    stock_code: string;
    stock_name: string;
    alert_type: 'up' | 'down' | 'both';
    threshold: number;
  }) =>
    request('/api/alerts/set', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // 删除预警
  removeAlert: (alertId: string) =>
    request(`/api/alerts/${alertId}`, { method: 'DELETE' }),

  // 获取预警历史
  getHistory: (params?: { stock_code?: string; days?: number }) => {
    const query = new URLSearchParams(params as any).toString();
    return request<any>(`/api/alerts/history${query ? `?${query}` : ''}`);
  },
};

/**
 * 新闻资讯 API
 */
export const newsApi = {
  // 获取股票相关新闻
  getStockNews: (stockCode: string, limit = 20) =>
    request<any>(`/api/news/stock/${stockCode}?limit=${limit}`),

  // 获取板块新闻
  getSectorNews: (sectorName: string, limit = 20) =>
    request<any>(`/api/news/sector/${sectorName}?limit=${limit}`),

  // 获取热门新闻
  getHotNews: (limit = 20) =>
    request<any>(`/api/news/hot?limit=${limit}`),

  // 搜索新闻
  search: (keyword: string, limit = 20) =>
    request<any>(`/api/news/search?keyword=${encodeURIComponent(keyword)}&limit=${limit}`),
};

/**
 * 系统配置 API
 */
export const configApi = {
  // 获取布局配置
  getLayoutConfig: () => request<any>('/api/config/layout'),

  // 更新布局配置
  updateLayoutConfig: (config: {
    left_panel_width: number;
    right_panel_width: number;
    center_panel_min_width: number;
    headbar_height: number;
    statusbar_height: number;
  }) =>
    request('/api/config/layout', {
      method: 'POST',
      body: JSON.stringify(config),
    }),

  // 获取交易时段配置
  getTradingHoursConfig: () => request<TradingHoursConfig>('/api/config/trading-hours'),

  // 更新交易时段配置
  updateTradingHoursConfig: (config: TradingHoursConfig) =>
    request<TradingHoursConfig>('/api/config/trading-hours', {
      method: 'POST',
      body: JSON.stringify(config),
    }),
};

// 交易时段配置类型
export interface TradingHoursConfig {
  morning_session_start: string;
  morning_session_end: string;
  afternoon_session_start: string;
  afternoon_session_end: string;
  trading_days: string;
  price_alert_check_interval: number;
  enable_price_alert_monitoring: boolean;
  auto_stop_after_trigger: boolean;
  market_sentiment_update_interval: number;
}

/**
 * 系统状态 API
 */
export const statusApi = {
  // 获取API连接状态
  getApiStatus: async () => {
    const fallbackPayload = {
      tushare: { status: 'timeout', message: '状态检查暂不可用' },
      alphavantage: { status: 'timeout', message: '状态检查暂不可用' },
      finnhub: { status: 'timeout', message: '状态检查暂不可用' },
      tencent: { status: 'timeout', message: '状态检查暂不可用' },
      timestamp: new Date().toISOString(),
    };
    try {
      return await request<any>('/api-status', { timeoutMs: 45000 });
    } catch {
      try {
        return await request<any>('/api/api-status', { timeoutMs: 45000 });
      } catch {
        return fallbackPayload;
      }
    }
  },
};

/**
 * 市场数据 API（基于 AKShare）
 */
export const marketApi = {
  // ==================== 板块数据 ====================
  // 获取行业板块列表
  getIndustrySectors: () => request<any>('/api/market/industry-sectors'),
  
  // 获取概念板块列表
  getConceptSectors: () => request<any>('/api/market/concept-sectors'),
  
  // 获取板块成分股
  getSectorStocks: (sectorName: string) => 
    request<any>(`/api/market/sector-stocks/${encodeURIComponent(sectorName)}`),
  
  // ==================== 资金流向 ====================
  // 获取个股资金流向
  getFundFlow: (stockCode: string) => 
    request<any>(`/api/market/fund-flow/${stockCode}`),
  
  // 获取板块资金流向
  getSectorFundFlow: (sectorType: string = '行业') => 
    request<any>(`/api/market/sector-fund-flow?sector_type=${encodeURIComponent(sectorType)}`),
  
  // 获取大盘资金流向（市场净流入）
  getMarketFundFlow: (days: number = 20) =>
    request<any>(`/api/market/market-fund-flow?days=${days}`),
  
  // ==================== 龙虎榜 ====================
  // 获取龙虎榜详情
  getLHBDetail: (days: number = 1) => 
    request<any>(`/api/market/lhb-detail?days=${days}`),
  
  // ==================== 市场情绪 ====================
  // 获取市场情绪统计
  getMarketSentiment: () => request<any>('/api/market/market-sentiment'),
  
  // 获取历史市场情绪数据
  getMarketSentimentHistory: (days: number = 30) => 
    request<any>(`/api/market/market-sentiment/history?days=${days}`),
  
  // 获取上证指数历史数据
  getSHIndexHistory: (days: number = 30) => 
    request<any>(`/api/market/index-sh-history?days=${days}`),
  
  // ==================== 港股美股 ====================
  // 获取港股实时行情
  getHKSpot: (limit: number = 100) => 
    request<any>(`/api/market/hk-spot?limit=${limit}`),
  
  // 获取美股实时行情
  getUSSpot: (limit: number = 100) => 
    request<any>(`/api/market/us-spot?limit=${limit}`),
  
  // ==================== 宏观经济 ====================
  // 获取中国 CPI 数据
  getChinaCPI: () => request<any>('/api/market/macro/cpi'),
  
  // 获取中国 GDP 数据
  getChinaGDP: () => request<any>('/api/market/macro/gdp'),
  
  // 获取中国 PMI 数据
  getChinaPMI: () => request<any>('/api/market/macro/pmi'),
  
  // ==================== 北向资金 ====================
  // 获取北向资金流向
  getNorthMoneyFlow: () => request<any>('/api/market/north-money-flow'),
  
  // 获取北向资金持股前十
  getNorthMoneyTop10: () => request<any>('/api/market/north-money-top10'),
  
  // ==================== 机构持仓 ====================
  // 获取机构持仓数据
  getInstitutionHoldings: (stockCode: string) => 
    request<any>(`/api/market/institution-holdings/${stockCode}`),
  
  // ==================== 指数数据 ====================
  // 获取指数 K 线
  getIndexKline: (indexCode: string, period: string = 'day', count: number = 100) => 
    request<any>(`/api/market/index-kline/${indexCode}?period=${period}&count=${count}`),
  
  // ==================== ETF 基金 ====================
  // 获取 ETF 实时行情
  getETFSpot: (limit: number = 100) => 
    request<any>(`/api/market/etf-spot?limit=${limit}`),
};

/**
 * 快速K线 API（优先数据库，后台异步更新）
 */
export const klineFastApi = {
  // 快速获取K线数据（优先数据库）
  getKlineFast: (
    stockCode: string,
    period = 'day',
    count = 100,
    sessionId?: string,
    quickLoad = false,
    localOnly = false,
    timeoutMs = 15000 // 从 10s 增加到 15s
  ) => {
    const params = new URLSearchParams({
      period,
      count: count.toString(),
      quick_load: quickLoad.toString(),
      local_only: localOnly.toString()
    });
    if (sessionId) {
      params.append('session_id', sessionId);
    }
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    return request<{
      data: any[];
      local_data_available: boolean;
      is_updating: boolean;
      task_id: string | null;
      last_update: string | null;
      last_data_date: string | null;
      update_reason: string | null;
      session_id: string;
      quick_load: boolean;
      actual_count: number;
    }>(`/api/stocks/kline-db-fast/${stockCode}?${params.toString()}`, {
      signal: controller.signal
    }).finally(() => {
      clearTimeout(timeoutId);
    });
  },
  
  // 获取K线更新状态
  getKlineStatus: (stockCode: string) =>
    request<{
      stock_code: string;
      needs_update: boolean;
      is_updating: boolean;
      task_ids: string[];
      last_update: string | null;
      reason: string;
    }>(`/api/stocks/kline-status/${stockCode}`),
};

/**
 * 数据更新管理 API
 */
export const dataUpdateApi = {
  // 获取所有股票和指数的更新状态
  getStatusAll: () =>
    request<{
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
    }>('/api/data/status-all', { timeoutMs: 30000 }), // 增加超时到30秒，因为涉及大量数据库检查
  
  // 获取单个股票的更新状态
  getStatus: (stockCode: string) =>
    request<{
      stock_code: string;
      needs_update: boolean;
      last_update: string | null;
      reason: string;
      data_source: string;
    }>(`/api/data/status/${stockCode}`),
  
  // 强制更新（批量）
  forceUpdate: (data: { stock_codes?: string[]; us_indices?: string[]; period?: string; force?: boolean }) =>
    request<{
      success: boolean;
      message: string;
      financial_updated_count?: number;
      kline_submitted_count?: number;
      us_index_submitted_count?: number;
      task_ids?: string[];
    }>('/api/data/force-update', {
      method: 'POST',
      body: JSON.stringify({
        stock_codes: data.stock_codes || [],
        us_indices: data.us_indices || [],
        period: data.period || 'day',
        force: data.force || false
      }),
    }),
  
  // 强制更新（单个）
  forceUpdateSingle: (stockCode: string, period = 'day') =>
    request<{
      success: boolean;
      message: string;
      task_id: string | null;
    }>(`/api/data/force-update/${stockCode}?period=${period}`, { method: 'POST' }),
  
  // 获取所有后台任务
  getTasks: () =>
    request<{
      total_count: number;
      running_count: number;
      tasks: Array<{
        task_id: string;
        status: string;
        stock_code: string;
        data_type: string;
        started_at: string;
        completed_at?: string;
        error?: string;
      }>;
    }>('/api/data/tasks'),
  
  // 获取指定任务状态
  getTaskStatus: (taskId: string) =>
    request<{
      task_id: string;
      status: string;
      stock_code: string;
      data_type: string;
      started_at: string;
      completed_at?: string;
      error?: string;
    }>(`/api/data/tasks/${taskId}`),
  
  // 取消任务
  cancelTask: (taskId: string) =>
    request<{
      success: boolean;
      message: string;
    }>(`/api/data/tasks/${taskId}`, { method: 'DELETE' }),
  
  // 获取更新日志
  getLogs: (params?: { stock_code?: string; data_type?: string; limit?: number }) => {
    const query = new URLSearchParams(params as any).toString();
    return request<{
      total: number;
      logs: Array<{
        id: number;
        stock_code: string;
        data_type: string;
        update_type: string;
        started_at: string;
        completed_at: string | null;
        status: string;
        records_updated: number;
        error_message: string | null;
      }>;
    }>(`/api/data/logs${query ? `?${query}` : ''}`);
  },
  
  // 获取最后更新时间
  getLatestUpdateTime: () =>
    request<{
      last_update: string | null;
      stock_code: string | null;
      data_type: string | null;
    }>('/api/data/logs/latest'),
};

/**
 * 每日关注 API
 */
export const dailyWatchlistApi = {
  // 获取关注列表汇总（按日期分组）
  getSummary: (includeArchived = false, limit = 30) =>
    request<{
      dates: Array<{
        watch_date: string;
        stocks: Array<{
          id: number;
          stock_code: string;
          stock_name: string;
          watch_date: string;
          reason: string | null;
          target_price: number | null;
          change_up_pct: number | null;
          change_down_pct: number | null;
          stop_loss_price: number | null;
          notes: string | null;
          price: number | null;
          change: number | null;
          change_pct: number | null;
          quote_timestamp: string | null;
          quote_is_updating: boolean;
          is_archived: boolean;
          archived_at: string | null;
          created_at: string;
          updated_at: string;
        }>;
        total_count: number;
      }>;
      total_dates: number;
      total_stocks: number;
    }>(`/api/daily-watchlist/summary?include_archived=${includeArchived}&limit=${limit}`),

  // 获取所有日期
  getDates: (includeArchived = false) =>
    request<{ dates: string[] }>(`/api/daily-watchlist/dates?include_archived=${includeArchived}`),

  // 获取某日关注列表
  getByDate: (watchDate: string, includeArchived = false) =>
    request<Array<{
      id: number;
      stock_code: string;
      stock_name: string;
      watch_date: string;
      reason: string | null;
      target_price: number | null;
      stop_loss_price: number | null;
      notes: string | null;
      price: number | null;
      change: number | null;
      change_pct: number | null;
      quote_timestamp: string | null;
      quote_is_updating: boolean;
      is_archived: boolean;
      archived_at: string | null;
      created_at: string;
      updated_at: string;
    }>>(`/api/daily-watchlist/${watchDate}?include_archived=${includeArchived}`),

  // 获取单只股票详情
  getStock: (stockId: number) =>
    request<{
      id: number;
      stock_code: string;
      stock_name: string;
      watch_date: string;
      reason: string | null;
      target_price: number | null;
      stop_loss_price: number | null;
      notes: string | null;
      price: number | null;
      change: number | null;
      change_pct: number | null;
      quote_timestamp: string | null;
      quote_is_updating: boolean;
      is_archived: boolean;
      archived_at: string | null;
      created_at: string;
      updated_at: string;
    }>(`/api/daily-watchlist/stock/${stockId}`),

  // 添加股票到关注列表
  addStock: (data: {
    stock_name: string;
    stock_code?: string;
    watch_date: string;
    reason?: string;
    target_price?: number;
    change_up_pct?: number;
    change_down_pct?: number;
    stop_loss_price?: number;
    notes?: string;
  }) =>
    request('/api/daily-watchlist/stock', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // 更新关注股票
  updateStock: (stockId: number, data: {
    reason?: string;
    target_price?: number;
    change_up_pct?: number;
    change_down_pct?: number;
    stop_loss_price?: number;
    notes?: string;
  }) =>
    request('/api/daily-watchlist/stock/' + stockId, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  // 删除关注股票
  deleteStocks: (data: { stock_ids?: number[]; watch_date?: string }) =>
    request('/api/daily-watchlist/stock', {
      method: 'DELETE',
      body: JSON.stringify(data),
    }),

  // 归档关注股票
  archiveStocks: (data: { stock_ids?: number[]; watch_date?: string }) =>
    request('/api/daily-watchlist/archive', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // 取消归档
  unarchiveStocks: (stockIds: number[]) =>
    request('/api/daily-watchlist/unarchive', {
      method: 'POST',
      body: JSON.stringify({ stock_ids: stockIds }),
    }),
};

/**
 * 飞书对话 API
 */
export const feishuChatApi = {
  // 获取对话历史
  getHistory: (chatId?: string, limit = 50, offset = 0) => {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    if (chatId) {
      params.append('chat_id', chatId);
    }
    return request<{
      messages: Array<{
        id: number;
        message_id: string;
        sender_id: string | null;
        sender_name: string | null;
        sender_type: string;
        message_type: string;
        content: string;
        send_time: string;
        reply_to_id: string | null;
      }>;
      total: number;
      has_more: boolean;
    }>(`/api/feishu-chat/history?${params.toString()}`);
  },

  // 获取最近消息
  getRecent: (limit = 20) =>
    request<Array<{
      id: number;
      message_id: string;
      sender_id: string | null;
      sender_name: string | null;
      sender_type: string;
      message_type: string;
      content: string;
      send_time: string;
      reply_to_id: string | null;
    }>>(`/api/feishu-chat/recent?limit=${limit}`),

  // 发送消息到最近的对话
  sendMessage: (message: string) =>
    request<{ status: string; message: string; chat_id?: string }>(
      '/api/feishu/send-to-recent-chat',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      }
    ),

  clearHistory: () =>
    request<{ status: string; deleted_rows: number; deleted_files: number }>(
      '/api/feishu-chat/clear',
      {
        method: 'POST',
      }
    ),

  // 推送事件卡片（如：STOCK_RESEARCH_START）
  pushEvent: (eventId: string) =>
    request<{ status: string; message: string; event_id: string; chat_id: string }>(
      `/api/feishu/push-event/${eventId}`,
      {
        method: 'POST',
      }
    ),
};

/**
 * Settings API
 */
export const settingsApi = {
  // 获取交易时段配置
  getTradingHours: () =>
    request<{
      morning_session_start: string;
      morning_session_end: string;
      afternoon_session_start: string;
      afternoon_session_end: string;
      trading_days: string;
      trading_days_list: number[];
      price_alert_check_interval: number;
      enable_price_alert_monitoring: boolean;
      auto_stop_after_trigger: boolean;
      market_sentiment_update_interval: number;
    }>('/api/settings/trading-hours'),

  // 更新交易时段配置
  updateTradingHours: (config: {
    morning_session_start: string;
    morning_session_end: string;
    afternoon_session_start: string;
    afternoon_session_end: string;
    trading_days: string;
    price_alert_check_interval: number;
    enable_price_alert_monitoring: boolean;
    auto_stop_after_trigger: boolean;
    market_sentiment_update_interval: number;
  }) =>
    request<{
      morning_session_start: string;
      morning_session_end: string;
      afternoon_session_start: string;
      afternoon_session_end: string;
      trading_days: string;
      trading_days_list: number[];
      price_alert_check_interval: number;
      enable_price_alert_monitoring: boolean;
      auto_stop_after_trigger: boolean;
      market_sentiment_update_interval: number;
    }>('/api/settings/trading-hours', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    }),

  // 重新加载配置
  reloadTradingHours: () =>
    request<{ status: string; message: string }>('/api/settings/trading-hours/reload', {
      method: 'POST',
    }),
};

