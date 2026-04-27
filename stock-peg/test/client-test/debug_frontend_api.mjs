/**
 * 前端API调试工具
 * 
 * 用于检查前端实际调用的API和数据格式
 */

const BASE_URL = process.argv[2] || 'http://localhost:8000';

console.log('🔧 前端API调试工具');
console.log('后端地址:', BASE_URL);
console.log();

// 测试前端实际调用的API
async function testFrontendAPI() {
  try {
    // 1. 测试获取持仓列表
    console.log('📥 [1/3] 测试获取持仓列表...');
    const holdingsResponse = await fetch(`${BASE_URL}/api/holdings/`);
    if (!holdingsResponse.ok) {
      throw new Error(`HTTP ${holdingsResponse.status}`);
    }
    const holdings = await holdingsResponse.json();
    console.log('✅ 持仓列表获取成功');
    console.log(`   板块数: ${holdings.sectors?.length || 0}`);
    
    // 获取第一只股票代码
    const firstStock = holdings.sectors?.[0]?.stocks?.[0];
    if (!firstStock) {
      console.log('❌ 没有找到股票');
      return;
    }
    console.log(`   测试股票: ${firstStock.name} (${firstStock.code})\n`);

    // 2. 测试前端调用的K线API（kline-db）
    console.log('📊 [2/3] 测试前端K线API (kline-db)...');
    const klineDbUrl = `${BASE_URL}/api/stocks/kline-db/${firstStock.code}?period=day&count=60&quick_load=true`;
    console.log('   请求URL:', klineDbUrl);
    
    const klineDbResponse = await fetch(klineDbUrl);
    if (!klineDbResponse.ok) {
      throw new Error(`HTTP ${klineDbResponse.status}`);
    }
    const klineDbData = await klineDbResponse.json();
    
    console.log('✅ K线数据获取成功 (kline-db)');
    console.log('   数据结构:');
    console.log('   - data存在:', 'data' in klineDbData);
    console.log('   - metadata存在:', 'metadata' in klineDbData);
    console.log('   - data长度:', klineDbData.data?.length || 0);
    console.log('   - local_data_available:', klineDbData.metadata?.local_data_available);
    console.log('   - is_updating:', klineDbData.metadata?.is_updating);
    
    if (klineDbData.data && klineDbData.data.length > 0) {
      console.log('   - 第一条数据:', klineDbData.data[0]);
      console.log('   - 最后一条数据:', klineDbData.data[klineDbData.data.length - 1]);
    }
    console.log();

    // 3. 检查前端如何处理数据
    console.log('🔍 [3/3] 检查前端数据处理逻辑...');
    const response = klineDbData;
    const klines = response.data || response;
    
    console.log('   前端处理后的数据:');
    console.log('   - klines类型:', Array.isArray(klines) ? '数组' : typeof klines);
    console.log('   - klines长度:', klines?.length || 0);
    
    if (klines && klines.length > 0) {
      console.log('   - 第一条K线:', {
        date: klines[0].date,
        open: klines[0].open,
        close: klines[0].close
      });
      console.log('   ✅ 数据格式正确，前端应该能正常显示');
    } else {
      console.log('   ❌ 数据为空，前端会显示"暂无K线数据"');
    }
    console.log();

    // 4. 完整测试报告
    console.log('📋 测试报告:');
    console.log('═'.repeat(60));
    if (klines && klines.length > 0) {
      console.log('✅ API正常工作');
      console.log('✅ 数据格式正确');
      console.log('✅ 本地数据可用');
      console.log();
      console.log('如果前端仍显示"暂无K线数据"，可能的原因:');
      console.log('1. React Query缓存问题 - 刷新页面或清除缓存');
      console.log('2. 前端路由问题 - 检查是否正确加载股票代码');
      console.log('3. 前端状态管理问题 - 检查loading状态');
      console.log('4. 浏览器控制台错误 - 打开开发者工具查看');
    } else {
      console.log('❌ 数据为空');
      console.log('可能的原因:');
      console.log('1. 数据库无数据 - 需要先更新K线数据');
      console.log('2. 股票代码错误 - 检查股票代码是否正确');
      console.log('3. 后端服务问题 - 检查后端日志');
    }
    console.log('═'.repeat(60));

  } catch (error) {
    console.error('❌ 测试失败:', error.message);
    console.log();
    console.log('排查建议:');
    console.log('1. 检查后端服务是否启动');
    console.log('2. 检查端口是否正确（默认8000）');
    console.log('3. 检查网络连接');
    console.log('4. 查看后端日志');
  }
}

testFrontendAPI();
