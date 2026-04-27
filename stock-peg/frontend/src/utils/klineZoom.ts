export interface ZoomRange {
  start: number;
  end: number;
}

export interface ZoomWindow {
  startIndex: number;
  endIndex: number;
}

export const DEFAULT_ZOOM_RANGE: ZoomRange = { start: 60, end: 100 };

export const normalizeZoomRangeToRight = (start: number, end: number): ZoomRange => {
  const safeStart = Math.max(0, Math.min(100, start));
  const safeEnd = Math.max(0, Math.min(100, end));
  const width = Math.max(1, Math.min(100, Math.abs(safeEnd - safeStart)));
  return {
    start: Math.max(0, 100 - width),
    end: 100
  };
};

export const areZoomRangesEqual = (a: ZoomRange, b: ZoomRange): boolean => {
  return Math.abs(a.start - b.start) < 0.01 && Math.abs(a.end - b.end) < 0.01;
};

export const getPinnedZoomWindow = (totalCount: number, range: ZoomRange): ZoomWindow => {
  if (totalCount <= 0) {
    return { startIndex: 0, endIndex: 0 };
  }

  const normalized = normalizeZoomRangeToRight(range.start, range.end);
  const widthPercent = Math.max(1, normalized.end - normalized.start) / 100;
  const visibleCount = Math.max(1, Math.round(totalCount * widthPercent));
  const endIndex = totalCount - 1;
  const startIndex = Math.max(0, endIndex - visibleCount + 1);
  return { startIndex, endIndex };
};

export const getUnifiedAxisLabelInterval = (
  totalCount: number,
  range?: ZoomRange,
  targetLabelCount = 6
): number => {
  if (totalCount <= 1) {
    return 0;
  }

  let visibleCount = totalCount;
  if (range) {
    const normalized = normalizeZoomRangeToRight(range.start, range.end);
    const widthPercent = Math.max(1, normalized.end - normalized.start) / 100;
    visibleCount = Math.max(1, Math.round(totalCount * widthPercent));
  }

  const safeTargetCount = Math.max(2, targetLabelCount);
  return Math.max(0, Math.ceil(visibleCount / safeTargetCount) - 1);
};

export const getZoomRangeFromPayload = (
  payload: any,
  totalCount: number,
  currentRange: ZoomRange,
  dates?: string[]
): ZoomRange => {
  if (typeof payload?.start === 'number' && typeof payload?.end === 'number') {
    return normalizeZoomRangeToRight(payload.start, payload.end);
  }

  const startValue = payload?.startValue;
  const endValue = payload?.endValue;

  if (totalCount > 0 && startValue !== undefined && endValue !== undefined) {
    let startIndex: number | null = null;
    let endIndex: number | null = null;

    if (typeof startValue === 'number' && typeof endValue === 'number') {
      startIndex = Math.floor(startValue);
      endIndex = Math.floor(endValue);
    } else if (dates && typeof startValue === 'string' && typeof endValue === 'string') {
      startIndex = dates.indexOf(startValue);
      endIndex = dates.indexOf(endValue);
    }

    if (startIndex !== null && endIndex !== null && startIndex >= 0 && endIndex >= startIndex) {
      const safeStart = Math.max(0, Math.min(totalCount - 1, startIndex));
      const safeEnd = Math.max(safeStart, Math.min(totalCount - 1, endIndex));
      const visibleCount = safeEnd - safeStart + 1;
      const width = (visibleCount / totalCount) * 100;
      return normalizeZoomRangeToRight(100 - width, 100);
    }
  }

  return currentRange;
};
