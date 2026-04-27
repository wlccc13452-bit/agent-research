/**
 * 客户端日志服务
 * 记录加载过程和数据读取过程，通过WebSocket发送到后端
 */

export type LogLevel = 'debug' | 'info' | 'warning' | 'error';
export type LogCategory = 'loading' | 'api' | 'websocket' | 'cache' | 'performance' | 'error';

export interface ClientLogEntry {
  id: string;
  timestamp: string;
  level: LogLevel;
  category: LogCategory;
  message: string;
  details?: any;
  duration?: number; // 毫秒
  stockCode?: string;
  userId?: string;
  sessionId: string;
  userAgent: string;
  url: string;
}

class ClientLogger {
  private sessionId: string;
  private ws: WebSocket | null = null;
  private logQueue: ClientLogEntry[] = [];
  private flushInterval: ReturnType<typeof setInterval> | null = null;
  private readonly MAX_QUEUE_SIZE = 50;
  private readonly FLUSH_INTERVAL = 2000; // 2秒批量发送一次
  private lastWsWarningAt = 0;
  private readonly WS_WARNING_INTERVAL = 15000;

  constructor() {
    this.sessionId = this.generateSessionId();
    this.startFlushInterval();
    
    // 监听WebSocket连接状态
    window.addEventListener('websocket-connected', () => {
      this.flush(); // 连接后立即发送队列中的日志
    });

    window.addEventListener('pagehide', () => {
      this.info('loading', '客户端会话结束', {
        sessionId: this.sessionId,
        remainingQueue: this.logQueue.length,
      });
      this.flush();
    });

    this.info('loading', '客户端会话启动', {
      sessionId: this.sessionId,
      url: window.location.href,
    });
  }

