/**
 * K线快速加载测试 - 模拟客户端读取逻辑
 * 
 * 功能：
 * 1. 从后端API获取自持股票列表
 * 2. 测试所有自持股票的K线快速加载
 * 3. 验证本地数据可用性
 * 4. 统计加载性能和成功率
 */

// ==================== 类型定义 ====================

interface StockInfo {
  code: string;
  name: string;
  sector: string;
}

interface SectorInfo {
  name: string;
  stocks: StockInfo[];
}

interface Holdings {
  sectors: SectorInfo[];
  last_updated: string;
}

interface KlineFastResponse {
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
}

interface TestResult {
  stockCode: string;
  stockName: string;
  sector: string;
  success: boolean;
  localDataAvailable: boolean;
  dataCount: number;
  firstDate: string | null;
  lastDate: string | null;
  loadTime: number;
  error?: string;
}

interface TestSummary {
  totalStocks: number;
  successCount: number;
  failedCount: number;
  localDataAvailableCount: number;
  totalLoadTime: number;
  avgLoadTime: number;
  results: TestResult[];
}

// ==================== API 客户端 ====================

class APIClient {
  private baseUrl: string;
  private timeout: number;

  constructor(baseUrl: string = 'http://localhost:8000', timeout: number = 5000) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
    this.timeout = timeout;
  }

  /**
   * 通用请求方法（模拟前端 api.ts 中的 request 函数）
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(`HTTP ${response.status} ${response.statusText}: ${text}`);
      }

      return await response.json();
    } finally {
      clearTimeout(timeoutId);
    }
  }

  /**
   * 获取持仓列表（模拟前端 holdingsApi.getHoldings）
   */
  async getHoldings(): Promise<Holdings> {
    return this.request<Holdings>('/api/holdings/');
  }

  /**
   * 快速加载K线数据（模拟前端 klineFastApi.getKlineFast）
   */
  async getKlineFast(
    stockCode: string,
    options: {
      period?: string;
      count?: number;
      quickLoad?: boolean;
      localOnly?: boolean;
      sessionId?: string;
    } = {}
  ): Promise<KlineFastResponse> {
    const {
      period = 'day',
      count = 100,
      quickLoad = true,
      localOnly = true,
      sessionId = `test-${Date.now()}`,
    } = options;

    const params = new URLSearchParams({
      period,
      count: String(count),
      quick_load: String(quickLoad),
      local_only: String(localOnly),
      session_id: sessionId,
    });

    return this.request<KlineFastResponse>(
      `/api/stocks/kline-db-fast/${stockCode}?${params.toString()}`
    );
  }
}

// ==================== 测试逻辑 ====================

