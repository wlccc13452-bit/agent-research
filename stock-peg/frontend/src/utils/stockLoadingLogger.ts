/**
 * 股票加载过程日志跟踪器（前端）
 * 
 * 用于记录股票切换时前端的加载过程，分析性能瓶颈
 */

class StockLoadingLoggerFrontend {
  private activeSessions: Map<string, {
    stockCode: string;
    source: string;
    startTime: number;
    events: Array<{
      timestamp: string;
      eventType: string;
      location: string;
      data?: any;
      durationMs?: number;
      elapsedMs: number;
    }>;
  }> = new Map();

  /**
   * 开始一个新的加载跟踪会话
   */
  startSession(stockCode: string, source: string = 'unknown'): string {
    // 强制校验代码有效性
    if (!stockCode || stockCode.startsWith('UNKNOWN')) {
      console.warn(`[StockLoadingLogger] 拒绝为无效代码开始会话: ${stockCode} (来源: ${source})`);
      return `invalid_${Date.now()}`;
    }

    const sessionId = `${stockCode}_${Date.now()}`;
    
    this.activeSessions.set(sessionId, {
      stockCode,
      source,
      startTime: Date.now(),
      events: []
    });

    this.logEvent(sessionId, 'frontend_session_start', 'frontend', {
      stockCode,
      source
    });

    console.log(`[${sessionId}] 🚀 开始跟踪股票加载: ${stockCode} (来源: ${source})`);
    return sessionId;
  }

  /**
   * 记录一个事件
   */
  logEvent(
    sessionId: string,
    eventType: string,
    location: string = 'frontend',
    data?: any,
    durationMs?: number
  ) {
    const session = this.activeSessions.get(sessionId);
    if (!session) {
      console.warn(`[${sessionId}] 会话不存在，跳过事件: ${eventType}`);
      return;
    }

    const now = Date.now();
    const elapsedMs = now - session.startTime;

    const event = {
      timestamp: new Date().toISOString(),
      eventType,
      location,
      data,
      durationMs,
      elapsedMs
    };

    session.events.push(event);

    // 简化日志输出
    const durationStr = durationMs ? ` [${durationMs.toFixed(1)}ms]` : '';
    const emoji = this.getEventEmoji(eventType);
    console.log(
      `[${sessionId}] ${emoji} [${location}] ${eventType}${durationStr} @${elapsedMs.toFixed(1)}ms`,
      data || ''
    );
  }

  /**
   * 结束会话并输出总结
   */
  endSession(sessionId: string, success: boolean = true, error?: string) {
    const session = this.activeSessions.get(sessionId);
    if (!session) {
      console.warn(`[${sessionId}] 会话不存在，无法结束`);
      return;
    }

    const totalDurationMs = Date.now() - session.startTime;

    // 记录结束事件
    this.logEvent(sessionId, 'frontend_session_end', 'frontend', {
      success,
      error,
      totalEvents: session.events.length
    }, totalDurationMs);

    // 输出性能总结
    console.log(`\n[${sessionId}] 📊 会话总结:`);
    console.log(`  股票代码: ${session.stockCode}`);
    console.log(`  总耗时: ${totalDurationMs.toFixed(2)}ms`);
    console.log(`  事件数: ${session.events.length}`);
    console.log(`  状态: ${success ? '✅ 成功' : '❌ 失败'}`);
    
    if (error) {
      console.log(`  错误: ${error}`);
    }

    // 性能分析
    const analysis = this.analyzePerformance(session.events);
    console.log(`\n  性能分析:`);
    analysis.forEach(line => console.log(`    ${line}`));

    // 清理会话
    this.activeSessions.delete(sessionId);
  }

  /**
   * 分析性能瓶颈
   */
  private analyzePerformance(events: any[]): string[] {
    const analysis: string[] = [];

    // 按位置分组统计耗时
    const locationStats = new Map<string, { count: number; totalMs: number }>();
    
    events.forEach(event => {
      if (event.durationMs) {
        const stats = locationStats.get(event.location) || { count: 0, totalMs: 0 };
        stats.count++;
        stats.totalMs += event.durationMs;
        locationStats.set(event.location, stats);
      }
    });

    // 找出耗时最长的事件
    const longestEvents = events
      .filter(e => e.durationMs)
      .sort((a, b) => b.durationMs - a.durationMs)
      .slice(0, 5);

    if (locationStats.size > 0) {
      analysis.push('各位置总耗时:');
      locationStats.forEach((stats, location) => {
        analysis.push(`  ${location}: ${stats.count}次调用, 总计 ${stats.totalMs.toFixed(2)}ms`);
      });
    }

    if (longestEvents.length > 0) {
      analysis.push('\n耗时最长的5个事件:');
      longestEvents.forEach((event, i) => {
        analysis.push(
          `  ${i + 1}. ${event.eventType} (${event.location}): ` +
          `${event.durationMs.toFixed(2)}ms @${event.elapsedMs.toFixed(2)}ms`
        );
      });
    }

    // 性能建议
    if (longestEvents.length > 0 && longestEvents[0].durationMs > 500) {
      const slowest = longestEvents[0];
      analysis.push(`\n⚠️  主要瓶颈: ${slowest.eventType} 耗时 ${slowest.durationMs.toFixed(2)}ms`);
    }

    return analysis;
  }

  /**
   * 获取事件的emoji图标
   */
  private getEventEmoji(eventType: string): string {
    if (eventType.includes('start')) return '🚀';
    if (eventType.includes('end')) return '🏁';
    if (eventType.includes('request')) return '📤';
    if (eventType.includes('response')) return '📥';
    if (eventType.includes('render')) return '🎨';
    if (eventType.includes('error')) return '❌';
    if (eventType.includes('click')) return '👆';
    if (eventType.includes('update')) return '🔄';
    return '📍';
  }

  /**
   * 获取所有活跃会话
   */
  getActiveSessions() {
    const result: any = {};
    this.activeSessions.forEach((session, sessionId) => {
      result[sessionId] = {
        stockCode: session.stockCode,
        elapsedMs: Date.now() - session.startTime,
        eventsCount: session.events.length
      };
    });
    return result;
  }
}

// 单例实例
export const stockLoadingLogger = new StockLoadingLoggerFrontend();
