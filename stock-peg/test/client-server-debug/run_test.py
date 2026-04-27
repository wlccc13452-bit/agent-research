"""启动后端服务器进行测试"""
import subprocess
import sys
import time
import httpx

# 启动服务器
print("启动后端服务器...")
process = subprocess.Popen(
    [sys.executable, "main.py"],
    cwd=r"D:\play-ground\股票研究\stock-peg\backend",
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# 等待服务器启动
print("等待服务器启动...")
for i in range(30):
    time.sleep(1)
    try:
        response = httpx.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print(f"服务器已启动! (等待了{i+1}秒)")
            break
    except:
        pass
else:
    print("服务器启动超时")
    stdout, stderr = process.communicate(timeout=5)
    print("STDOUT:", stdout.decode('utf-8', errors='ignore'))
    print("STDERR:", stderr.decode('utf-8', errors='ignore'))
    process.kill()
    sys.exit(1)

# 运行测试
print("\n运行测试...")
import subprocess
result = subprocess.run(
    [sys.executable, r"D:\play-ground\股票研究\stock-peg\test\client-server-debug\test_server_client.py", "basic"],
    cwd=r"D:\play-ground\股票研究\stock-peg"
)
print("\n测试完成")

# 关闭服务器
print("关闭服务器...")
process.terminate()
process.wait(timeout=5)
print("完成")
