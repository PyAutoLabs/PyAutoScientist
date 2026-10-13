/* Static, public evidence only. Updating the feed must not move a reader. */
(() => {
'use strict';
const root = document.getElementById('live-feed');
if (!root) return;
const list = root.querySelector('[data-feed-list]');
const more = root.querySelector('[data-feed-more]');
const fresh = root.querySelector('[data-feed-freshness]');
const notice = root.querySelector('[data-feed-notice]');
const incoming = root.querySelector('[data-feed-new]');
const empty = root.querySelector('[data-feed-empty]');
const coverage = root.querySelector('[data-feed-coverage]');
let current, pending, count = 5, refreshing = false, lastChecked = null;
function safeURL(value, host) {
  try { const u = new URL(value); return u.protocol === 'https:' && !u.username && !u.password && (host ? u.hostname === host : u.hostname.endsWith('.github.io')); } catch (_) { return false; }
}
function validate(feed) {
  if (!feed || feed.schema_version !== 1 || !Array.isArray(feed.tasks) || feed.tasks.length > 200 || !Array.isArray(feed.coverage)) throw Error('Invalid activity feed');
  if (feed.generated !== null && !Number.isFinite(Date.parse(feed.generated))) throw Error('Invalid collection time');
  const ids = new Set();
  for (const t of feed.tasks) {
    if (typeof t.id !== 'string' || ids.has(t.id) || typeof t.title !== 'string' || typeof t.board !== 'string' || typeof t.repo !== 'string' || !safeURL(t.board_url) || !Array.isArray(t.events) || !t.events.length || t.events.length > 20) throw Error('Invalid task');
    ids.add(t.id);
    for (const e of t.events) if (typeof e.id !== 'string' || typeof e.summary !== 'string' || !Number.isFinite(Date.parse(e.time)) || !safeURL(e.url, 'github.com')) throw Error('Invalid event');
  }
  return feed;
}
function el(tag, text, className) {
  const node = document.createElement(tag); if (text !== undefined) node.textContent = text; if (className) node.className = className; return node;
}
function link(text, href, className) { const a = el('a', text, className); a.href = href; return a; }
function age(value) {
  const mins = Math.max(0, Math.floor((Date.now() - Date.parse(value)) / 60000));
  return mins < 1 ? 'just now' : mins < 60 ? `${mins}m ago` : mins < 1440 ? `${Math.floor(mins / 60)}h ago` : `${Math.floor(mins / 1440)}d ago`;
}
function time(value) { const node = el('time', age(value), 'feed-time'); node.dateTime = value; node.title = new Date(value).toLocaleString(); return node; }
function taskRow(task) {
  const li = el('li'); const details = el('details', undefined, 'feed-task'); details.dataset.task = task.id;
  const summary = el('summary'); const latest = task.events[0];
  summary.append(link(({scientist:'🔭',brain:'🧠',mind:'💭',cortex:'🔬',heart:'❤️',hands:'🛠️',pulse:'⏱️',insight:'💡',dna:'🧬',memory:'📚',eyes:'👁️',ears:'👂',broca:'🗣️',nerves:'⚡',gut:'♻️'}[task.board] || '') + ' ' + task.board.replace(/^./, c => c.toUpperCase()), task.board_url, 'feed-board'), el('span', task.title, 'feed-title'), el('span', latest.summary, 'feed-stage'), time(latest.time));
  details.append(summary, el('p', `${task.repo} · ${task.state || 'unknown'}${task.source_status !== 'ok' ? ' · last known evidence' : ''}`, 'feed-meta'));
  const history = el('ol');
  for (const e of task.events) { const item = el('li', undefined, 'feed-event'); item.append(time(e.time), document.createTextNode(' '), link(e.summary, e.url)); history.append(item); }
  details.append(history);
  if (task.history_count > task.events.length) details.append(el('p', 'Showing the latest 20 recorded updates. Open the source for older history.', 'feed-meta'));
  li.append(details); return li;
}
function renderTasks() {
  const opened = new Set([...list.querySelectorAll('details[open]')].map(x => x.dataset.task));
  const rows = current.tasks.slice(0, count).map(task => { const row = taskRow(task); if (opened.has(task.id)) row.firstElementChild.open = true; return row; });
  list.replaceChildren(...rows);
  more.hidden = count >= current.tasks.length;
  empty.hidden = current.tasks.length > 0;
  empty.textContent = !current.generated || !current.coverage.length ? 'Activity collection not yet available.' : current.coverage.some(c => c.status !== 'ok') ? 'No activity available from the checked sources. See coverage below.' : 'No recorded development activity in the collected window.';
}
function renderCoverage() {
  const gaps = current.coverage.filter(c => c.status !== 'ok').length;
  const aged = current.generated && Date.now() - Date.parse(current.generated) > 15 * 60000;
  fresh.textContent = current.generated ? `Collected ${age(current.generated)}${aged ? ' · delayed' : ''}${lastChecked ? ' · checked ' + age(lastChecked) : ''}` : 'Collection not yet available';
  root.querySelector('[data-feed-coverage-label]').textContent = `Coverage and freshness · ${current.coverage.length - gaps}/${current.coverage.length} sources checked${gaps ? ' · gaps' : ''}${current.truncated ? ' · latest 200 tasks' : ''}`;
  coverage.replaceChildren(...current.coverage.map(c => el('li', `${c.repo}: ${c.status}${c.checked ? ' · checked ' + age(c.checked) : ''}${c.reason ? ' · ' + c.reason : ''}`)));
}
function reading() {
  return count > 5 || Boolean(root.querySelector('details[open]')) || root.contains(document.activeElement) || root.getBoundingClientRect().top < -30;
}
function signature(feed) { return JSON.stringify(feed.tasks); }
function apply(feed) { current = feed; pending = null; incoming.hidden = true; renderTasks(); renderCoverage(); }
function receive(feed) {
  if ((pending?.generated || current.generated) && feed.generated && Date.parse(feed.generated) < Date.parse(pending?.generated || current.generated)) throw Error('Older feed');
  if (signature(feed) !== signature(current)) {
    if (reading()) {
      pending = feed;
      const prior = new Map(current.tasks.map(t => [t.id, JSON.stringify(t)]));
      const changed = feed.tasks.filter(t => prior.get(t.id) !== JSON.stringify(t)).length;
      incoming.textContent = changed ? `${changed} updated task${changed === 1 ? '' : 's'} · Show updates` : 'Feed changed · Show updates';
      incoming.hidden = false;
    } else apply(feed);
  } else { current = {...feed, tasks: current.tasks}; pending = null; incoming.hidden = true; renderCoverage(); }
}
more.addEventListener('click', () => {
  // Append; existing details and their focus remain untouched.
  const start = count; count += 5;
  for (const task of current.tasks.slice(start, count)) list.append(taskRow(task));
  more.hidden = count >= current.tasks.length;
  if (more.hidden) list.lastElementChild?.querySelector('summary')?.focus();
});
incoming.addEventListener('click', () => {
  if (!pending) return;
  const top = root.getBoundingClientRect().top;
  apply(pending);
  const first = list.querySelector('summary'); if (first) first.focus({preventScroll:true});
  window.scrollBy(0, root.getBoundingClientRect().top - top);
});
async function refresh() {
  if (refreshing || document.visibilityState === 'hidden') return;
  refreshing = true;
  const controller = new AbortController(); const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(new URL('activity.json', location.href), {cache:'no-store', signal:controller.signal});
    if (!response.ok) throw Error('Activity unavailable');
    const feed = validate(await response.json()); lastChecked = new Date().toISOString(); receive(feed); notice.textContent = '';
  } catch (_) { notice.textContent = 'Live updates unavailable. Showing the last loaded evidence.'; }
  finally { clearTimeout(timeout); refreshing = false; }
}
try { current = validate(JSON.parse(document.getElementById('live-feed-snapshot').textContent)); apply(current); }
catch (_) { notice.textContent = 'Activity snapshot unavailable.'; return; }
refresh(); setInterval(refresh, 60000);
document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') refresh(); });
})();