  private generateSessionId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private generateId(): string {
    return `${this.sessionId}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * 设置WebSocket连接
   */
  setWebSocket(ws: WebSocket | null, isConnected: boolean) {
    this.ws = ws;
    
    if (isConnected && this.logQueue.length > 0) {
      this.lastWsWarningAt = 0;
      this.flush();
    }
  }

  /**
   * 记录日志
   */
  log(
    level: LogLevel,
    category: LogCategory,
    message: string,
    details?: any,
    duration?: number,
    stockCode?: string
  ): string {
    const entry: ClientLogEntry = {
      id: this.generateId(),
      timestamp: new Date().toISOString(),
      level,
      category,
      message,
      details: details ? this.sanitizeDetails(details) : undefined,
      duration,
      stockCode,
      sessionId: this.sessionId,
      userAgent: navigator.userAgent,
      url: window.location.href,
    };

    // 同时输出到浏览器控制台
    this.logToConsole(entry);

    // 添加到队列
    this.logQueue.push(entry);

    // 如果队列满了，立即发送
    if (this.logQueue.length >= this.MAX_QUEUE_SIZE) {
      this.flush();
    }

    return entry.id;
  }

  /**
   * 清理详细信息，避免循环引用和敏感数据
   */
  private sanitizeDetails(details: any): any {
    try {
      // 简单的清理：只保留基本类型和第一层对象
      if (typeof details !== 'object' || details === null) {
        return details;
      }

      const sanitized: any = {};
      for (const key in details) {
        if (details.hasOwnProperty(key)) {
          const value = details[key];
          if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
            sanitized[key] = value;
          } else if (value === null) {
            sanitized[key] = null;
          } else if (Array.isArray(value)) {
            sanitized[key] = `[Array(${value.length})]`;
          } else if (typeof value === 'object') {
            sanitized[key] = '[Object]';
          }
        }
      }
      return sanitized;
    } catch (error) {
      return '[Unable to sanitize]';
    }
  }

  /**
   * 输出到浏览器控制台
   */
  private logToConsole(entry: ClientLogEntry) {
    const prefix = `[${entry.category.toUpperCase()}]`;
    const stockPrefix = entry.stockCode ? ` [${entry.stockCode}]` : '';
    const durationSuffix = entry.duration ? ` (${entry.duration}ms)` : '';
    
    const fullMessage = `${prefix}${stockPrefix} ${entry.message}${durationSuffix}`;
    
    switch (entry.level) {
      case 'error':
        console.error(fullMessage, entry.details || '');
        break;
      case 'warning':
        console.warn(fullMessage, entry.details || '');
        break;
      case 'debug':
        console.debug(fullMessage, entry.details || '');
        break;
      default:
        console.log(fullMessage, entry.details || '');
    }
  }

  /**
   * 批量发送日志到后端
   */
  private flush() {
    // 如果没有日志，直接返回
    if (this.logQueue.length === 0) {
      return;
    }

    // 检查 WebSocket 实际状态（不仅仅是 isConnected 标志）
    // 关键修复：避免在 CLOSING/CLOSED 状态调用 send() 导致错误
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      const now = Date.now();
      if (now - this.lastWsWarningAt >= this.WS_WARNING_INTERVAL) {
        this.lastWsWarningAt = now;
        console.log(`⚠️ WebSocket未连接(readyState=${this.ws?.readyState})，${this.logQueue.length} 条客户端日志暂存在队列中`);
      }
      return;
    }

    const logs = [...this.logQueue];
    try {
      this.logQueue = [];

      this.ws.send(JSON.stringify({
        action: 'client_log',
        logs: logs,
        timestamp: new Date().toISOString(),
      }));

      console.log(`📤 已发送 ${logs.length} 条客户端日志到服务器`);
    } catch (error) {
      console.error('发送客户端日志失败:', error);
      // 发送失败，把日志放回队列
      this.logQueue.unshift(...logs);
    }
  }

  /**
   * 启动定时刷新
   */
  private startFlushInterval() {
    this.flushInterval = setInterval(() => {
      this.flush();
    }, this.FLUSH_INTERVAL);
  }

  /**
   * 停止定时刷新
   */
  stopFlushInterval() {
    if (this.flushInterval) {
      clearInterval(this.flushInterval);
      this.flushInterval = null;
    }
  }

  // ==================== 便捷方法 ====================

  debug(category: LogCategory, message: string, details?: any, duration?: number, stockCode?: string) {
    return this.log('debug', category, message, details, duration, stockCode);
  }

  info(category: LogCategory, message: string, details?: any, duration?: number, stockCode?: string) {
    return this.log('info', category, message, details, duration, stockCode);
  }

  warning(category: LogCategory, message: string, details?: any, duration?: number, stockCode?: string) {
    return this.log('warning', category, message, details, duration, stockCode);
  }

  error(category: LogCategory, message: string, details?: any, duration?: number, stockCode?: string) {
    return this.log('error', category, message, details, duration, stockCode);
  }

  /**
   * 记录API请求
   */
  logApiRequest(url: string, method: string, params?: any, stockCode?: string): string {
    return this.info('api', `发起API请求: ${method} ${url}`, { method, url, params }, undefined, stockCode);
  }

  /**
   * 记录API响应
   */
  logApiResponse(url: string, duration: number, success: boolean, dataSize?: number, stockCode?: string) {
    const level = success ? 'info' : 'error';
    const message = success 
      ? `API请求成功: ${url} (${duration}ms${dataSize ? `, ${dataSize} bytes` : ''})`
      : `API请求失败: ${url} (${duration}ms)`;
    
    return this.log(level, 'api', message, { success, dataSize }, duration, stockCode);
  }

  /**
   * 记录加载阶段开始
   */
  logLoadingStart(stage: string, stockCode?: string): string {
    return this.info('loading', `开始: ${stage}`, { stage }, undefined, stockCode);
  }

  /**
   * 记录加载阶段完成
   */
  logLoadingComplete(stage: string, duration: number, success: boolean, stockCode?: string, details?: any) {
    const level = success ? 'info' : 'error';
    const message = success 
      ? `完成: ${stage} (${duration}ms)`
      : `失败: ${stage} (${duration}ms)`;
    
    return this.log(level, 'loading', message, { stage, success, ...details }, duration, stockCode);
  }

  /**
   * 记录性能指标
   */
  logPerformance(metric: string, value: number, unit: string = 'ms', stockCode?: string) {
    return this.info('performance', `性能指标: ${metric} = ${value}${unit}`, { metric, value, unit }, undefined, stockCode);
  }

  /**
   * 获取会话ID
   */
  getSessionId(): string {
    return this.sessionId;
  }

  /**
   * 手动刷新日志
   */
  manualFlush() {
    this.flush();
  }
}

// 单例实例
export const clientLogger = new ClientLogger();