class KlineFastLoadTester {
  private client: APIClient;
  private results: TestResult[] = [];

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.client = new APIClient(baseUrl);
  }

  /**
   * 测试单个股票的K线快速加载
   */
  async testSingleStock(stock: StockInfo): Promise<TestResult> {
    const startTime = Date.now();
    
    try {
      console.log(`📊 测试股票: ${stock.name} (${stock.code})`);
      
      const response = await this.client.getKlineFast(stock.code, {
        period: 'day',
        count: 100,
        quickLoad: true,
        localOnly: true,
      });

      const loadTime = Date.now() - startTime;

      // 提取首尾日期
      const data = response.data || [];
      const firstDate = data.length > 0 ? data[0]?.date : null;
      const lastDate = data.length > 0 ? data[data.length - 1]?.date : null;

      const result: TestResult = {
        stockCode: stock.code,
        stockName: stock.name,
        sector: stock.sector,
        success: true,
        localDataAvailable: response.local_data_available,
        dataCount: data.length,
        firstDate,
        lastDate,
        loadTime,
      };

      console.log(`  ✅ 成功: 数据量=${data.length}, 本地可用=${response.local_data_available}, 耗时=${loadTime}ms`);
      
      return result;
    } catch (error: any) {
      const loadTime = Date.now() - startTime;
      
      const result: TestResult = {
        stockCode: stock.code,
        stockName: stock.name,
        sector: stock.sector,
        success: false,
        localDataAvailable: false,
        dataCount: 0,
        firstDate: null,
        lastDate: null,
        loadTime,
        error: error?.message || String(error),
      };

      console.error(`  ❌ 失败: ${error?.message || error}`);
      
      return result;
    }
  }

  /**
   * 测试所有自持股票
   */
  async testAllHoldings(): Promise<TestSummary> {
    console.log('🚀 开始测试自持股票K线快速加载...\n');

    const startTime = Date.now();

    // 1. 获取自持股票列表
    console.log('📥 获取自持股票列表...');
    let holdings: Holdings;
    
    try {
      holdings = await this.client.getHoldings();
      console.log(`✅ 获取成功: ${holdings.sectors.length} 个板块\n`);
    } catch (error: any) {
      console.error(`❌ 获取自持股票列表失败: ${error?.message || error}`);
      throw error;
    }

    // 2. 提取所有股票代码
    const allStocks: StockInfo[] = [];
    for (const sector of holdings.sectors) {
      for (const stock of sector.stocks) {
        allStocks.push({
          code: stock.code,
          name: stock.name,
          sector: sector.name,
        });
      }
    }

    console.log(`📋 共 ${allStocks.length} 只自持股票\n`);
    console.log('─'.repeat(80));

    // 3. 逐个测试（并行可能导致服务端压力过大，使用串行）
    for (const stock of allStocks) {
      const result = await this.testSingleStock(stock);
      this.results.push(result);
      await this.sleep(100); // 避免请求过快
    }

    console.log('─'.repeat(80));
    console.log();

    // 4. 统计结果
    const totalLoadTime = Date.now() - startTime;
    const summary: TestSummary = {
      totalStocks: allStocks.length,
      successCount: this.results.filter(r => r.success).length,
      failedCount: this.results.filter(r => !r.success).length,
      localDataAvailableCount: this.results.filter(r => r.localDataAvailable).length,
      totalLoadTime,
      avgLoadTime: this.results.length > 0 
        ? this.results.reduce((sum, r) => sum + r.loadTime, 0) / this.results.length 
        : 0,
      results: this.results,
    };

    return summary;
  }

  /**
   * 打印测试报告
   */
  printReport(summary: TestSummary): void {
    console.log('📊 测试报告');
    console.log('═'.repeat(80));
    console.log();
    
    // 总体统计
    console.log('📈 总体统计:');
    console.log(`  总股票数: ${summary.totalStocks}`);
    console.log(`  成功加载: ${summary.successCount} (${this.percent(summary.successCount, summary.totalStocks)}%)`);
    console.log(`  失败数量: ${summary.failedCount} (${this.percent(summary.failedCount, summary.totalStocks)}%)`);
    console.log(`  本地数据可用: ${summary.localDataAvailableCount} (${this.percent(summary.localDataAvailableCount, summary.totalStocks)}%)`);
    console.log(`  总耗时: ${summary.totalLoadTime}ms`);
    console.log(`  平均耗时: ${summary.avgLoadTime.toFixed(2)}ms`);
    console.log();

    // 失败详情
    if (summary.failedCount > 0) {
      console.log('❌ 失败详情:');
      for (const result of summary.results.filter(r => !r.success)) {
        console.log(`  ${result.stockName} (${result.stockCode}) - ${result.sector}`);
        console.log(`    错误: ${result.error}`);
      }
      console.log();
    }

    // 本地数据不可用详情
    const noLocalData = summary.results.filter(r => r.success && !r.localDataAvailable);
    if (noLocalData.length > 0) {
      console.log('⚠️  本地数据不可用:');
      for (const result of noLocalData) {
        console.log(`  ${result.stockName} (${result.stockCode}) - ${result.sector}`);
      }
      console.log();
    }

    // 成功详情
    const successResults = summary.results.filter(r => r.success);
    if (successResults.length > 0) {
      console.log('✅ 成功加载详情:');
      for (const result of successResults) {
        console.log(`  ${result.stockName} (${result.stockCode}) - ${result.sector}`);
        console.log(`    数据量: ${result.dataCount}条, 日期范围: ${result.firstDate || 'N/A'} ~ ${result.lastDate || 'N/A'}`);
        console.log(`    本地可用: ${result.localDataAvailable ? '是' : '否'}, 耗时: ${result.loadTime}ms`);
      }
      console.log();
    }

    console.log('═'.repeat(80));
  }

  private percent(part: number, total: number): string {
    if (total === 0) return '0.00';
    return ((part / total) * 100).toFixed(2);
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// ==================== 主程序 ====================

async function main() {
  // 解析命令行参数
  const args = process.argv.slice(2);
  const baseUrl = args.find(arg => arg.startsWith('--base='))?.split('=')[1] || 'http://localhost:8000';

  console.log('🔧 配置信息:');
  console.log(`  后端地址: ${baseUrl}`);
  console.log();

  try {
    // 创建测试器
    const tester = new KlineFastLoadTester(baseUrl);

    // 运行测试
    const summary = await tester.testAllHoldings();

    // 打印报告
    tester.printReport(summary);

    // 根据结果设置退出码
    if (summary.failedCount > 0) {
      process.exitCode = 1;
    }
  } catch (error: any) {
    console.error('💥 测试过程出错:', error?.message || error);
    process.exitCode = 1;
  }
}

// 执行主程序
main();
