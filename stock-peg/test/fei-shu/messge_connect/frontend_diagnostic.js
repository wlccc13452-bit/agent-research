"""
Frontend diagnostic script - to be run in browser console
Paste this into the browser console (F12) while on the frontend page
"""

console.log(`
============================================================
Frontend Feishu Message Diagnostic
============================================================
`);

// Check 1: WebSocket connection status
console.log('[CHECK 1] WebSocket Connection Status');
const wsConnected = window.__stockPegWsConnected;
console.log('  Connected:', wsConnected);

// Check 2: Test event listeners
console.log('[CHECK 2] Setting up test event listeners');

let messageReceived = false;
let feishuMessageReceived = false;

window.addEventListener('websocket-message', (e) => {
    console.log('[EVENT] websocket-message received:', e.detail);
    messageReceived = true;
});

window.addEventListener('feishu-chat-message-received', (e) => {
    console.log('[EVENT] feishu-chat-message-received received:', e.detail);
    feishuMessageReceived = true;
});

// Check 3: QueryClient status
console.log('[CHECK 3] React Query Status');
console.log('  QueryClient available:', typeof window.__REACT_QUERY_DEVTOOLS_GLOBAL_HOOK__ !== 'undefined');

// Instructions for testing
console.log(`
[INSTRUCTIONS]
1. Now send a message from your Feishu mobile app
2. OR run this in console to simulate:
   
   fetch('http://localhost:8000/api/feishu/test-broadcast', {method: 'POST'})
     .then(r => r.json())
     .then(console.log);

3. Check if the events above are logged
4. Check the Network tab (F12 > Network) for WebSocket messages

[EXPECTED RESULTS]
- websocket-message event should be logged
- feishu-chat-message-received event should be logged
- BotChatTab should refresh and show the message

[POTENTIAL ISSUES]
- If no events logged: WebSocket connection problem
- If events logged but UI doesn't update: React Query problem
- If only websocket-message logged: Event dispatch problem in useWebSocket.ts
`);

// Test broadcast function
window.testFeishuBroadcast = async function() {
    console.log('[TEST] Triggering test broadcast...');
    try {
        const resp = await fetch('http://localhost:8000/api/feishu/test-broadcast', {method: 'POST'});
        const data = await resp.json();
        console.log('[TEST] Broadcast response:', data);
        
        setTimeout(() => {
            console.log('[TEST] Results after 2 seconds:');
            console.log('  websocket-message received:', messageReceived);
            console.log('  feishu-chat-message-received received:', feishuMessageReceived);
        }, 2000);
    } catch (e) {
        console.error('[TEST] Error:', e);
    }
};

console.log('Run window.testFeishuBroadcast() to test');
