// ============================================
// 前端诊断脚本 - 在浏览器控制台(F12)运行
// ============================================

console.log('\n========================================');
console.log('飞书消息前端诊断工具');
console.log('========================================\n');

// 1. 检查WebSocket连接状态
console.log('[1] WebSocket连接状态:');
console.log('  __stockPegWsConnected:', window.__stockPegWsConnected);

// 2. 设置消息监听器
console.log('\n[2] 设置消息监听器...');

let messageCount = 0;
let feishuCount = 0;

// 监听通用WebSocket消息
window.addEventListener('websocket-message', function handler(e) {
    const msg = e.detail;
    messageCount++;
    console.log(`\n[WS消息 #${messageCount}] type:`, msg.type);
    if (msg.type && msg.type.includes('feishu')) {
        console.log('  >> 这是飞书消息！');
        console.log('  >> data:', JSON.stringify(msg.data, null, 2).substring(0, 200));
    }
});

// 监听飞书专用事件
window.addEventListener('feishu-chat-message-received', function handler(e) {
    feishuCount++;
    console.log(`\n[飞书事件 #${feishuCount}] 接收到飞书消息:`);
    console.log('  data:', JSON.stringify(e.detail, null, 2).substring(0, 200));
});

console.log('  监听器已设置');

// 3. 测试广播
console.log('\n[3] 测试广播...');
fetch('http://localhost:8000/api/feishu/test-broadcast', {method: 'POST'})
  .then(r => r.json())
  .then(d => {
      console.log('  广播响应:', d);
      console.log('  如果上面的消息计数增加，说明WebSocket工作正常');
  });

// 4. 检查React Query
console.log('\n[4] React Query状态:');
console.log('  可用:', typeof window.__REACT_QUERY_DEVTOOLS_GLOBAL_HOOK__ !== 'undefined');

// 5. 手动刷新对话
console.log('\n[5] 手动刷新对话API...');
fetch('http://localhost:8000/api/feishu-chat/recent?limit=3')
  .then(r => r.json())
  .then(d => {
      console.log('  对话记录:', d.length, '条');
      d.forEach((m, i) => {
          console.log(`  [${i+1}] ${m.sender_type}: ${m.content.substring(0, 30)}...`);
      });
  });

// 6. 使用说明
console.log('\n========================================');
console.log('使用说明:');
console.log('========================================');
console.log('1. 现在从飞书手机App发送一条消息');
console.log('2. 观察控制台是否显示 "[飞书事件]" 或 "[WS消息]"');
console.log('3. 如果收到消息但UI没更新，检查BotChatTab组件');
console.log('4. 运行 window.testFeishuMessage() 测试模拟消息');
console.log('========================================\n');

// 测试函数：模拟飞书消息
window.testFeishuMessage = function(content = '测试消息') {
    console.log('\n[测试] 模拟飞书消息...');
    
    // 模拟WebSocket消息
    const mockMessage = {
        type: 'feishu-chat-message',
        data: {
            chat_id: 'test_chat',
            message_id: 'test_' + Date.now(),
            sender_type: 'user',
            content: content,
            send_time: new Date().toISOString()
        }
    };
    
    // 派发事件
    window.dispatchEvent(new CustomEvent('websocket-message', {
        detail: mockMessage
    }));
    
    window.dispatchEvent(new CustomEvent('feishu-chat-message-received', {
        detail: mockMessage.data
    }));
    
    console.log('[测试] 事件已派发，检查UI是否更新');
};

// 状态检查函数
window.checkStatus = function() {
    console.log('\n[状态]');
    console.log('  WebSocket消息数:', messageCount);
    console.log('  飞书事件数:', feishuCount);
    console.log('  WS连接:', window.__stockPegWsConnected);
};

console.log('提示: 运行 window.checkStatus() 查看消息统计');
