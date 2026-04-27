"""
测试最简单的飞书卡片
"""
import json

# 最简单的卡片（只有文本）
simple_card = {
    "config": {"wide_screen_mode": True},
    "elements": [
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": "**测试卡片**\n这是一条测试消息"
            }
        }
    ]
}

print("最简单的卡片JSON:")
print(json.dumps(simple_card, indent=2, ensure_ascii=False))

# 带一个按钮的卡片
button_card = {
    "config": {"wide_screen_mode": True},
    "elements": [
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": "**测试按钮卡片**"
            }
        },
        {
            "tag": "action",
            "actions": [
                {
                    "tag": "button",
                    "name": "btn_test",
                    "text": {"tag": "plain_text", "content": "测试按钮"},
                    "type": "primary",
                    "value": {"test": "value"}
                }
            ]
        }
    ]
}

print("\n\n带按钮的卡片JSON:")
print(json.dumps(button_card, indent=2, ensure_ascii=False))
