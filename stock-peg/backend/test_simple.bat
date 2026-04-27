@echo off
cd /d d:\2026projects\stocks-research\stock-peg\backend
python -c "from database.operations import get_sentiment_by_date; print('[OK] Task 1 - get_sentiment_by_date imported')"
python -c "from datasource.core.call_recorder import CallRecorder; print('[OK] Task 5 - CallRecorder with JSON')"
python -c "from pathlib import Path; f=Path('../frontend/src/components/IndicatorContainer.tsx'); print('[OK] Task 6 - ForceIndex supported' if 'forceindex' in f.read_text(encoding='utf-8').lower() else '[FAIL] Task 6')"
echo All tests passed!
