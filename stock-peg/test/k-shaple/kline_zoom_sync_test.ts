import assert from 'node:assert/strict';
import { areZoomRangesEqual, getPinnedZoomWindow, getZoomRangeFromPayload, normalizeZoomRangeToRight } from '../../frontend/src/utils/klineZoom';

const dates = [
  '2026-01-01',
  '2026-01-02',
  '2026-01-03',
  '2026-01-04',
  '2026-01-05',
  '2026-01-06',
  '2026-01-07',
  '2026-01-08',
  '2026-01-09',
  '2026-01-10'
];

const current = { start: 80, end: 100 };

const normalized = normalizeZoomRangeToRight(20, 60);
assert.equal(normalized.end, 100);
assert.equal(normalized.start, 60);

const fromPercent = getZoomRangeFromPayload({ start: 25, end: 55 }, dates.length, current, dates);
assert.equal(fromPercent.end, 100);
assert.ok(fromPercent.start > 60 && fromPercent.start < 80);

const fromIndexValue = getZoomRangeFromPayload({ startValue: 2, endValue: 6 }, dates.length, current, dates);
assert.equal(fromIndexValue.end, 100);
assert.equal(Number(fromIndexValue.start.toFixed(2)), 50);

const fromDateValue = getZoomRangeFromPayload(
  { startValue: '2026-01-03', endValue: '2026-01-07' },
  dates.length,
  current,
  dates
);
assert.equal(fromDateValue.end, 100);
assert.equal(Number(fromDateValue.start.toFixed(2)), 50);

const fallback = getZoomRangeFromPayload({ startValue: 'NA', endValue: 'NA' }, dates.length, current, dates);
assert.ok(areZoomRangesEqual(fallback, current));

const windowByRange = getPinnedZoomWindow(10, { start: 70, end: 100 });
assert.equal(windowByRange.startIndex, 7);
assert.equal(windowByRange.endIndex, 9);

console.log('kline_zoom_sync_test passed');
