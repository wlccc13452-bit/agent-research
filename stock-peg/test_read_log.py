import sys
log_file = 'd:/play-ground/股票研究/stock-peg/backend/data/logs/conversation_2026-03-16.log'
with open(log_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    print(''.join(lines[-30:]))
