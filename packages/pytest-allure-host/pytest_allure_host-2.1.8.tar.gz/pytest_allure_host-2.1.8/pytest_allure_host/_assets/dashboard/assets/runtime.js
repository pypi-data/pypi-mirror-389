// Dashboard runtime (externalized for CSP)
// Helpers and formatters
let COLORS = null;
function getThemeColors() {
  if (COLORS) return COLORS;
  const s = getComputedStyle(document.body);
  COLORS = {
    ok: s.getPropertyValue("--ok") || "#16a34a",
    fail: s.getPropertyValue("--fail") || "#dc2626",
    broken: s.getPropertyValue("--broken") || "#f59e0b",
    bg: s.getPropertyValue("--bg") || "#ffffff",
    bg2: s.getPropertyValue("--bg2") || "#f6f7f9",
  };
  // Trim values
  for (const k of Object.keys(COLORS)) {
    COLORS[k] = String(COLORS[k]).trim();
  }
  return COLORS;
}
function esc(s) {
  // Lightweight HTML escape to prevent accidental injection when building innerHTML
  if (s == null) return "";
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
const nf0 = new Intl.NumberFormat(undefined, { maximumFractionDigits: 0 });
const nf1 = new Intl.NumberFormat(undefined, {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});
function format_percent(x, dp = 1) {
  if (x == null || Number.isNaN(x)) return "—";
  const val = Math.max(0, Math.min(100, x));
  const nf =
    dp === 1
      ? nf1
      : new Intl.NumberFormat(undefined, {
          minimumFractionDigits: dp,
          maximumFractionDigits: dp,
        });
  return nf.format(val) + "%";
}
function signed_delta(x, suffix = "") {
  if (x == null || Number.isNaN(x)) return "—";
  const s = x > 0 ? "+" : x < 0 ? "−" : "±";
  return s + Math.abs(x).toFixed(1) + suffix;
}
function format_duration(sec) {
  if (sec == null || Number.isNaN(sec)) return "—";
  const s = Math.max(0, Math.floor(sec));
  if (s < 60) return `${s} s`;
  const m = Math.floor(s / 60), r = s % 60;
  if (m < 60) return `${m}m ${r}s`;
  const h = Math.floor(m / 60), rm = m % 60;
  return `${h}h ${rm}m ${r}s`;
}
function utc_to_local_pair(epochSec) {
  if (!epochSec) return { local: "—", utc: "—" };
  const d = new Date(epochSec * 1000);
  return {
    local: d.toLocaleString(),
    utc: d.toISOString().replace("T", " ").replace(".000Z", " UTC"),
  };
}

// Theme toggler
(function () {
  const btn = () => document.getElementById("theme");
  function apply(t) {
    if (t === "dark") {
      document.body.setAttribute("data-theme", "dark");
      if (btn()) btn().textContent = "Light";
    } else {
      document.body.removeAttribute("data-theme");
      if (btn()) btn().textContent = "Dark";
    }
  }
  const LS = "ah_dash_";
  function lsGet(k) {
    try {
      return localStorage.getItem(LS + k);
    } catch (e) {
      return null;
    }
  }
  function lsSet(k, v) {
    try {
      localStorage.setItem(LS + k, v);
    } catch (e) {}
  }
  let cur = lsGet("theme") || "";
  if (!cur) {
    cur =
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";
  }
  window.__dashThemeApply = apply;
  window.__dashThemeGet = () => cur;
  window.__dashThemeSet = (t) => {
    cur = t;
    lsSet("theme", t);
    apply(t);
    try {
      const b = btn();
      if (b) {
        const next = t === "dark" ? "Light" : "Dark";
        b.setAttribute("title", `Switch to ${next} mode`);
        b.setAttribute("aria-label", `Switch to ${next} mode`);
      }
    } catch (e) {}
  };
  window.addEventListener("DOMContentLoaded", () => {
    apply(cur);
    const b = btn();
    if (b) {
      const next = cur === "dark" ? "Light" : "Dark";
      b.setAttribute("title", `Switch to ${next} mode`);
      b.setAttribute("aria-label", `Switch to ${next} mode`);
      b.addEventListener("click", () => {
        window.__dashThemeSet(
          window.__dashThemeGet() === "dark" ? "light" : "dark"
        );
      });
    }
  });
})();

// Selection origin: 'init' | 'table' | 'chart'
window.__dashSelOrigin = 'init';

// Feature flag helpers
function isPolishV2() {
  try { return document.body && document.body.classList.contains('ui-polish-v2') && document.body.getAttribute('data-ui') === 'polish-v2'; } catch (e) { return false; }
}
function ensureUiFlagFromQuery() {
  try {
    const u = new URL(window.location.href);
    const raw = (u.searchParams.get('ui') || '').toLowerCase();
    const ui = raw.replace(/^v/, 'polish-v'); // accept v2/v1 shorthand
    if (ui === 'polish-v1') {
      document.body.classList.remove('ui-polish-v2');
      document.body.classList.add('ui-polish-v1');
      document.body.setAttribute('data-ui', 'polish-v1');
    } else if (ui === 'polish-v2') {
      document.body.classList.remove('ui-polish-v1');
      document.body.classList.add('ui-polish-v2');
      document.body.setAttribute('data-ui', 'polish-v2');
    }
  } catch (e) {}
}

// Plotly loader: prefer local asset, fallback to CDN dynamically
function ensurePlotly(timeoutMs = 8000) {
  return new Promise((resolve, reject) => {
    if (typeof window.Plotly !== "undefined") return resolve();
    const cdn =
      "https://cdn.jsdelivr.net/npm/plotly.js-dist-min@2.29.1/plotly.min.js";
    const s = document.createElement("script");
    s.src = cdn;
    s.defer = true;
    s.onload = () => resolve();
    s.onerror = () => reject(new Error("Failed to load Plotly from CDN"));
    document.head.appendChild(s);
    setTimeout(() => {
      if (typeof window.Plotly === "undefined") {
        reject(new Error("Plotly load timeout"));
      }
    }, timeoutMs);
  });
}

// Determine data/runs paths robustly regardless of nesting (root or latest/dashboard)
let __dashResolvedPrefix = null; // like "./" or "../" or "../../"

// Build an absolute path to the runs index that works from any dashboard location
function computeRunsIndexHref() {
  try {
    const u = new URL(window.location.href);
    // Drop trailing file name to work with directory path
    const rawParts = u.pathname.split("/");
    // Keep empties to preserve leading slash position, but also a filtered copy for indexing
    const parts = rawParts.filter(Boolean);
    // Prefer explicit 'latest' segment which lives under the branch root
    const iLatest = parts.indexOf("latest");
    if (iLatest >= 0) {
      const base = parts.slice(0, iLatest).join("/"); // /<prefix>/<project>/<branch>
      return "/" + base + "/runs/index.html";
    }
    // Fallback: if we are in .../<something>/dashboard/, go up two segments to branch root
    const iDash = parts.indexOf("dashboard");
    if (iDash >= 0) {
      const upto = Math.max(0, iDash - 1); // drop the segment before 'dashboard' (latest or run_id)
      const base = parts.slice(0, upto).join("/");
      return "/" + base + "/runs/index.html";
    }
    // Last resort: use discovered prefix (may be './' or '../') and hope for shallow nesting
    const pref = typeof __dashResolvedPrefix === "string" && __dashResolvedPrefix ? __dashResolvedPrefix : "./";
    return pref + "runs/index.html";
  } catch (e) {
    // Extremely defensive default
    return "../runs/index.html";
  }
}
async function loadData() {
  // Try a set of candidate prefixes relative to current page
  const prefixes = ["./", "../", "../../", "../../../", "../../../../"]; // generous depth
  const ts = String(Date.now());
  let lastErr = null;
  for (const p of prefixes) {
    try {
      const probe = new URL(p + "data/history.json", window.location.href);
      probe.searchParams.set("_", ts);
      const r = await fetch(probe.toString(), { cache: "no-store" });
      if (!r.ok) { lastErr = new Error("HTTP " + r.status + " @ " + probe); continue; }
      const ctype = (r.headers.get("content-type") || "").toLowerCase();
      let data = null;
      if (ctype.includes("application/json")) {
        data = await r.json();
      } else {
        const txt = await r.text();
        const trimmed = String(txt || "").trim();
        if (trimmed.startsWith("{") || trimmed.startsWith("[")) {
          data = JSON.parse(trimmed);
        }
      }
      if (data) {
        __dashResolvedPrefix = p; // remember for other links (e.g., runs index)
        return data;
      }
    } catch (e) {
      lastErr = e;
    }
  }
  throw lastErr || new Error("Unable to locate data/history.json from current page");
}

function stackedAndRate(divId, data) {
  const C = getThemeColors();
  const runs = data.runs || [];
  const x = runs.map((r) => r.run_id);
  const passed = runs.map((r) => r.passed),
    failed = runs.map((r) => r.failed),
    broken = runs.map((r) => r.broken);
  const rate = data.rolling10 || [];
  const bars = [
    {
      x,
      y: passed,
      type: "bar",
      name: "Passed",
      marker: {
        color: C.ok,
        line: { width: 0, color: "transparent" },
      },
      insidetextanchor: "middle",
    },
    {
      x,
      y: failed,
      type: "bar",
      name: "Failed",
      marker: {
        color: C.fail,
        line: { width: 0, color: "transparent" },
      },
      insidetextanchor: "middle",
    },
    {
      x,
      y: broken,
      type: "bar",
      name: "Broken",
      marker: {
        color: C.broken,
        line: { width: 0, color: "transparent" },
      },
      insidetextanchor: "middle",
    },
  ];
  const line = {
    x,
    y: rate,
    type: "scatter",
    mode: "lines+markers",
    name: "Pass% (rolling10)",
    yaxis: "y2",
  };
  const layout = {
    barmode: "stack",
    hovermode: "closest",
    xaxis: {
      title: "Run",
      tickfont: { size: 12 },
      titlefont: { size: 13 },
    },
    yaxis: {
      title: "Count",
      tickfont: { size: 12 },
      titlefont: { size: 13 },
    },
    yaxis2: {
      overlaying: "y",
      side: "right",
      title: "Pass %",
      rangemode: "tozero",
      tickfont: { size: 12 },
      titlefont: { size: 13 },
    },
    margin: { t: 10, r: 8, b: 28, l: 32 },
    paper_bgcolor: C.bg || "#fff",
    plot_bgcolor: C.bg2 || "#f6f7f9",
  };
  Plotly.newPlot(divId, [...bars, line], layout, {
    displayModeBar: false,
    responsive: true,
  });
}

function chartLayoutBase() {
  const C = getThemeColors();
  return {
    margin: { t: 6, r: 10, b: 26, l: 72 },
    paper_bgcolor: C.bg || '#fff',
    plot_bgcolor: C.bg2 || '#f6f7f9',
    xaxis: { tickfont: { size: 12 }, titlefont: { size: 13 } },
    yaxis: { tickfont: { size: 12 }, titlefont: { size: 13 } },
  };
}

// --- helper: measure text width in px (robust left margin calc) -----------
function __measureTextPx(txt, font='12px "Open Sans", Arial, sans-serif'){
  try{
    const c = document.createElement('canvas');
    const ctx = c.getContext('2d');
    ctx.font = font;
    return ctx.measureText(String(txt||'')).width || 0;
  }catch(e){ return (String(txt||'').length * 7); }
}
function __maxLabelWidthPx(labels){
  try{
    const fontSize = 12; // keep in sync with yaxis.tickfont.size
    const font = `${fontSize}px "Open Sans", Arial, sans-serif`;
    let mx = 0;
    for (const s of (labels||[])) {
      const w = __measureTextPx(s, font);
      if (w > mx) mx = w;
    }
    return mx;
  }catch(e){ return 0; }
}

function maybeRotateXTicks(divEl) {
  try {
    const svg = divEl && divEl.querySelector('svg');
    if (!svg) return;
    const ticks = svg.querySelectorAll('.xtick text');
    let needsRotate = false;
    let lastRight = -Infinity;
    ticks.forEach((t) => {
      const b = t.getBoundingClientRect();
      if (b.left < lastRight - 2) needsRotate = true;
      lastRight = Math.max(lastRight, b.right);
    });
    if (needsRotate && window.Plotly) {
      const id = divEl.id;
      const gd = document.getElementById(id);
      window.Plotly.relayout(gd, { 'xaxis.tickangle': -25, 'margin.b': 40 });
    }
  } catch (e) {}
}

// Enforce a sensible minimum plot width if the container is too narrow
function ensureMinPlotWidth(divId, minPx = 520) {
  try {
    const el = document.getElementById(divId);
    if (!el || !window.Plotly) return;
    const rect = el.getBoundingClientRect();
    const w = rect && rect.width ? rect.width : 0;
    // If rendered width is tiny, bump both the element style and Plotly layout width.
    if (w > 0 && w < minPx) {
      el.style.minWidth = `${minPx}px`;
      try {
        window.Plotly.relayout(el, { autosize: false, width: minPx });
      } catch (e) {}
    }
  } catch (e) {}
}

function suitesBar(divId, data) {
  const C = getThemeColors();
  // Align with build output but be tolerant to older/newer keys
  const items = data.failures_by_suite || data.failures_by_area || [];
  // Empty-state handling: if no failures, show a subtle message instead of an empty chart
  try {
    const el = document.getElementById(divId);
    if (!items.length) {
      if (el) {
        el.innerHTML = '<div class="subtle" style="text-align:center; padding:8px">No failures by suite</div>';
      }
      return;
    }
  } catch (e) {}
  const y = items.map((i) => i[0]).reverse();
  const x = items.map((i) => i[1]).reverse();
  // --- Dynamic left margin to avoid clipping long labels (pixel-based) ---
  const _font2 = '12px "Open Sans", Arial, sans-serif';
  const _yMaxPx2 = __maxLabelWidthPx(y.map(String), _font2);
  const marginL = Math.max(84, Math.min(380, Math.ceil(_yMaxPx2 + 18)));
  const base = chartLayoutBase();
  // Normalize margins and font sizes to align with the Top failing tests chart
  const marginB = Math.max(40, (base.margin && base.margin.b) || 0);
  const xaxisTitleSize = Math.max(
    10,
    ((base.xaxis && base.xaxis.titlefont && base.xaxis.titlefont.size) || 13) - 2
  );
  const xaxisTickSize = Math.max(
    10,
    ((base.xaxis && base.xaxis.tickfont && base.xaxis.tickfont.size) || 12) - 1
  );
  Plotly.newPlot(
    divId,
    [
      {
        x,
        y,
        type: "bar",
        orientation: "h",
        marker: {
          color: C.fail,
          line: { width: 0, color: "transparent" },
        },
        insidetextanchor: "middle",
      },
    ],
    Object.assign({}, base, {
      // Dynamic left margin so long labels aren't clipped (with a small buffer)
      // Let Plotly autosize to the container instead of forcing a fixed width
      autosize: true,
      margin: Object.assign({}, base.margin, { l: marginL, b: marginB, r: 20 }),
      bargap: 0.45,
      xaxis: Object.assign({}, base.xaxis, {
        title: "Failures (last 10)",
        titlefont: Object.assign(
          {},
          (base.xaxis && base.xaxis.titlefont) || {},
          { size: xaxisTitleSize }
        ),
        tickfont: Object.assign(
          {},
          (base.xaxis && base.xaxis.tickfont) || {},
          { size: xaxisTickSize }
        ),
      }),
      yaxis: Object.assign({}, base.yaxis, {
        automargin: true,
        ticklabelposition: 'outside left',
        ticklabeloverflow: 'allow'
      }),
    }),
    { displayModeBar: false, responsive: true }
  );
  ensureMinPlotWidth(divId, 520);
  setTimeout(() => maybeRotateXTicks(document.getElementById(divId)), 50);
}

function drillTable(infoId, data) {
  const root = document.getElementById(infoId);
  const v2 = () => isPolishV2();
  function deriveS3Prefix(run) {
    try {
      const rid = run && run.run_id ? String(run.run_id) : '';
      const branch = run && run.branch ? String(run.branch) : '';
      const bucket = window.__AH_BUCKET || '';
      const prefix = window.__AH_PREFIX || 'reports';
      const project = window.__AH_PROJECT || '';
      // Build a best-effort prefix; avoid leading double slashes
      const parts = [prefix].concat(project ? [project] : []).concat(branch ? [branch] : []).concat(rid ? [rid] : []);
      const key = parts.filter(Boolean).join('/');
      return bucket ? `s3://${bucket}/${key}/` : `/${key}/`;
    } catch (e) { return ''; }
  }
  function setUrlParamRun(rid) {
    try {
      const u = new URL(window.location.href);
      if (rid) u.searchParams.set('run', String(rid)); else u.searchParams.delete('run');
      if (isPolishV2()) u.searchParams.set('ui', 'polish-v2');
      window.history.replaceState({}, '', u.toString());
    } catch (e) {}
  }
  function cursorToRun(run) {
    try {
      if (!run || !run.run_id) return;
      const idx = (data.runs || []).findIndex(r => String(r.run_id) === String(run.run_id));
      const chart = document.getElementById('chart');
      if (idx >= 0 && chart && window.Plotly && window.Plotly.Fx) {
        const x = (data.runs || []).map(r => r.run_id);
        const rid = x[idx];
        // Hover the x value to indicate selection; ignore errors
        try { window.Plotly.Fx.hover(chart, [{ curveNumber: 0, pointNumber: idx }]); } catch (e) {}
      }
    } catch (e) {}
  }
  function setRows(run) {
    root.innerHTML = "";
    if (!run || !run.run_id) {
      const kEl = document.createElement("div");
      kEl.className = "k";
      kEl.textContent = "Selected run";
      const vEl = document.createElement("div");
      vEl.className = "v subtle";
      vEl.textContent = "Select a run to see details";
      root.appendChild(kEl);
      root.appendChild(vEl);
      return;
    }
    const started = utc_to_local_pair(run.started_at || run.time);
    // V2 actions row (Open report, Copy link, Copy S3 prefix)
    if (v2()) {
      const actionsWrap = document.createElement('div');
      actionsWrap.style.display = 'flex';
      actionsWrap.style.gap = '8px';
      actionsWrap.style.margin = '0 0 8px 0';
      const openBtn = document.createElement('button');
      openBtn.className = 'btn';
      openBtn.type = 'button';
  openBtn.textContent = 'Open Report';
  openBtn.setAttribute('aria-label', 'Open Report');
      if (run.report_url) {
        openBtn.addEventListener('click', () => {
          try { window.open(String(run.report_url), '_blank', 'noopener'); } catch (e) {}
        });
      } else {
        openBtn.disabled = true;
      }
      const copyLink = document.createElement('button');
      copyLink.className = 'btn';
      copyLink.type = 'button';
      copyLink.textContent = 'Copy link';
      copyLink.addEventListener('click', async () => {
        try {
          setUrlParamRun(run.run_id);
          await navigator.clipboard.writeText(window.location.href);
          copyLink.textContent = 'Copied!';
          setTimeout(()=> copyLink.textContent = 'Copy link', 800);
        } catch (e) {}
      });
      const copyS3 = document.createElement('button');
      copyS3.className = 'btn';
      copyS3.type = 'button';
      copyS3.textContent = 'Copy S3 prefix';
      copyS3.addEventListener('click', async () => {
        try {
          const p = deriveS3Prefix(run);
          if (p) { await navigator.clipboard.writeText(p); copyS3.textContent = 'Copied!'; setTimeout(()=> copyS3.textContent='Copy S3 prefix', 800);} }
        catch (e) {}
      });
      actionsWrap.appendChild(openBtn);
      actionsWrap.appendChild(copyLink);
      actionsWrap.appendChild(copyS3);
      // Actions row spans 2 columns in CSS grid layout
      root.appendChild(actionsWrap);
    }
    const rows = [
      ["Pass%", format_percent(run.pass_percent || 0, 1)],
      ["Duration", format_duration(run.duration_seconds || 0)],
      ["Failed", nf0.format(run.failed || 0)],
      ["Run ID", run.run_id || "-"],
      ["Started", `${started.local}`],
      ["Started (UTC)", `${started.utc}`],
    ];
    for (const [k, v] of rows) {
      const kEl = document.createElement("div");
      kEl.className = "k";
      kEl.textContent = k;
      const vEl = document.createElement("div");
      vEl.className = "v";
      if (k === "Run ID") {
        vEl.style.fontFamily = "ui-monospace, SFMono-Regular, Menlo, monospace";
        const code = document.createElement('code');
        const rid = String(v || '-');
        if (run.report_url) {
          const a = document.createElement('a');
          a.href = String(run.report_url);
          a.target = '_blank';
          a.rel = 'noopener noreferrer';
          a.textContent = rid;
          code.appendChild(a);
        } else {
          code.textContent = rid;
        }
        vEl.appendChild(code);
      } else {
        vEl.textContent = String(v);
      }
      root.appendChild(kEl);
      root.appendChild(vEl);
    }

  // Update URL and chart cursor for v2 when selection changes
  try { if (v2()) { setUrlParamRun(run.run_id); cursorToRun(run); } } catch (e) {}

    // Update compact selected summary card
    try {
      const wrap = document.getElementById("selected-summary");
      const cont = document.getElementById("selected-summary-content");
      if (wrap && cont) {
        wrap.style.display = "block";
        const pass = format_percent(run.pass_percent || 0, 1);
        const dur = format_duration(run.duration_seconds || 0);
        const rid = String(run.run_id || "-");
        let html =
          '<div class="k">Run</div><div class="v"><code>' + (run.report_url ? ('<a target="_blank" rel="noopener noreferrer" href="' + esc(String(run.report_url)) + '">' + esc(rid) + '</a>') : esc(rid)) + '</code></div>' +
          '<div class="k">Pass%</div><div class="v">' + pass + '</div>' +
          '<div class="k">Fails</div><div class="v">' + nf0.format(run.failed||0) + '</div>' +
          '<div class="k">Duration</div><div class="v">' + dur + '</div>';
        cont.innerHTML = html;
      }
    } catch (e) {}
  }
  // Expose setter globally so table/chart can drive selection consistently
  try {
    window.__dashSetRows = function (run) {
      setRows(run || {});
      try {
        const rid = run && run.run_id ? run.run_id : null;
        document.dispatchEvent(new CustomEvent("run:selected", { detail: rid }));
      } catch (e) {}
      // Also attempt to scroll selected row into view directly in case listeners run later
      try { if (window.__dashScrollSelected) window.__dashScrollSelected(); } catch (e) {}
    };
  } catch (e) {}

  // default to latest and broadcast selection
  let initial = (data.runs || [])[data.runs.length - 1] || {};
  try {
    const u = new URL(window.location.href);
    const rid = u.searchParams.get('run');
    if (rid) {
      const found = (data.runs || []).find(r => String(r.run_id) === String(rid));
      if (found) initial = found;
    }
  } catch (e) {}
  if (window.__dashSetRows) window.__dashSetRows(initial);
  // register click
  const chart = document.getElementById("chart");
  if (chart) {
    chart.addEventListener("plotly_click", (ev) => {
      const p = ev && ev.points && ev.points[0];
      if (!p) return;
      const idx = p.pointIndex;
      if (idx == null) return;
      const run = data.runs[idx];
      if (run && window.__dashSetRows) {
        try { window.__dashSelOrigin = 'chart'; } catch (e) {}
        window.__dashSetRows(run);
      }
    });
  }
}

function renderTopTests(data) {
  const C = getThemeColors();
  const totalFails = data.top_failing_total_fails || 0;
  const section = document.getElementById("top-tests-section");
  const empty = document.getElementById("top-tests-empty");
  const chartDivId = "top-tests-chart";
  const tbl = document.getElementById("table-tests");
  const tbody = tbl ? tbl.querySelector("tbody") : null;
  if (!section || !empty || !tbody) return;
  tbody.innerHTML = "";
  if (!totalFails) {
    empty.style.display = "block";
    try { section.classList.add("is-empty"); } catch (e) {}
    const c = document.getElementById(chartDivId);
    if (c) { c.innerHTML = ""; c.style.display = "none"; }
    if (tbl) tbl.style.display = "none";
    const more = document.getElementById("top-tests-more");
    if (more) more.style.display = "none";
    return;
  }
  empty.style.display = "none";
  try { section.classList.remove("is-empty"); } catch (e) {}
  if (tbl) tbl.style.display = "table";
  const items = (data.top_failing_tests || []).slice();
  // Normalize potential legacy shape
  for (const t of items) {
    if (t.fail_count != null && t.fails == null) t.fails = t.fail_count;
  }
  // Show up to top 10 immediately (no incremental "next 5")
  const topN = items.slice(0, 10);
  // Chart
  // Prefer new chart container id, fallback to legacy if not present
  const newChartId = (document.getElementById('top-failing-tests')) ? 'top-failing-tests' : chartDivId;
  const cShow = document.getElementById(newChartId);
  if (cShow) cShow.style.display = "block";
  try {
    // Truncate/hide long test names for axis labels; keep full name for hover
    const TRUNC_LEN = 24; // hide labels longer than this
    const yFull = topN.map((t) => String(t.id || "?"));
    const yCats = yFull.slice(); // real categories used by Plotly
    const x = topN.map((t) => Number(t.fails || 0));

    // Axis tick text: empty if over limit (we still show full name on hover)
    const tickText = yFull.map((name) =>
      name.length > TRUNC_LEN ? "" : name
    );

    const base = chartLayoutBase();

    // --- Dynamic left margin based on what we actually render (may be empty) ---
    const _font = '12px "Open Sans", Arial, sans-serif';
    const labelsForWidth = tickText.filter(Boolean);
    const _yMaxPx = labelsForWidth.length ? __maxLabelWidthPx(labelsForWidth, _font) : 0;
    // If labels are empty, we can keep a tight left margin
    const marginL = labelsForWidth.length
      ? Math.max(120, Math.min(360, Math.ceil(_yMaxPx + 16)))
      : 80;

    // Provide extra breathing room at the bottom and slightly smaller axis text
    const marginB = Math.max(40, (base.margin && base.margin.b) || 0);
    const xaxisTitleSize = Math.max(10, ((base.xaxis && base.xaxis.titlefont && base.xaxis.titlefont.size) || 13) - 2);
    const xaxisTickSize = Math.max(10, ((base.xaxis && base.xaxis.tickfont && base.xaxis.tickfont.size) || 12) - 1);

    Plotly.newPlot(
      newChartId,
      [
        {
          x,
          y: yCats,
          type: "bar",
          orientation: "h",
          marker: { color: C.fail, line: { width: 0, color: "transparent" } },
          customdata: yFull, // full test names for hover
          hovertemplate: "%{customdata}<br>Fails: %{x}<extra></extra>",
          insidetextanchor: "middle",
        },
      ],
      Object.assign(
        {},
        base,
        {
          // Allow responsive autosizing; remove fixed width
          autosize: true,
          margin: Object.assign({}, base.margin, { l: marginL, r: 24, b: marginB }),
          bargap: 0.45,
          xaxis: Object.assign({}, base.xaxis, {
            title: 'Fails',
            fixedrange: true,
            titlefont: Object.assign({}, (base.xaxis && base.xaxis.titlefont) || {}, { size: xaxisTitleSize }),
            tickfont: Object.assign({}, (base.xaxis && base.xaxis.tickfont) || {}, { size: xaxisTickSize }),
          }),
          yaxis: Object.assign({}, base.yaxis, {
            automargin: true,
            ticklabelposition: 'outside left',
            ticklabeloverflow: 'allow',
            tickmode: 'array',
            tickvals: yCats,
            ticktext: tickText
          }),
        }
      ),
      { displayModeBar: false, responsive: true }
    );
    ensureMinPlotWidth(newChartId, 520);
  } catch (e) {
    // ignore chart failure
  }
  // Table (compact 4 rows)
  const rows = items.slice(0, 10);
  for (const t of rows) {
    const tr = document.createElement("tr");
    const name = String(t.id || "?");
    const short = name.length > 64 ? name.slice(0, 61) + "…" : name;
    const flaky = !!t.flaky;
    const flakyBadge = `<span class="chip ${flaky ? 'flaky-yes' : 'flaky-no'}">${flaky ? 'yes' : 'no'}</span>`;
    const last = t.last_failed_run || "-";
    const linkIcon = t.path
      ? '<svg aria-hidden="true" viewBox="0 0 24 24" width="14" height="14" style="vertical-align:-2px;margin-left:6px"><path d="M14 3h7v7" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><path d="M21 3l-8 8" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>'
      : "";
    const cellTest = (data.runs && data.runs.length)
      ? (function(){
          // Build link to the latest run where it failed. If per-test path is unavailable,
          // fall back to the run report root URL so the name is still clickable.
          const rid = t.last_failed_run;
          const run = (data.runs || []).find((r)=> String(r.run_id) === String(rid)) || {};
          const base = run.report_url || null;
          if (base) {
            const url = encodeURI(String(base)) + (t.path ? encodeURI(String(t.path)) : "");
            const aria = `Open ${esc(short)} in latest failed run`;
            return `<a class="test-link" href="${url}" target="_blank" rel="noopener noreferrer" title="Open in report" aria-label="${aria}">${esc(short)}${linkIcon}</a>`;
          }
          return `<span title="${esc(name)}">${esc(short)}</span>`;
        })()
      : `<span title="${esc(name)}">${esc(short)}</span>`;
    tr.innerHTML =
      `<td>${cellTest}</td>` +
      `<td>${Number(t.fails || 0)}</td>` +
      `<td>${flakyBadge}</td>` +
      `<td><code>${esc(last)}</code></td>`;
    tbody.appendChild(tr);
  }
  const more = document.getElementById("top-tests-more");
  if (more) {
  const show = items.length > 10;
    more.style.display = show ? "block" : "none";
    if (show) {
      try {
        const link = document.getElementById('top-tests-viewall');
        if (link) {
          // Link to the runs index which provides full browsing/sorting
          // Build absolute path robustly from current location
          const href = computeRunsIndexHref();
          link.setAttribute('href', href);
          link.setAttribute('target', '_blank');
          link.setAttribute('rel', 'noopener noreferrer');
          link.setAttribute('title', 'Open runs index to explore more failing tests');
        }
      } catch (e) {}
    }
  }
}

function renderLastUpdated(built_at) {
  const el = document.getElementById("last-updated");
  if (!el) return;
  const ts = built_at || Math.floor(Date.now() / 1000);
  const now = Math.floor(Date.now() / 1000);
  const diff = Math.max(0, now - ts);
  function fmtAgo(s) {
    if (s < 60) return "just now";
    const m = Math.floor(s / 60);
    if (m < 60) return `${m}m ago`;
    const h = Math.floor(m / 60);
    if (h < 24) return `${h}h ago`;
    const d = Math.floor(h / 24);
    return `${d}d ago`;
  }
  const d = new Date(ts * 1000);
  el.textContent = `Last updated ${fmtAgo(diff)}`;
  el.title = `Built at ${d.toLocaleString()} (${d
    .toISOString()
    .replace("T", " ")
    .replace(".000Z", " UTC")})`;
}

async function boot() {
  let data;
  try {
    data = await loadData();
  } catch (e) {
    console.error("[dashboard] Failed to load data", e);
    const kEl = document.getElementById("kpis");
    if (kEl) {
      kEl.innerHTML =
        '<div class="panel" style="border-style:dashed; padding:12px">' +
        '<div style="font-weight:600; margin-bottom:4px">Unable to load dashboard data</div>' +
        '<div class="subtle">The data file may be missing or still propagating. Refresh in a few seconds.</div>' +
        "</div>";
    }
    return;
  }

  renderLastUpdated(data.built_at);

  // Wire the header "Runs index" pill using the discovered prefix
  try {
    const link = document.getElementById('back-to-runs');
    if (link) {
      const href = computeRunsIndexHref();
      link.setAttribute('href', href);
      link.style.display = 'inline-block';
    }
  } catch (e) {}

  // KPIs
  const k = data.kpis || {};
  const kEl = document.getElementById("kpis");
  // Compute deltas vs prior 10 runs locally (do not rely on backend deltas)
  const runsForDelta = (data.runs || []).slice();
  const latestRun = runsForDelta.length ? runsForDelta[runsForDelta.length - 1] : null;
  const windowStart = Math.max(0, runsForDelta.length - 11); // 10 prior runs + latest
  const prior = runsForDelta.slice(windowStart, Math.max(windowStart, runsForDelta.length - 1));
  function avg(arr) {
    if (!arr || !arr.length) return 0;
    let s = 0, n = 0;
    for (const v of arr) {
      const x = Number(v);
      if (!Number.isNaN(x)) { s += x; n += 1; }
    }
    return n ? s / n : 0;
  }
  const priorPassAvg = avg(prior.map(r => (r && r.pass_percent != null) ? Number(r.pass_percent) : 0));
  const priorFailAvg = avg(prior.map(r => (r && r.failed != null) ? Number(r.failed) : 0));
  const priorDurAvg  = avg(prior.map(r => (r && r.duration_seconds != null) ? Number(r.duration_seconds) : 0));
  const dPass = latestRun ? (Number(latestRun.pass_percent || 0) - priorPassAvg) : 0;
  const dFail = latestRun ? (Number(latestRun.failed || 0) - priorFailAvg) : 0;
  const dDur  = latestRun ? (Number(latestRun.duration_seconds || 0) - priorDurAvg) : 0;
  function card(title, val, delta, tooltip = "") {
    const d = typeof delta === "number" && !Number.isNaN(delta) ? delta : null;
    const trend =
      d == null
        ? { sym: "—", cls: "neutral", text: "—" }
        : d > 0
        ? { sym: "▲", cls: "up", text: signed_delta(d) }
        : d < 0
        ? { sym: "▼", cls: "down", text: signed_delta(d) }
  : { sym: "±", cls: "neutral", text: "0" };
    // Safety: ensure we never render a duplicated sign like "± ± 0" if text already
    // includes a sign character (e.g. legacy bundles or external CSS/pseudo-content).
    // We only de-sign the text when the displayed symbol is our neutral "±".
    let trendText = String(trend.text == null ? "" : trend.text);
    if (trend.sym === "±") {
      trendText = trendText.replace(/^\s*±\s*/, "");
    }
    // Debug: help trace any unexpected renders of delta text
    try {
      if (window.__DEBUG_DASH) {
        // eslint-disable-next-line no-console
        console.debug("[dash:kpi]", title, { value: val, delta: d, trend });
      }
    } catch (e) {}
    return (
      '<div class="card" title="' +
      (tooltip || "") +
      '"><div class="t">' +
      title +
      "</div><div class=\"v\">" +
      val +
      ' <span class="delta ' +
      trend.cls +
      '" role="status" aria-live="polite" data-delta="' +
      (d == null ? '' : (d > 0 ? 'up' : d < 0 ? 'down' : 'neutral')) +
      '"><span class="sym" aria-hidden="true">' +
      trend.sym +
      '</span> <span class="text">' +
      trendText +
      "</span></span></div></div>"
    );
  }
  const passPct = format_percent(k.latest_pass || 0, 1);
  const failVal = nf0.format(k.latest_fail || 0);
  const durAvg = format_duration(k.avg_duration_last10 || k.latest_duration || 0);
  const passTip = "Pass% = Passed / (Passed + Failed + Broken)";
  const streak = k.streak || 0;
  const lastPerf = k.last_perfect_ago || 0;
  const streakCopy =
    streak > 0
      ? `Healthy streak: ${streak} perfect runs`
      : '<span class="chip subtle">No perfect runs yet</span>';
  const lastPerfCopy = streak > 0 ? `Last perfect run: ${lastPerf} ago` : "";
  if (kEl)
    kEl.innerHTML =
      card(
        "Pass%",
        passPct,
        dPass,
        `${signed_delta(dPass, "%")} vs prior 10 runs`
      ) +
      card(
        "Failures",
        failVal,
        dFail,
        `${signed_delta(dFail, "")} vs prior 10 runs`
      ) +
      card(
        "Avg Duration (10)",
        durAvg,
        dDur,
        `${signed_delta(dDur, "s")} vs prior 10 runs`
      ) +
      (streakCopy ? '<span class="chip" style="margin-left:6px">' + streakCopy + "</span>" : "") +
      (lastPerfCopy ? '<span class="chip">' + lastPerfCopy + "</span>" : "");

  // Charts (only if Plotly available)
  try {
    await ensurePlotly();
    if (typeof Plotly !== "undefined") {
      stackedAndRate("chart", data);
      // Prefer new sidebar container if present; fallback to legacy
      const suitesTarget = document.getElementById('failures-by-area') ? 'failures-by-area' : 'suites';
      suitesBar(suitesTarget, data);
      // Nudge Plotly to recalc after grid applies
      try {
        const gd = document.getElementById('chart');
        if (gd && window.Plotly && window.Plotly.Plots && window.Plotly.Plots.resize) {
          window.Plotly.Plots.resize(gd);
          setTimeout(() => { try { window.Plotly.Plots.resize(gd); } catch (e) {} }, 60);
        }
      } catch (e) {}
    }
  } catch (e) {
    console.warn(e);
  }

  // Details and tables
  drillTable("run-info", data);
  let selectedRunId = (data.runs || [])[Math.max(0, (data.runs || []).length - 1)]?.run_id || null;

  // Keep table highlight in sync when selection changes elsewhere
  // Expose a helper to scroll the current selected row into view
  window.__dashScrollSelected = function() {
    try {
      const row = document.querySelector('#runs-table tbody tr.is-active');
      if (!row) return;
      const section = document.getElementById('recent-runs');
      if (section && section.scrollIntoView) {
        section.scrollIntoView({ behavior: 'auto', block: 'start', inline: 'nearest' });
      }
      const center = () => { try { row.scrollIntoView({ behavior: 'auto', block: 'center', inline: 'nearest' }); } catch (e) {} };
      center();
      setTimeout(center, 60);
    } catch (e) {}
  };

  document.addEventListener("run:selected", (ev) => {
    selectedRunId = ev && ev.detail ? ev.detail : null;
    // If the selected run is off the current page window, auto-page to it
    try {
      if (selectedRunId) {
        // Recompute the same sorted/filtered list used by renderRunsTable()
        let runsAll = (data.runs || []).slice();
        // Apply current filter query if present
        try {
          const qEl = document.getElementById('run-filter');
          const qRaw = qEl ? (qEl.value || '').trim().toLowerCase() : '';
          if (qRaw) {
            runsAll = runsAll.filter((r) => {
              const hay = [r.run_id, r.branch, r.commit, r.triggered_by, r.environment]
                .filter(Boolean)
                .map((x)=>String(x).toLowerCase())
                .join(' ');
              return hay.includes(qRaw);
            });
          }
        } catch (e) {}
        // Apply current sort settings from the table header
        try {
          const table = document.getElementById('runs-table');
          const sortKey = (table && table.getAttribute('data-sort-key')) || 'time';
          const sortDir = (table && table.getAttribute('data-sort-dir')) || 'desc';
          runsAll.sort((a,b) => {
            const va = a[sortKey];
            const vb = b[sortKey];
            const cmp = va === vb ? 0 : (va > vb ? 1 : -1);
            return sortDir === 'desc' ? -cmp : cmp;
          });
        } catch (e) {}
        const idx = runsAll.findIndex((r) => String(r.run_id) === String(selectedRunId));
        if (idx >= 0) {
          const { pageSize, setPage, getPageForIndex } = pagerApi;
          const p = getPageForIndex(idx, pageSize());
          setPage(p);
        }
      }
    } catch (e) {}
    renderRunsTable();
    // Smoothly scroll selected row into view after render
    try {
      function scrollAfterRender() {
        const row = document.querySelector('#runs-table tbody tr.is-active');
        if (!row) return;
        try { row.focus({ preventScroll: false }); } catch (e) { try { row.focus(); } catch (e2) {} }
        // Bring the recent runs section into view first
        try {
          const section = document.getElementById('recent-runs');
          if (section && section.scrollIntoView) {
            section.scrollIntoView({ behavior: 'auto', block: 'start', inline: 'nearest' });
          }
        } catch (e) {}
        // Center the selected row in the viewport deterministically
        const center = () => {
          try { row.scrollIntoView({ behavior: 'auto', block: 'center', inline: 'nearest' }); } catch (e) {}
        };
        center();
        setTimeout(center, 80);
      }
      // Double-rAF to ensure DOM has painted
      requestAnimationFrame(() => requestAnimationFrame(scrollAfterRender));
    } catch (e) {}
  });

  function renderRunsTable() {
    const table = document.getElementById("runs-table");
    const tb = table ? table.querySelector("tbody") : null;
    if (!tb) return;
    tb.innerHTML = "";
    let runsAll = (data.runs || []).slice();
    const sortKey = (table && table.getAttribute("data-sort-key")) || "time";
    const sortDir = (table && table.getAttribute("data-sort-dir")) || "desc";
    runsAll.sort((a,b) => {
      const va = a[sortKey];
      const vb = b[sortKey];
      const cmp = va === vb ? 0 : (va > vb ? 1 : -1);
      return sortDir === "desc" ? -cmp : cmp;
    });
    // Filter runs by query (substring across run_id, branch, commit, triggered_by, environment)
    try {
      const qEl = document.getElementById('run-filter');
      const qRaw = qEl ? (qEl.value || '').trim().toLowerCase() : '';
      if (qRaw) {
        runsAll = runsAll.filter((r) => {
          const hay = [r.run_id, r.branch, r.commit, r.triggered_by, r.environment]
            .filter(Boolean)
            .map((x)=>String(x).toLowerCase())
            .join(' ');
          return hay.includes(qRaw);
        });
      }
    } catch (e) {}
    // Pagination window
  const { pageSize, pageIndex, totalPages, slice } = pagerApi;
  const win = slice(runsAll, pageIndex(), pageSize());
  updatePagerUi(totalPages(runsAll.length, pageSize()));

    for (let i = 0; i < win.length; i++) {
      const r = win[i];
      const tr = document.createElement("tr");
      if ((r.failed||0) > 0 || (r.broken||0) > 0) {
        tr.style.background = "rgba(220,38,38,0.06)";
      }
      tr.setAttribute("tabindex", "0");
      if (r.run_id && r.run_id === selectedRunId) {
        tr.classList.add("is-active");
        tr.setAttribute("aria-selected", "true");
      }
      tr.addEventListener("keydown", (ev) => {
        if (ev.key === "Enter" || ev.key === " ") {
          ev.preventDefault();
          tr.click();
        }
      });
      const runIdCell = (function(){
        const runIdText = r.run_id || "-";
        if (r.report_url) {
          const url = encodeURI(r.report_url);
          return `<a class="run-link" href="${url}" target="_blank" rel="noopener noreferrer" title="Open Report"><code>${esc(runIdText)}</code></a>`;
        }
        return `<code>${esc(runIdText)}</code>`;
      })();
      const commitShort = (r.commit || "").slice(0,7);
      const passPct = r.pass_percent || 0;
      let passCls = "";
      if (passPct >= 95) passCls = "color:#16a34a";
      else if (passPct >= 75) passCls = "color:#f59e0b";
      else passCls = "color:#dc2626";
      const passTip = `${nf0.format(r.passed||0)} passed, ${nf0.format(r.failed||0)} failed, ${nf0.format(r.broken||0)} broken${r.skipped?`, ${nf0.format(r.skipped)} skipped`:''}`;
      tr.innerHTML =
        `<td style="font-family:ui-monospace,Menlo,monospace">${runIdCell}</td>` +
        `<td title="${esc(r.branch||'')}">${esc(r.branch||'-')}</td>` +
        `<td title="${esc(r.commit||'')}">${esc(commitShort||'-')}</td>` +
        `<td title="${esc(r.triggered_by||'')}">${esc(r.triggered_by||'-')}</td>` +
        `<td title="${esc(r.environment||'')}">${esc(r.environment||'-')}</td>` +
        `<td title="${passTip}" style="${passCls}">${format_percent(passPct, 1)}</td>` +
        `<td>${nf0.format(r.failed || 0)}</td>` +
        `<td>${nf0.format(r.broken || 0)}</td>` +
        `<td>${format_duration(r.duration_seconds || 0)}</td>`;
      tr.style.cursor = "pointer";
      const summary = (
        `Run ${esc(r.run_id||'-')} — ` +
        `Pass ${format_percent(passPct,1)} ` +
        `(${nf0.format(r.passed||0)}/${nf0.format(r.failed||0)}/${nf0.format(r.broken||0)}) — ` +
        `Duration ${format_duration(r.duration_seconds||0)}`
      );
      tr.title = summary;
      tr.addEventListener("click", (ev) => {
        if (ev.target && ev.target.closest && ev.target.closest('.run-link')) return;
        // Drive global selection so panel and table stay in sync
        if (window.__dashSetRows) {
          try { window.__dashSelOrigin = 'table'; } catch (e) {}
          window.__dashSetRows(r);
        }
      });
      tb.appendChild(tr);
    }

    // One-time header click sorting binding (robust: delegate + direct th binding)
    if (table && !table.getAttribute('data-sort-bound')) {
      const thead = table.querySelector('thead');
      const applySort = (th) => {
        if (!th || !th.parentNode) return;
        const idx = Array.from(th.parentNode.children).indexOf(th);
        const map = {
          0:'run_id',1:'branch',2:'commit',3:'triggered_by',4:'environment',
          5:'pass_percent',6:'failed',7:'broken',8:'duration_seconds'
        };
        const key = map[idx];
        if (!key) return;
        const curKey = table.getAttribute('data-sort-key') || 'time';
        const curDir = table.getAttribute('data-sort-dir') || 'desc';
        const nextDir = (curKey === key && curDir === 'desc') ? 'asc' : 'desc';
        table.setAttribute('data-sort-key', key);
        table.setAttribute('data-sort-dir', nextDir);
        // a11y: update aria-sort on headers
        if (thead) {
          const headers = thead.querySelectorAll('th');
          headers.forEach(h => h.removeAttribute('aria-sort'));
          th.setAttribute('aria-sort', nextDir === 'asc' ? 'ascending' : 'descending');
        }
        renderRunsTable();
      };
      if (thead) {
        // Delegate on thead for general clicks
        thead.addEventListener('click', (ev) => {
          const target = ev && ev.target && ev.target.closest ? ev.target.closest('th') : null;
          if (target) applySort(target);
        });
        // Direct binding on each th to avoid delegation edge cases
        thead.querySelectorAll('th').forEach((th) => {
          th.addEventListener('click', () => applySort(th));
        });
      }
      // Initialize sort attributes so observers have a stable base
      if (!table.getAttribute('data-sort-key')) table.setAttribute('data-sort-key', 'time');
      if (!table.getAttribute('data-sort-dir')) table.setAttribute('data-sort-dir', 'desc');
      table.setAttribute('data-sort-bound','1');
    }
  }
  // Expose so pagination controls can trigger re-render
  try { window.__dashRenderRunsTable = renderRunsTable; } catch (e) {}
  renderRunsTable();
  renderTopTests(data);
  // Initialize pager UI counts after first render
  try {
    const total = (data.runs || []).length;
    const pages = pagerApi.totalPages(total, pagerApi.pageSize());
    updatePagerUi(pages);
  } catch (e) {}

  // Render compact Top Failures hybrid card
  try {
    const list = document.getElementById("top-failures-list");
    const miniId = "top-failures-mini";
    if (list) {
      const items = (data.top_failing_tests || []).slice(0, 3);
      list.innerHTML = "";
      for (const t of items) {
        const li = document.createElement("li");
        const name = String(t.id || "?");
        const short = name.length > 64 ? name.slice(0, 61) + "…" : name;
        li.textContent = short + " (" + (t.fails || t.fail_count || 0) + ")";
        list.appendChild(li);
      }
      if (items.length && typeof Plotly !== "undefined") {
        const x = items.map((t) => Number(t.fails || t.fail_count || 0)).reverse();
        const yFullMini = items.map((t) => String(t.id || "?")).reverse();
        const TRUNC_LEN_MINI = 24;
        const tickTextMini = yFullMini.map((name) => (name.length > TRUNC_LEN_MINI ? "" : name));

        const C = getThemeColors();

        // Tight left margin if all labels are hidden
        const labelsForWidthMini = tickTextMini.filter(Boolean);
        const _fontMini = '11px "Open Sans", Arial, sans-serif';
        const maxPxMini = labelsForWidthMini.length ? __maxLabelWidthPx(labelsForWidthMini, _fontMini) : 0;
        const leftMini = labelsForWidthMini.length ? Math.max(90, Math.min(220, Math.ceil(maxPxMini + 14))) : 60;

        Plotly.newPlot(
          miniId,
          [
            {
              x,
              y: yFullMini,
              type: "bar",
              orientation: "h",
              marker: { color: C.fail, line: { width: 0, color: "transparent" } },
              customdata: yFullMini,
              hovertemplate: "%{customdata}<br>Fails: %{x}<extra></extra>",
            },
          ],
          {
            margin: { t: 4, r: 10, b: 10, l: leftMini },
            xaxis: { tickfont: { size: 11 }, fixedrange: true },
            yaxis: {
              tickfont: { size: 11 },
              tickmode: 'array',
              tickvals: yFullMini,
              ticktext: tickTextMini,
              automargin: true
            },
          },
          { displayModeBar: false, responsive: true }
        );
      } else {
        // v2: keep card height but show empty message subtly
        try {
          if (isPolishV2()) {
            const mini = document.getElementById(miniId);
            if (mini) { mini.innerHTML = '<div class="subtle" style="text-align:center; padding:8px">No recent failures</div>'; }
          }
        } catch (e) {}
      }
    }
  } catch (e) {}

  // (More columns toggle removed per request)
}

// --- Pagination helpers ----------------------------------------------------
const pagerApi = (function(){
  let _page = 1; // 1-based
  let _size = 20;
  function readQueryDefaults(){
    try {
      const u = new URL(window.location.href);
      const ps = parseInt(u.searchParams.get('ps') || '', 10);
      const pn = parseInt(u.searchParams.get('p') || '', 10);
      if (!Number.isNaN(ps) && ps > 0) {
        _size = ps;
      } else {
        // Fallback to body data attribute if present
        const fromBody = parseInt((document.body.getAttribute('data-page-size') || ''), 10);
        if (!Number.isNaN(fromBody) && fromBody > 0) _size = fromBody;
      }
      if (!Number.isNaN(pn) && pn > 0) _page = pn;
    } catch (e) {}
  }
  function writeQuery(){
    try {
      const u = new URL(window.location.href);
      u.searchParams.set('ps', String(_size));
      u.searchParams.set('p', String(_page));
      // Preserve ui and run if present
      if (isPolishV2()) u.searchParams.set('ui', 'polish-v2');
      window.history.replaceState({}, '', u.toString());
    } catch (e) {}
  }
  function pageSize(){ return _size; }
  function pageIndex(){ return Math.max(1, _page); }
  function setPage(n){
    const v = Math.max(1, parseInt(n,10) || 1);
  _page = v; try { if (window.__DEBUG_DASH) console.debug('[dash:pager] setPage ->', v); } catch (e) {}
    writeQuery();
  }
  function setSize(n){
    const v = Math.max(1, parseInt(n,10) || 20);
  _size = v; _page = 1; try { if (window.__DEBUG_DASH) console.debug('[dash:pager] setSize ->', v); } catch (e) {}
    writeQuery();
  }
  function totalPages(total, size){
    const s = Math.max(1, size);
    return Math.max(1, Math.ceil(total / s));
  }
  function getPageForIndex(idx, size){
    const s = Math.max(1, size);
    return Math.floor(idx / s) + 1;
  }
  function slice(arr, page, size){
    const s = Math.max(1, size);
    const p = Math.max(1, page);
    const start = (p - 1) * s;
    return arr.slice(start, start + s);
  }
  readQueryDefaults();
  return { pageSize, pageIndex, setPage, setSize, totalPages, slice, getPageForIndex };
})();

function updatePagerUi(totalPagesCount){
  try {
    const elCur = document.getElementById('page-cur');
    const elTot = document.getElementById('page-total');
    const sel = document.getElementById('page-size');
    const bPrev = document.getElementById('page-prev');
    const bNext = document.getElementById('page-next');
    if (!elCur || !elTot || !sel || !bPrev || !bNext) return;
    elCur.textContent = String(pagerApi.pageIndex());
    elTot.textContent = String(totalPagesCount);
    // Sync select
    const want = String(pagerApi.pageSize());
    if (sel.value !== want) sel.value = want;
    // Disable/enable buttons
    const p = pagerApi.pageIndex();
    bPrev.disabled = p <= 1;
    bNext.disabled = p >= totalPagesCount;
  try { if (window.__DEBUG_DASH) console.debug('[dash:pager] UI updated:', { p, totalPagesCount, size: pagerApi.pageSize(), prevDisabled: bPrev.disabled, nextDisabled: bNext.disabled }); } catch (e) {}
  } catch (e) {}
}

window.addEventListener('DOMContentLoaded', () => {
  try {
    const sel = document.getElementById('page-size');
    const bPrev = document.getElementById('page-prev');
    const bNext = document.getElementById('page-next');
    const qEl = document.getElementById('run-filter');
    const loadWrap = document.getElementById('load-more-wrap');
    const loadBtn = document.getElementById('load-more');
    // Early header sorting binding to avoid race with data boot
    try {
      const table = document.getElementById('runs-table');
      const thead = table ? table.querySelector('thead') : null;
      if (table && thead && !table.getAttribute('data-sort-bound')) {
        // Initialize default sort attributes
        if (!table.getAttribute('data-sort-key')) table.setAttribute('data-sort-key', 'time');
        if (!table.getAttribute('data-sort-dir')) table.setAttribute('data-sort-dir', 'desc');
        const applySortEarly = (th) => {
          if (!th || !th.parentNode) return;
          const idx = Array.from(th.parentNode.children).indexOf(th);
          const map = { 0:'run_id',1:'branch',2:'commit',3:'triggered_by',4:'environment',5:'pass_percent',6:'failed',7:'broken',8:'duration_seconds' };
          const key = map[idx];
          if (!key) return;
          const curKey = table.getAttribute('data-sort-key') || 'time';
          const curDir = table.getAttribute('data-sort-dir') || 'desc';
          const nextDir = (curKey === key && curDir === 'desc') ? 'asc' : 'desc';
          table.setAttribute('data-sort-key', key);
          table.setAttribute('data-sort-dir', nextDir);
          // Update aria-sort for a11y
          try {
            const hs = thead.querySelectorAll('th');
            hs.forEach(h => h.removeAttribute('aria-sort'));
            th.setAttribute('aria-sort', nextDir === 'asc' ? 'ascending' : 'descending');
          } catch (e) {}
          // Trigger render if available
          try { if (window.__dashRenderRunsTable) window.__dashRenderRunsTable(); } catch (e) {}
        };
        thead.addEventListener('click', (ev) => {
          const target = ev && ev.target && ev.target.closest ? ev.target.closest('th') : null;
          if (target) applySortEarly(target);
        });
        // Mark as bound to prevent duplicate bindings later
        table.setAttribute('data-sort-bound', '1');
      }
    } catch (e) {}
    // Optional load-more mode if body[data-paging="load-more"]
    try {
      const isLoadMore = (document.body.getAttribute('data-paging') || '').toLowerCase() === 'load-more';
      if (isLoadMore) {
        if (loadWrap) loadWrap.style.display = 'block';
        const btns = document.getElementById('pager-btns');
        if (btns) btns.style.display = 'none';
      }
      if (isLoadMore && loadBtn) {
        loadBtn.addEventListener('click', () => {
          pagerApi.setSize(pagerApi.pageSize() + 20);
          try { if (window.__dashRenderRunsTable) window.__dashRenderRunsTable(); } catch (e) {}
        });
      }
    } catch (e) {}
    if (sel) {
      sel.addEventListener('change', () => {
  try { if (window.__DEBUG_DASH) console.debug('[dash:pager] change page-size ->', sel.value); } catch (e) {}
        pagerApi.setSize(parseInt(sel.value, 10));
        // Re-render table on size change
        try { if (window.__dashRenderRunsTable) window.__dashRenderRunsTable(); } catch (e) {}
      });
    }
  if (bPrev) bPrev.addEventListener('click', () => { try { if (window.__DEBUG_DASH) console.debug('[dash:pager] click prev'); } catch (e) {} pagerApi.setPage(pagerApi.pageIndex() - 1); try { if (window.__dashRenderRunsTable) window.__dashRenderRunsTable(); } catch (e) {} });
  if (bNext) bNext.addEventListener('click', () => { try { if (window.__DEBUG_DASH) console.debug('[dash:pager] click next'); } catch (e) {} pagerApi.setPage(pagerApi.pageIndex() + 1); try { if (window.__dashRenderRunsTable) window.__dashRenderRunsTable(); } catch (e) {} });
    if (qEl) {
      const onInput = () => { try { if (window.__dashRenderRunsTable) window.__dashRenderRunsTable(); } catch (e) {} };
      qEl.addEventListener('input', onInput);
      qEl.addEventListener('change', onInput);
    }
  } catch (e) {}
});

// Debounced resize for charts
let __dashResizeTimer = null;
function __dashResizeAll() {
  try {
    // Ensure tiny charts get widened on resize
    ensureMinPlotWidth('failures-by-area', 520);
    ensureMinPlotWidth('top-failing-tests', 520);
    ensureMinPlotWidth('top-tests-chart', 520);
    ensureMinPlotWidth('suites', 520);
    if (!window.Plotly || !window.Plotly.Plots || !window.Plotly.Plots.resize) return;
    ["chart", "suites", "failures-by-area", "top-failing-tests", "top-tests-chart", "top-failures-mini"].forEach((id) => {
      const el = document.getElementById(id);
      if (el) { try { window.Plotly.Plots.resize(el); } catch (e) {} }
    });
  } catch (e) {}
}
window.addEventListener('resize', () => {
  if (__dashResizeTimer) clearTimeout(__dashResizeTimer);
  __dashResizeTimer = setTimeout(__dashResizeAll, 150);
});

window.addEventListener("DOMContentLoaded", () => { ensureUiFlagFromQuery(); boot(); });

// Slightly increase chart width responsiveness
window.addEventListener('load', () => {
  try {
    const style = document.createElement('style');
    style.textContent = `
      #top-failing-tests, #failures-by-area, #top-tests-chart, #suites {
        width: 100% !important;
        min-width: 520px !important;
        max-width: 100% !important;
      }
      @media (max-width: 640px) {
        #top-failing-tests, #failures-by-area, #top-tests-chart, #suites {
          min-width: 320px !important;
        }
      }
    `;
    document.head.appendChild(style);
    ensureMinPlotWidth('failures-by-area', 520);
    ensureMinPlotWidth('top-failing-tests', 520);
    setTimeout(() => {
      if (window.Plotly && window.Plotly.Plots && window.Plotly.Plots.resize) {
        ['top-failing-tests', 'failures-by-area'].forEach(id => {
          const el = document.getElementById(id);
          if (el) try { window.Plotly.Plots.resize(el); } catch (e) {}
        });
      }
    }, 100);
  } catch (e) {}
});
