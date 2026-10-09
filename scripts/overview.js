// Owner state stays authoritative. Validation/observation follow the cockpit v1 contract.
const STATUSES = ["green", "yellow", "red", "stale", "grey"];
const SEVERITIES = ["red", "yellow", "info"];
function esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, c =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function safeUrl(u) {
  if (typeof u !== "string" || !/^https?:\/\//i.test(u)) return null;
  try { const url = new URL(u); return url.hostname ? url.href : null; } catch (e) { return null; }
}
function age(iso) {
  const t = Date.parse(iso);
  if (isNaN(t)) return "unknown age";
  let s = Math.max(0, Math.round((Date.now() - t) / 1000));
  if (s < 60) return s + "s ago";
  const m = Math.round(s / 60); if (m < 60) return m + "m ago";
  const h = Math.round(m / 60); if (h < 48) return h + "h ago";
  return Math.round(h / 24) + "d ago";
}

// Additive v1 metadata: older producers need no migration.
const ITEM_STATES = ["healthy", "active", "stale", "blocked", "failed", "action_required", "unknown"];
const ACTION_SAFETY = ["read_only", "requires_approval", "scientific_judgement", "never_automatic", "unclassified"];
const oneLine = v => typeof v === "string" && v.trim() !== "" && !/[\r\n]/.test(v);
function utcTime(v) {
  if (typeof v !== "string" || !/T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)$/.test(v)) return NaN;
  const t = Date.parse(v);
  // Date.parse normalizes impossible dates such as February 30.
  return Number.isFinite(t) && new Date(t).toISOString().slice(0, 19) === v.slice(0, 19) ? t : NaN;
}
function validate(d, organ = null) {
  if (!d || typeof d !== "object" || Array.isArray(d)) return "not an object";
  if (d.schema_version !== 1) return "schema_version " + d.schema_version;
  if (!STATUSES.includes(d.status)) return "invalid status";
  if (![d.organ, d.repo, d.pages_url, d.headline].every(oneLine)) return "missing identity or headline";
  if (organ && (d.organ !== organ.organ.toLowerCase() || d.repo !== organ.repo)) return "wrong organ";
  if (!Number.isFinite(utcTime(d.updated))) return "invalid updated timestamp";
  if ("valid_until" in d && (!Number.isFinite(utcTime(d.valid_until)) || utcTime(d.valid_until) < utcTime(d.updated))) return "invalid valid_until";
  if (!Array.isArray(d.items)) return "no items";
  const ids = new Set();
  for (const it of d.items) {
    if (!it || !SEVERITIES.includes(it.severity) || !oneLine(it.text)) return "bad item";
    for (const key of ["url", "prompt"]) if (it[key] != null && typeof it[key] !== "string") return "bad " + key;
    for (const key of ["id", "reason", "decision", "recommended_action_id"]) if (key in it && !oneLine(it[key])) return "bad " + key;
    if ("id" in it) { if (ids.has(it.id)) return "duplicate item id"; ids.add(it.id); }
    if ("state" in it && !ITEM_STATES.includes(it.state)) return "bad item state";
    if ("requires_human_decision" in it && typeof it.requires_human_decision !== "boolean") return "bad decision flag";
    if (it.requires_human_decision && !oneLine(it.decision)) return "missing decision";
    if ("actions" in it && !Array.isArray(it.actions)) return "bad actions";
    const actions = new Set();
    for (const action of it.actions || []) {
      if (!action || ![action.id, action.label, action.target].every(oneLine)) return "bad action";
      if (!["link", "command", "prompt"].includes(action.kind)) return "bad action kind";
      if ("safety" in action && !ACTION_SAFETY.includes(action.safety)) return "bad action safety";
      if (action.kind === "link" && !safeUrl(action.target)) return "bad action URL";
      if (actions.has(action.id)) return "duplicate action id";
      actions.add(action.id);
    }
    if ("recommended_action_id" in it && !actions.has(it.recommended_action_id)) return "missing recommended action";
  }
  return null;
}

// Pure observation model. Source health and transport/freshness are separate
// facts. Missing expiry means no declared age policy, not infinite freshness.
function observation(st = {}, now = Date.now()) {
  const d = st.feed || st.lastGood || null;
  const base = { feed: d, sourceStatus: d ? d.status : null, lastChecked: st.lastChecked || null };
  if (!d) return { ...base, status: "grey", current: false, freshness: "unknown", reason: st.error || "waiting for first check" };
  if (st.error || !st.feed) return { ...base, status: "stale", current: false, freshness: "unavailable", reason: st.error || "not checked this session" };
  if (!Number.isFinite(utcTime(d.updated)) || utcTime(d.updated) > now) return { ...base, status: "grey", current: false, freshness: "unknown", reason: "source timestamp is invalid or in the future" };
  if (d.valid_until && utcTime(d.valid_until) <= now) return { ...base, status: "stale", current: false, freshness: "expired", reason: "source freshness deadline passed" };
  if (d.status === "stale") return { ...base, status: "stale", current: false, freshness: "expired", reason: "source reports stale evidence" };
  if (d.status === "grey") return { ...base, status: "grey", current: false, freshness: "unknown", reason: "source reports insufficient evidence" };
  return { ...base, status: d.status, current: true, freshness: d.valid_until ? "within_policy" : "unspecified", reason: null };
}


