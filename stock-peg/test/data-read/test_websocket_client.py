"""
WebSocket 股票数据测试客户端（命令行版本）
通过 WebSocket 和 HTTP API 获取股票的全部数据
"""
import asyncio
import json
import sys
from datetime import datetime
from typing import Optional
import websockets
from pathlib import Path
import httpx

# 添加backend路径（用于获取配置）
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

try:
    from config.settings import settings
    WS_URL = f"ws://localhost:{settings.server_port}/ws"
    API_URL = f"http://localhost:{settings.server_port}"
except:
    WS_URL = "ws://localhost:8000/ws"
    API_URL = "http://localhost:8000"


class WebSocketTestClient:
    """WebSocket测试客户端"""
    
    def __init__(self, ws_url: str = WS_URL, api_url: str = API_URL):
        self.ws_url = ws_url
        self.api_url = api_url
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.is_connected = False
    
    async def connect(self):
        """连接到WebSocket服务器"""
        print(f"\n正在连接到: {self.ws_url}")
        try:
            self.websocket = await websockets.connect(self.ws_url)
            self.is_connected = True
            print("[OK] WebSocket连接成功\n")
            return True
        except Exception as e:
            print(f"[ERROR] 连接失败: {e}\n")
            return False
    
    async def disconnect(self):
        """断开WebSocket连接"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            print("\n[OK] WebSocket连接已关闭")
    
    async def get_stock_quote(self, stock_code: str) -> Optional[dict]:
        """获取股票实时行情"""
        url = f"{self.api_url}/api/stocks/quote/{stock_code}"
        print(f"正在获取实时行情: {url}")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    print(f"[OK] 获取实时行情成功")
                    return data
                else:
                    print(f"[WARN] HTTP {response.status_code}: {response.text}")
                    return None
        except Exception as e:
            print(f"[ERROR] 获取实时行情失败: {e}")
            return None
    
    async def get_stock_kline(self, stock_code: str, period: str = "day", count: int = 500) -> Optional[dict]:
        """获取股票K线数据（数据库优先）"""
        url = f"{self.api_url}/api/stocks/kline-db/{stock_code}?period={period}&count={count}"
        print(f"正在获取K线数据: {url}")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    print(f"[OK] 获取K线数据成功")
                    return data
                else:
                    print(f"[WARN] HTTP {response.status_code}: {response.text}")
                    return None
        except Exception as e:
            print(f"[ERROR] 获取K线数据失败: {e}")
            return None
    
    async def listen_websocket(self, stock_code: str, duration: int = 10):
        """监听WebSocket实时推送"""
        if not self.is_connected:
            print("[ERROR] 未连接到服务器")
            return
        
        # 订阅股票
        message = {
            "action": "subscribe",
            "stock_code": stock_code
        }
        
        try:
            await self.websocket.send(json.dumps(message))
            print(f"[OK] 已发送订阅请求: {stock_code}")
        except Exception as e:
            print(f"[ERROR] 发送订阅请求失败: {e}")
            return
        
        print(f"\n开始监听实时推送（{duration}秒）...")
        print("=" * 60)
        
        message_count = 0
        
        try:
            while True:
                try:
                    message = await asyncio.wait_for(
                        self.websocket.recv(),
                        timeout=duration
                    )
                    
                    data = json.loads(message)
                    message_count += 1
                    
                    msg_type = data.get('type', 'unknown')
                    print(f"\n消息 #{message_count} [{datetime.now().strftime('%H:%M:%S')}]")
                    print(f"类型: {msg_type}")
                    
                    if msg_type == 'quote':
                        quote_data = data.get('data', {})
                        print(f"股票代码: {stock_code}")
                        print(f"股票名称: {quote_data.get('name', 'N/A')}")
                        print(f"当前价格: {quote_data.get('price', 0):.2f}")
                        print(f"涨跌幅: {quote_data.get('change_pct', 0):.2f}%")
                    else:
                        print(json.dumps(data, indent=2, ensure_ascii=False))
                    
                    print("-" * 60)
                    
                except asyncio.TimeoutError:
                    print(f"\n[INFO] 监听{duration}秒结束")
                    break
                    
        except websockets.exceptions.ConnectionClosed:
            print("\n[INFO] 连接已关闭")
        except Exception as e:
            print(f"\n[ERROR] 监听失败: {e}")


def print_data_summary(data_type: str, data: any, max_show: int = 2):
    """打印数据摘要（数据多时只显示前N条）"""
    print(f"\n{'=' * 60}")
    print(f"{data_type}")
    print(f"{'=' * 60}")
    
    if data is None:
        print("[ERROR] 数据为空")
        return
    
    if isinstance(data, dict):
        # 检查是否是带metadata的响应
        if 'data' in data:
            actual_data = data['data']
            metadata = {k: v for k, v in data.items() if k != 'data'}
            
            # 打印metadata
            if metadata:
                print("\n[元数据]")
                for key, value in metadata.items():
                    print(f"  {key}: {value}")
            
            # 处理实际数据
            if isinstance(actual_data, list):
                print(f"\n[数据] 总数: {len(actual_data)} 条")
                if len(actual_data) > max_show:
                    print(f"\n显示前 {max_show} 条:")
                    for i, item in enumerate(actual_data[:max_show]):
                        print(f"\n  [{i+1}] {json.dumps(item, indent=4, ensure_ascii=False)}")
                    print(f"\n... 省略剩余 {len(actual_data) - max_show} 条")
                else:
                    print("\n[全部数据]")
                    print(json.dumps(actual_data, indent=2, ensure_ascii=False))
            else:
                print("\n[数据]")
                print(json.dumps(actual_data, indent=2, ensure_ascii=False))
        else:
            # 直接是字典数据
            print("\n[数据]")
            print(json.dumps(data, indent=2, ensure_ascii=False))
    
    elif isinstance(data, list):
        print(f"\n[数据] 总数: {len(data)} 条")
        if len(data) > max_show:
            print(f"\n显示前 {max_show} 条:")
            for i, item in enumerate(data[:max_show]):
                print(f"\n  [{i+1}] {json.dumps(item, indent=4, ensure_ascii=False)}")
            print(f"\n... 省略剩余 {len(data) - max_show} 条")
        else:
            print("\n[全部数据]")
            print(json.dumps(data, indent=2, ensure_ascii=False))
    
    else:
        print(f"\n[数据] {data}")


async def test_stock_data(stock_code: str, listen_duration: int = 10):
    """测试获取股票的全部数据"""
    print("\n" + "=" * 60)
    print(f"股票数据测试 - {stock_code}")
    print("=" * 60)
    
    client = WebSocketTestClient()
    
    # 1. 获取实时行情
    print("\n[步骤1] 获取实时行情")
    quote_data = await client.get_stock_quote(stock_code)
    print_data_summary("实时行情", quote_data)
    
    # 2. 获取K线数据
    print("\n[步骤2] 获取K线数据")
    kline_data = await client.get_stock_kline(stock_code, period="day", count=500)
    print_data_summary("K线数据", kline_data)
    
    # 3. WebSocket实时推送
    print("\n[步骤3] WebSocket实时推送测试")
    if await client.connect():
        try:
            await client.listen_websocket(stock_code, listen_duration)
        finally:
            await client.disconnect()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


def print_usage():
    """打印使用说明"""
    print("\nWebSocket 股票数据测试客户端")
    print("=" * 60)
    print(f"WebSocket地址: {WS_URL}")
    print(f"API地址: {API_URL}")
    print("=" * 60)
    print("\n使用方法:")
    print("  python test_websocket_client.py <股票代码> [监听时长]")
    print("\n参数说明:")
    print("  股票代码    - 必填，如: 600219, 000001")
    print("  监听时长    - 可选，WebSocket监听秒数，默认10秒")
    print("\n示例:")
    print("  python test_websocket_client.py 600219")
    print("  python test_websocket_client.py 600219 30")
    print()


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print_usage()
        return
    
    stock_code = sys.argv[1]
    listen_duration = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    await test_stock_data(stock_code, listen_duration)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[INFO] 用户中断")
    except Exception as e:
        print(f"\n[ERROR] 运行失败: {e}")
