import os

files = [
    'backend/services/feishu/feishu_card_service.py',
    'backend/services/feishu/feishu_long_connection_service.py',
]

for f in files:
    if os.path.exists(f):
        with open(f, 'r', encoding='utf-8') as file:
            lines = sum(1 for _ in file)
        print(f'{lines:5d} lines: {f}')
    else:
        print(f'NOT FOUND: {f}')