const DOMAIN_LABELS = {
  brain: 'Coordination', mind: 'Tasks', cortex: 'Science', memory: 'Knowledge',
  eyes: 'Figures', ears: 'Conversations', heart: 'Checks', hands: 'Releases',
  pulse: 'Profiling', insight: 'Inference', dna: 'Compatibility', nerves: 'Configuration',
  broca: 'Assistants', gut: 'Cleanup'
};
function concise(text) {
  const words = String(text).trim().split(/\s+/);
  const short = words.slice(0, 12).join(' ');
  return short.slice(0, 130) + (words.length > 12 || short.length > 130 ? '…' : '');
}
function itemUrl(item, fallback) {
  const action = (item.actions || []).find(a => a.kind === 'link' && a.id === item.recommended_action_id)
    || (item.actions || []).find(a => a.kind === 'link');
  return safeUrl(item.url) || safeUrl(action && action.target) || fallback;
}
function needsAttention(item) {
  return item.requires_human_decision || ['failed', 'blocked', 'action_required', 'stale', 'unknown'].includes(item.state)
    || (!item.state && ['red', 'yellow'].includes(item.severity));
}
function summaries(organ, view) {
  const feed = view.feed;
  const url = organ.url;
  if (!feed) return [{ label: 'Evidence', text: 'Unavailable', url }];
  if (!view.current) return [
    { label: 'Evidence', text: view.reason || 'Not verified', url },
    { label: 'Last known', text: feed.headline, url }
  ];
  const rows = [];
  const attention = feed.items.filter(needsAttention).sort((a,b) =>
    Number(!!b.requires_human_decision) - Number(!!a.requires_human_decision)
    || (a.severity === 'red' ? -1 : 0) - (b.severity === 'red' ? -1 : 0));
  if (attention.length) {
    const item = attention[0];
    rows.push({ label: item.requires_human_decision ? 'Your decision' : 'Needs attention',
      text: item.requires_human_decision ? item.decision : item.text, url: itemUrl(item, url) });
  } else {
    rows.push({ label: 'Attention', text: feed.status === 'green' ? 'No action reported' :
      feed.status === 'red' ? 'Review failing status' : 'Review current status', url });
  }
  const active = feed.items.find(item => item.state === 'active' && !attention.includes(item));
  if (active) rows.push({ label: 'In progress', text: active.text, url: itemUrl(active, url) });
  // The release owner already includes the version and event age in its headline.
  // No other headline is promoted to "completed"; updated is never an event date.
  if (!rows.some(row => row.text === feed.headline)) rows.push({
    label: organ.key === 'hands' && /^v?\d{4}\.\d{1,2}\.\d{1,2}\.\d+\s*·/.test(feed.headline)
      ? 'Latest release' : DOMAIN_LABELS[organ.key] || 'Current position', text: feed.headline, url
  });
  return rows.slice(0, 3);
}
function statusLabel(view) {
  if (!view.current) return view.feed ? 'Not verified' : 'Unavailable';
  if (view.feed.items.some(needsAttention)) return 'Needs attention';
  if (view.feed.items.some(item => item.state === 'active')) return 'In progress';
  return { green: 'No action reported', yellow: 'Review', red: 'Needs attention' }[view.status] || 'Unknown';
}
function summaryHtml(rows) {
  return rows.map(row => `<div class="summary-row"><dt>${esc(row.label)}</dt><dd><a href="${esc(safeUrl(row.url) || '#')}" title="${esc(row.text)}">${esc(concise(row.text))}</a></dd></div>`).join('');
}

// ---- browser startup ----
const snapshot = JSON.parse(document.getElementById('scientist-snapshot').textContent);
const organStates = new Map();
for (const organ of snapshot.boards) {
  const identity = { organ: organ.name, repo: organ.repo };
  let saved = null;
  try { saved = JSON.parse(localStorage.getItem('pyauto-cockpit:last-good:' + organ.repo)); } catch (_) {}
  const lastGood = saved && !validate(saved.feed, identity) ? saved.feed :
    organ.feed && !validate(organ.feed, identity) ? organ.feed : null;
  organStates.set(organ.key, { lastGood });
}
function paint(organ) {
  const view = observation(organStates.get(organ.key));
  const card = document.getElementById('board-' + organ.key);
  const badge = card.querySelector('.organ-status');
  badge.textContent = statusLabel(view);
  badge.dataset.status = view.status;
  const list = card.querySelector('dl');
  const markup = summaryHtml(summaries(organ, view));
  if (list.innerHTML !== markup) {
    // Keep a focused evidence link in place even when its text changes.
    const links = [...list.querySelectorAll('a')];
    const focused = links.indexOf(document.activeElement);
    list.innerHTML = markup;
    if (focused >= 0) (list.querySelectorAll('a')[focused] || card.querySelector('summary')).focus({ preventScroll: true });
  }
  const stamp = card.querySelector('[data-freshness]');
  stamp.textContent = view.feed ? `${view.current ? 'Source updated' : 'Last known source'} ${age(view.feed.updated)}` : 'No verified evidence';
  stamp.title = view.feed ? view.feed.updated : '';
}
let refreshing = false;
async function refresh() {
  if (refreshing) return;
  refreshing = true;
  try {
    await Promise.all(snapshot.boards.map(async organ => {
      const st = organStates.get(organ.key);
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 15000);
      try {
        const response = await fetch(organ.url + 'state.json?t=' + Date.now(), { cache: 'no-store', signal: controller.signal });
        if (!response.ok) throw new Error('Evidence unavailable');
        const feed = await response.json();
        if (validate(feed, { organ: organ.name, repo: organ.repo })) throw new Error('Invalid evidence');
        st.feed = feed; st.lastGood = feed; st.error = null;
        try { localStorage.setItem('pyauto-cockpit:last-good:' + organ.repo, JSON.stringify({ feed, at: new Date().toISOString() })); } catch (_) {}
      } catch (_) { st.feed = null; st.error = 'Evidence unavailable'; }
      finally { clearTimeout(timeout); paint(organ); }
    }));
  } finally { refreshing = false; }
}
for (const organ of snapshot.boards) paint(organ);
refresh();
setInterval(refresh, 60000);
document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') refresh(); });
