const DEFAULT_BASE_URL = process.env.BASE_URL || "http://localhost:8000";

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith("--")) continue;
    const key = token.slice(2);
    const value = argv[i + 1];
    if (!value || value.startsWith("--")) {
      args[key] = "true";
      continue;
    }
    args[key] = value;
    i += 1;
  }
  return args;
}

function toBool(value, fallback = false) {
  if (value === undefined) return fallback;
  return String(value).toLowerCase() === "true";
}

function toInt(value, fallback) {
  const n = Number.parseInt(String(value), 10);
  return Number.isFinite(n) ? n : fallback;
}

async function requestKlineFast({
  baseUrl,
  stockCode,
  period = "day",
  count = 100,
  sessionId,
  quickLoad = false,
  localOnly = false,
  timeoutMs = 2500,
}) {
  const params = new URLSearchParams({
    period,
    count: String(count),
    quick_load: String(quickLoad),
    local_only: String(localOnly),
  });
  if (sessionId) {
    params.append("session_id", sessionId);
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  const url = `${baseUrl}/api/stocks/kline-db-fast/${stockCode}?${params.toString()}`;

  try {
    const resp = await fetch(url, { signal: controller.signal });
    if (!resp.ok) {
      const text = await resp.text();
      throw new Error(`HTTP ${resp.status} ${resp.statusText} ${text}`);
    }
    return await resp.json();
  } finally {
    clearTimeout(timer);
  }
}

function summarize(result) {
  const list = Array.isArray(result?.data) ? result.data : [];
  const first = list.length > 0 ? list[0] : null;
  const last = list.length > 0 ? list[list.length - 1] : null;
  return {
    count: list.length,
    local_data_available: result?.local_data_available,
    is_updating: result?.is_updating,
    task_id: result?.task_id,
    last_update: result?.last_update,
    first_date: first?.date ?? null,
    last_date: last?.date ?? null,
  };
}

async function main() {
  const cli = parseArgs(process.argv.slice(2));
  const stockCode = cli.stock || cli.code || "000001";
  const baseUrl = (cli.base || DEFAULT_BASE_URL).replace(/\/+$/, "");
  const period = cli.period || "day";
  const quickCount = toInt(cli.quickCount, 100);
  const fullCount = Math.min(toInt(cli.fullCount, 500), 500);
  const timeoutMs = toInt(cli.timeout, 2500);
  const localOnly = toBool(cli.localOnly, true);
  const sessionId = cli.sessionId || `node-debug-${Date.now()}`;

  console.log("开始测试参数:");
  console.log({
    baseUrl,
    stockCode,
    period,
    quickCount,
    fullCount,
    localOnly,
    timeoutMs,
    sessionId,
  });

  const quick = await requestKlineFast({
    baseUrl,
    stockCode,
    period,
    count: quickCount,
    sessionId,
    quickLoad: true,
    localOnly,
    timeoutMs,
  });

  const full = await requestKlineFast({
    baseUrl,
    stockCode,
    period,
    count: fullCount,
    sessionId,
    quickLoad: false,
    localOnly,
    timeoutMs,
  });

  const quickSummary = summarize(quick);
  const fullSummary = summarize(full);

  console.log("快速加载结果:");
  console.log(quickSummary);
  console.log("完整加载结果:");
  console.log(fullSummary);

  const allCovered = fullSummary.count >= quickSummary.count && fullSummary.count > 0;
  console.log("是否获取到更多或全部本地可用K线数据:", allCovered);
}

main().catch((err) => {
  console.error("调试失败:", err?.message || err);
  process.exitCode = 1;
});
