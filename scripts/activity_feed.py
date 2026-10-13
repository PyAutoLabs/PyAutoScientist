"""Bounded public development-event index. Owner records remain authoritative.

Only normalized public fields are persisted: never API bodies, comments or tokens.
A source's cursor advances only after complete pagination. Unavailable/private
sources are removed from the publication, not silently retained as current.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import html
import json
import os
from pathlib import Path
import re
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SCHEMA = 1
MAX_EVENTS = 1500
MAX_TASKS = 200
MAX_PAGES = 3
RETENTION_DAYS = 30
BOARDS = {x.lower(): x for x in ('Scientist', 'Brain', 'Mind', 'Cortex', 'Memory', 'Eyes', 'Ears', 'Heart', 'Hands', 'Pulse', 'Insight', 'DNA', 'Nerves', 'Broca', 'Gut')}


def instant(value):
    if not isinstance(value, str):
        raise ValueError('missing timestamp')
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise ValueError('timestamp must include timezone')
    return dt.astimezone(timezone.utc)


def stamp(dt):
    return dt.astimezone(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def short(text, limit=110):
    return re.sub(r'\s+', ' ', str(text or '')).strip()[:limit]


def sources(path, routes=None):
    import yaml
    rows = yaml.safe_load(Path(path).read_text())['repos']
    result = {}
    for name, row in rows.items():
        repo = row.get('github', '')
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo):
            continue
        organ = str(row.get('organ', 'scientist' if name == 'PyAutoScientist' else 'mind')).lower()
        board = (routes or {}).get(name, organ if organ in BOARDS else 'mind')
        if board not in BOARDS:
            raise ValueError('unknown activity board')
        result[repo] = {'board': board, 'board_url': f'https://{repo.split("/")[0].lower()}.github.io/PyAuto{BOARDS[board]}/'}
    return dict(sorted(result.items()))


class CollectionError(Exception):
    """Public-safe source failure; never includes response content."""


class GitHub:
    def __init__(self, token=None, budget=60):
        self.token = token
        self.budget = budget
        self.requests = 0
        self.deadline = time.monotonic() + 120
        self.expired = False

    def get(self, path):
        if time.monotonic() >= self.deadline:
            self.expired = True
            raise CollectionError('collection time budget reached')
        if self.requests >= self.budget:
            raise CollectionError('request budget reached')
        self.requests += 1
        headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'PyAutoScientist-live-feed', 'X-GitHub-Api-Version': '2022-11-28'}
        if self.token:
            headers['Authorization'] = 'Bearer ' + self.token
        # Construct endpoints locally; never follow an API-supplied URL with a token.
        if not path.startswith(('/repos/', '/users/', '/orgs/')) or '://' in path:
            raise CollectionError('invalid API path')
        try:
            with urlopen(Request('https://api.github.com' + path, headers=headers), timeout=15) as response:
                return json.load(response)
        except HTTPError as exc:
            raise CollectionError(f'GitHub HTTP {exc.code}') from None
        except (OSError, ValueError):
            raise CollectionError('GitHub unavailable') from None

    def pages(self, path, params):
        rows = []
        for page in range(1, MAX_PAGES + 1):
            data = self.get(path + '?' + urlencode(dict(params, per_page=100, page=page)))
            if not isinstance(data, list):
                raise CollectionError('invalid response')
            rows.extend(data)
            if len(data) < 100:
                return rows
        error = CollectionError('pagination limit reached')
        error.rows = rows
        raise error


class RepositoryBudget:
    """A busy repo yields to peers; normalized partial batches resume next cycle."""
    def __init__(self, parent, limit=12):
        self.parent, self.start, self.limit = parent, parent.requests, limit

    def get(self, path):
        if self.parent.requests - self.start >= self.limit:
            raise CollectionError('repository allowance reached')
        return self.parent.get(path)

    def pages(self, path, params):
        return GitHub.pages(self, path, params)


def closing_issue(body):
    """Only one explicit, same-repository closing directive; no fuzzy pairing."""
    body = re.sub(r'```.*?```', '', body or '', flags=re.S)
    refs = set(re.findall(r'^\s*(?:Closes|Fixes|Resolves)\s+#(\d+)\s*\.?\s*$', body, re.M | re.I))
    return int(next(iter(refs))) if len(refs) == 1 else None


def event(repo, number, suffix, when, kind, summary, title, url, now):
    dt = instant(when)
    if dt > now + timedelta(minutes=5):
        raise ValueError('future timestamp')
    expected = f'https://github.com/{repo}/'
    if not isinstance(url, str) or not url.startswith(expected):
        raise ValueError('invalid source URL')
    return {'id': f'{repo}#{number}:{suffix}', 'task': f'{repo}#{number}',
            'repo': repo, 'time': stamp(dt), 'kind': kind, 'summary': short(summary),
            'title': short(title), 'url': url}


def collect_repo(api, repo, since, now, prior):
    """Transactional per-source batch: a failed page leaves cursor unchanged."""
    partial = []
    def page_set(path, params):
        try:
            return api.pages(path, params)
        except CollectionError as exc:
            if hasattr(exc, 'rows'):
                partial.append(str(exc))
                return exc.rows
            raise
    issues = page_set(f'/repos/{repo}/issues', {'state': 'all', 'sort': 'updated', 'direction': 'asc', 'since': since})
    comments = page_set(f'/repos/{repo}/issues/comments', {'sort': 'updated', 'direction': 'asc', 'since': since})
    tasks = dict(prior.get('tasks', {}))
    events = dict(prior.get('events', {}))
    for item in issues:
        n = int(item['number'])
        is_pr = 'pull_request' in item
        # Resuming a bounded initial scan must not spend the entire next budget
        # re-fetching PR details already normalized from this exact revision.
        if tasks.get(str(n), {}).get('revision') == item.get('updated_at') and item.get('updated_at'):
            continue
        try:
            detail = api.get(f'/repos/{repo}/pulls/{n}') if is_pr else item
        except CollectionError as exc:
            partial.append(str(exc))
            break
        link = closing_issue(detail.get('body')) if is_pr else None
        tasks[str(n)] = {'title': short(item['title']), 'is_pr': is_pr, 'issue': link, 'state': item['state'], 'revision': item.get('updated_at')}
        url = f'https://github.com/{repo}/{"pull" if is_pr else "issues"}/{n}'
        e = event(repo, n, 'opened', item['created_at'], 'opened', 'Draft PR opened' if detail.get('draft') else 'PR opened' if is_pr else 'Task opened', item['title'], url, now)
        events[e['id']] = e
        if detail.get('merged_at'):
            e = event(repo, n, 'merged', detail['merged_at'], 'merged', 'PR merged', item['title'], url, now)
            events[e['id']] = e
            # A previously observed closed state is replaced by precise merge evidence.
            events.pop(f'{repo}#{n}:closed', None)
        elif item.get('closed_at'):
            e = event(repo, n, 'closed', item['closed_at'], 'closed', 'PR closed without merge' if is_pr else 'Task closed', item['title'], url, now)
            events[e['id']] = e
        elif item.get('state') == 'open':
            # We cannot timestamp a reopening from updated_at; keep historical events.
            pass
    for comment in comments:
        if comment.get('user', {}).get('type') == 'Bot':
            continue
        match = re.fullmatch(r'https://api.github.com/repos/' + re.escape(repo) + r'/issues/(\d+)', comment.get('issue_url', ''))
        if not match:
            continue
        n = match[1]
        if n not in tasks:
            partial.append('comment task metadata not yet collected')
            continue
        body = comment.get('body') or ''
        heading = re.search(r'^#{1,3}\s+(Progress(?: update)?|In progress|Blocked|Shipped|Workspace PR Created|Library PR Created)\b', body, re.M | re.I)
        stage = heading.group(1).lower() if heading else ''
        kind, summary = {'blocked': ('blocked', 'Blocker reported'), 'in progress': ('active', 'Work started'),
                         'shipped': ('reported', 'Shipment reported — see source'),
                         'workspace pr created': ('progress', 'Workspace PR recorded'),
                         'library pr created': ('progress', 'Library PR recorded')}.get(stage, ('progress', 'Progress update recorded' if heading else 'Discussion update recorded'))
        # Comment edits replace this event in-place at its original posted time.
        # No comment text is ever exported or interpreted as scientific acceptance.
        e = event(repo, int(n), 'comment-' + str(int(comment['id'])), comment['created_at'], kind, summary,
                  tasks[n]['title'], comment['html_url'], now)
        events[e['id']] = e
    cutoff = now - timedelta(days=RETENTION_DAYS)
    recent = sorted((e for e in events.values() if instant(e['time']) >= cutoff), key=lambda e: (e['time'], {'merged': 5, 'closed': 4, 'blocked': 3, 'progress': 2}.get(e['kind'], 1), e['id']), reverse=True)
    truncated = len(recent) > MAX_EVENTS
    recent = recent[:MAX_EVENTS]
    keep = {e['task'].rsplit('#', 1)[1] for e in recent}
    keep.update(str(tasks[n]['issue']) for n in list(keep) if tasks.get(n, {}).get('issue'))
    tasks = {n: t for n, t in tasks.items() if n in keep}
    if truncated:
        partial.append('event retention cap reached')
    result = {'events': {e['id']: e for e in recent}, 'tasks': tasks,
              'checked': stamp(now), 'status': 'partial' if partial else 'ok',
              'reason': '; '.join(dict.fromkeys(partial)) or None}
    if not partial:
        result['cursor'] = stamp(now)
    elif prior.get('cursor'):
        result['cursor'] = prior['cursor']
    return result


def collect(registry, previous, api, now=None, pulse_config=None, identities=None):
    now = now or datetime.now(timezone.utc)
    previous = previous if previous.get('schema_version') == SCHEMA else {}
    cache = {'schema_version': SCHEMA, 'sources': {}, 'next': 0}
    names = list(registry)
    offset = int(previous.get('next', 0)) % max(1, len(names))
    ordered = names[offset:] + names[:offset]
    # Public catalogs avoid one visibility request per repository on every tick.
    # A missing/failed owner catalog removes its entries from the exported cache.
    catalogs = {}
    for owner in sorted({repo.split('/')[0] for repo in names}):
        try:
            identity = api.get('/users/' + owner)
            route = '/orgs/' if identity.get('type') == 'Organization' else '/users/'
            entries = api.pages(route + owner + '/repos', {'type': 'public' if route == '/orgs/' else 'owner', 'sort': 'full_name'})
            catalogs[owner] = {item['full_name'].lower() for item in entries
                               if item.get('private') is False and item.get('visibility', 'public') == 'public'}
        except (CollectionError, ValueError, KeyError, TypeError):
            catalogs[owner] = set()
    public = set()
    for repo in ordered:
        old = previous.get('sources', {}).get(repo, {})
        if repo.lower() in catalogs[repo.split('/')[0]]:
            public.add(repo)
            cache['sources'][repo] = dict(old, status='stale', reason='awaiting collection')
        else:
            cache['sources'][repo] = {'status': 'unavailable', 'reason': 'public source unavailable', 'events': {}, 'tasks': {}}
    if pulse_config:
        from pulse_activity import collect_pulse
        cache['pulse'] = collect_pulse(RepositoryBudget(api), (identities or {}).get(pulse_config['repository'], ''),
                                      pulse_config.get('ref', 'main'), public, identities or {},
                                      previous.get('pulse', {}), now)
    advanced = 0
    for repo in ordered:
        if repo not in public:
            advanced += 1
            continue
        old = cache['sources'][repo]
        since = stamp(max(now - timedelta(days=RETENTION_DAYS), instant(old['cursor']) - timedelta(minutes=2))) if old.get('cursor') else stamp(now - timedelta(days=7))
        try:
            cache['sources'][repo] = collect_repo(RepositoryBudget(api) if isinstance(api, GitHub) else api, repo, since, now, old)
            advanced += 1
        except (CollectionError, ValueError, KeyError, TypeError) as exc:
            old['status'] = 'stale'
            old['reason'] = str(exc) if isinstance(exc, CollectionError) else 'invalid source data'
            if api.requests >= api.budget or getattr(api, 'expired', False):
                break
            advanced += 1
    cache['next'] = (offset + max(1, advanced)) % max(1, len(names))
    feed = make_feed(registry, cache, now)
    return cache, feed


def make_feed(registry, cache, now):
    grouped = {}
    coverage = []
    cutoff = now - timedelta(days=RETENTION_DAYS)
    for repo, source in cache['sources'].items():
        coverage.append({'repo': repo, 'status': source['status'], 'checked': source.get('checked'), 'reason': source.get('reason')})
        tasks = source.get('tasks', {})
        for e in source.get('events', {}).values():
            if instant(e['time']) < cutoff:
                continue
            n = e['task'].rsplit('#', 1)[1]
            task = tasks.get(n, {})
            target = str(task.get('issue'))
            # Only group when the explicit target is present and is actually an issue.
            if target in tasks and not tasks[target]['is_pr']:
                n, task = target, tasks[target]
            key = f'{repo}#{n}'
            row = grouped.setdefault(key, {'id': key, 'repo': repo, **registry[repo], 'title': task.get('title', e['title']),
                                          'state': task.get('state', 'unknown'), 'source_status': source['status'], 'events': []})
            row['events'].append(e)
    for row in grouped.values():
        row['events'].sort(key=lambda e: (e['time'], {'merged': 5, 'closed': 4, 'blocked': 3, 'progress': 2}.get(e['kind'], 1), e['id']), reverse=True)
        row['history_count'] = len(row['events'])
        row['events'] = row['events'][:20]
        row['time'] = row['events'][0]['time']
    if 'pulse' in cache:
        from pulse_activity import publish
        coverage.append({'repo': 'Pulse campaign evidence', **{k: cache['pulse'].get(k) for k in ('status', 'checked', 'reason')}})
        for row in publish(cache['pulse'], now):
            grouped[row['id']] = row
    rows = sorted(grouped.values(), key=lambda row: (row['time'], row['id']), reverse=True)
    return {'schema_version': SCHEMA, 'generated': stamp(now), 'scope': 'Development and Pulse campaign activity',
            'retention_days': RETENTION_DAYS, 'initial_backfill_days': 7, 'truncated': len(rows) > MAX_TASKS,
            'coverage': coverage, 'tasks': rows[:MAX_TASKS]}


CSS = '''
.live-feed{margin:1rem 0 2rem;border:1px solid var(--line);border-radius:12px;padding:1rem}
.feed-toolbar{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:.5rem}
.feed-toolbar p,.feed-meta{color:var(--muted);font-size:.85rem;margin:.25rem 0}
.feed-list{list-style:none;padding:0;margin:.8rem 0}
.feed-list>li{margin:0}
.feed-task{margin:0;border-top:1px solid var(--line);padding:.35rem 0;min-width:0}
.feed-task summary{padding:.25rem 0;cursor:pointer;display:flex;align-items:baseline;gap:.6rem;flex-wrap:wrap;list-style:none}
.feed-task summary::before{content:'▸';color:var(--muted)}
.feed-task[open] summary::before{content:'▾'}
.feed-title{flex:1 1 18rem;min-width:0;overflow-wrap:anywhere;font-weight:600}
.feed-time,.feed-stage{font-size:.85rem;color:var(--muted)}
.feed-board{font-size:.85rem;font-weight:600;text-decoration:none}
.feed-event{margin:.45rem 0;overflow-wrap:anywhere;font-size:.9rem}
.feed-event time{color:var(--muted);margin-right:.5rem}
.feed-task ol{padding-left:1.5rem}
.live-feed button{min-height:40px;padding:.4rem .8rem;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg);cursor:pointer}
.live-feed :focus-visible{outline:3px solid var(--accent);outline-offset:3px}
.feed-coverage{margin-top:.75rem;font-size:.85rem;color:var(--muted)}
.feed-coverage ul{max-height:14rem;overflow:auto;overflow-wrap:anywhere}
@media(max-width:40rem){.feed-title{flex-basis:100%}.feed-task summary{gap:.35rem}.live-feed{padding:.75rem}}
'''


def render_html(feed=None):
    feed = feed or {'schema_version': SCHEMA, 'tasks': [], 'coverage': [], 'generated': None}
    esc = html.escape
    rows = []
    for row in feed['tasks'][:5]:
        e = row['events'][0]
        rows.append(f'<li><details class="feed-task"><summary><span class="feed-title">{esc(row["title"])}</span><span class="feed-stage">{esc(e["summary"])}</span><time>{esc(e["time"])}</time></summary><a href="{esc(row["board_url"], quote=True)}">{esc(BOARDS[row["board"]])}</a> · <a href="{esc(e["url"], quote=True)}">Source</a></details></li>')
    data = json.dumps(feed, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    return f'''<h2 id="live-feed-heading">Live Feed</h2>
<section class="live-feed" aria-labelledby="live-feed-heading" id="live-feed">
<div class="feed-toolbar"><div><p>Development and Pulse campaign activity</p><p data-feed-freshness>Collection {esc(feed.get('generated') or 'not yet available')}</p></div><button type="button" data-feed-new hidden>New updates</button></div>
<p data-feed-notice role="status"></p><ul class="feed-list" data-feed-list>{''.join(rows)}</ul>
<p data-feed-empty {'hidden' if rows else ''}>No recorded activity available yet.</p>
<button type="button" data-feed-more hidden>Show more</button>
<details class="feed-coverage"><summary data-feed-coverage-label>Coverage and freshness</summary><p>Public development and Pulse campaign check-ins; only explicitly associated, dated run evidence enters the timeline. Unrecorded local work is not included. Up to 30 days retained; initial collection looks back seven days. Collection runs approximately every five minutes; repositories share a bounded request budget.</p><ul data-feed-coverage></ul></details>
<noscript><p>Publication snapshot; enable JavaScript for updates and more history.</p></noscript>
<script type="application/json" id="live-feed-snapshot">{data}</script></section>'''


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repos', required=True, type=Path)
    ap.add_argument('--cache', required=True, type=Path)
    ap.add_argument('--output', required=True, type=Path)
    ap.add_argument('--budget', type=int, default=60)
    ap.add_argument('--config', type=Path, default=Path(__file__).resolve().parents[1] / 'config' / 'activity_sources.json')
    args = ap.parse_args()
    # 180 calls / 5min fits a 5000/hour PAT. Default GITHUB_TOKEN uses 60/cycle.
    previous = json.loads(args.cache.read_text()) if args.cache.exists() else {}
    import yaml
    config = json.loads(args.config.read_text())
    if config.get('schema_version') != 1:
        raise ValueError('unsupported activity source config')
    identities = {name: row.get('github') for name, row in yaml.safe_load(args.repos.read_text())['repos'].items()}
    cache, feed = collect(sources(args.repos, config.get('board_routes')), previous,
                          GitHub(os.environ.get('GH_TOKEN'), args.budget),
                          pulse_config=config.get('pulse'), identities=identities)
    for path, value in ((args.cache, cache), (args.output, feed)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'tasks': len(feed['tasks']), 'sources': len(feed['coverage']), 'current': sum(c['status'] == 'ok' for c in feed['coverage'])}))


if __name__ == '__main__':
    import sys
    sys.modules['activity_feed'] = sys.modules[__name__]
    main()
