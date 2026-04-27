"""
测试对话日志功能
"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "backend"))

from services.bot_chat_logger import bot_chat_logger
from datetime import datetime

def test_logger():
    """测试日志记录功能"""
    
    print("="*60)
    print("测试对话日志功能")
    print("="*60)
    
    # 测试记录用户消息
    print("\n[测试1] 记录用户消息")
    bot_chat_logger.log_message(
        message_id="test_user_001",
        sender_type="user",
        sender_id="ou_test123",
        content="查询 紫金矿业",
        chat_id="oc_test456"
    )
    print("[OK] 用户消息已记录")
    
    # 测试记录 bot 回复
    print("\n[测试2] 记录 Bot 回复")
    bot_chat_logger.log_message(
        message_id="test_bot_001",
        sender_type="bot",
        sender_id="bot",
        content="[行情查询] 股票: 紫金矿业\n当前价格: 380.50 HKD\n涨跌幅: +1.2%",
        chat_id="oc_test456"
    )
    print("[OK] Bot 回复已记录")
    
    # 测试记录命令
    print("\n[测试3] 记录命令执行")
    bot_chat_logger.log_command(
        command="查询 紫金矿业",
        result="success",
        sender_id="ou_test123"
    )
    print("[OK] 命令已记录")
    
    # 测试记录错误
    print("\n[测试4] 记录错误")
    bot_chat_logger.log_error(
        error_msg="测试错误消息",
        context={"test": True}
    )
    print("[OK] 错误已记录")
    
    # 检查日志文件
    print("\n[测试5] 检查日志文件")
    log_dir = project_root / "backend" / "logs" / "bot-chat"
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    log_file = log_dir / f"chat-{current_date}.log"
    json_file = log_dir / f"chat-{current_date}.json"
    
    print(f"\n日志目录: {log_dir}")
    print(f"文本日志: {log_file} ({'存在' if log_file.exists() else '不存在'})")
    print(f"JSON日志: {json_file} ({'存在' if json_file.exists() else '不存在'})")
    
    if log_file.exists():
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f"\n文本日志内容 ({len(lines)} 行):")
            for line in lines[-5:]:  # 显示最后5行
                # 移除 emoji 和特殊字符
                safe_line = line.strip().encode('ascii', 'ignore').decode('ascii')
                if safe_line:
                    print(f"  {safe_line}")
    
    if json_file.exists():
        import json
        with open(json_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f"\nJSON日志内容 ({len(lines)} 条):")
            for line in lines[-3:]:  # 显示最后3条
                data = json.loads(line.strip())
                print(f"  {data['sender_type']}: {data['content'][:30]}...")
    
    # 测试读取最近日志
    print("\n[测试6] 读取最近日志")
    recent_logs = bot_chat_logger.get_recent_logs(limit=5)
    print(f"最近 {len(recent_logs)} 条日志:")
    for log in recent_logs:
        sender_label = "[BOT]" if log['sender_type'] == 'bot' else "[USER]"
        print(f"  {sender_label} {log['content'][:40]}...")
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)


if __name__ == "__main__":
    test_logger()
