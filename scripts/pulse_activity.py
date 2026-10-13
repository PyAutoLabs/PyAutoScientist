"""Read Pulse-owned, public campaign evidence without executing or judging it."""
from __future__ import annotations
import base64
from datetime import timedelta
import hashlib
import json
import re
from urllib.parse import quote
import yaml

from activity_feed import CollectionError, instant, short, stamp

STATES = {'active', 'ready', 'running', 'blocked', 'parked', 'needs-decision', 'needs-slicing', 'complete', 'superseded'}


def file_at(api, repo, path, revision):
    if not re.fullmatch(r'[A-Za-z0-9_./-]+', path) or '..' in path.split('/'):
        raise CollectionError('invalid Pulse source path')
    data = api.get(f'/repos/{repo}/contents/{path}?ref={quote(revision, safe="")}')
    if data.get('type') != 'file' or data.get('size', 0) > 8000000:
        raise CollectionError('unsupported Pulse source file')
    if data.get('encoding') == 'none' and re.fullmatch(r'[0-9a-f]{40}', data.get('sha', '')):
        # GitHub's contents API omits inline content above 1MB. Fetch the exact
        # blob named at the pinned revision, never a moving download URL.
        data = api.get(f'/repos/{repo}/git/blobs/{data["sha"]}')
    if data.get('encoding') != 'base64' or data.get('size', 0) > 8000000:
        raise CollectionError('unsupported Pulse blob')
    return base64.b64decode(data['content']).decode('utf-8')


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()[:24]


def collect_pulse(api, repo, ref, public, identities, previous, now):
    """Return a normalized campaign cache. Missing time/association is a gap."""
    if repo not in public:
        return {'status': 'unavailable', 'reason': 'Pulse is not a verified public source', 'rows': []}
    try:
        revision = api.get(f'/repos/{repo}/commits/{quote(ref, safe="")}')['sha']
        if not re.fullmatch(r'[0-9a-f]{40}', revision):
            raise ValueError('invalid revision')
        ledger = yaml.safe_load(file_at(api, repo, 'campaigns.yaml', revision))
        registry = yaml.safe_load(file_at(api, repo, 'registry.yaml', revision))
        if ledger.get('version') != 1 or registry.get('schema') != 1:
            raise ValueError('unsupported source version')
        reviewed = instant(ledger['last_checkin'])
        if reviewed > now + timedelta(minutes=5):
            raise ValueError('future check-in')
        campaigns = ledger['campaigns']
        tasks = ledger['tasks']
        if not isinstance(campaigns, list) or not isinstance(tasks, list) or len(campaigns) > 100:
            raise ValueError('invalid campaign list')
        old = {r['id']: r for r in previous.get('rows', [])}
        rows, ids = [], set()
        for campaign in campaigns:
            cid = campaign['id']
            if not isinstance(cid, str) or not re.fullmatch(r'[a-z0-9_-]+', cid) or cid in ids or campaign['status'] not in STATES:
                raise ValueError('invalid campaign identity/status')
            ids.add(cid)
            # Reviewed dates, render times and overall check-in stamps are not a
            # meaningful change to a campaign. Track facts and recorded direction.
            facts = {k: campaign.get(k) for k in ('title', 'status', 'next', 'evidence')}
            facts['tasks'] = sorted(({k: t.get(k) for k in ('id', 'title', 'status', 'next', 'evidence')}
                                     for t in tasks if t.get('campaign') == cid), key=lambda t: str(t['id']))
            task_marks = {str(t['id']): fingerprint(t) for t in facts['tasks']}
            digest = fingerprint(facts)
            key = f'pulse:campaign:{cid}'
            prior = old.get(key, {})
            events = list(prior.get('events', []))
            # Do not fabricate a newer event from an out-of-date snapshot.
            if prior.get('reviewed') and reviewed < instant(prior['reviewed']):
                raise ValueError('older campaign evidence')
            if digest != prior.get('fingerprint'):
                changed_tasks = [t for t in facts['tasks'] if prior.get('task_marks', {}).get(str(t['id'])) != task_marks[str(t['id'])]]
                summary = 'Check-in: ' + campaign['status'].replace('-', ' ') + ' · ' + str(campaign.get('next', ''))
                if prior and changed_tasks:
                    task = changed_tasks[0]
                    summary = 'Task update: ' + str(task.get('title') or task['id']) + ' · ' + str(task.get('status'))
                    if len(changed_tasks) > 1:
                        summary += f' (+{len(changed_tasks) - 1} more)'
                # Include check-in time in ID: a genuine later return to an old
                # state is a new transition; an unchanged check-in is not.
                events.append({'id': key + ':' + fingerprint([digest, stamp(reviewed)]),
                               'time': stamp(reviewed), 'kind': 'checkin',
                               'summary': short(summary),
                               'url': f'https://github.com/{repo}/blob/{revision}/campaigns.yaml'})
            rows.append({'id': key, 'repo': repo, 'board': 'pulse',
                         'board_url': f'https://{repo.split("/")[0].lower()}.github.io/PyAutoPulse/',
                         'title': short(campaign['title']), 'state': campaign['status'],
                         'fingerprint': digest, 'task_marks': task_marks, 'reviewed': stamp(reviewed), 'events': events})
        by_campaign = {r['id'].rsplit(':', 1)[1]: r for r in rows}
        # Pulse may explicitly associate a project run with a campaign without
        # requiring changes to a producer's versioned summary schema.
        associations = {}
        for campaign in campaigns:
            for run in campaign.get('runs', []):
                project = identities.get(run['repo'])
                key = (project, run['run_id'])
                if key in associations and associations[key] != campaign['id']:
                    raise ValueError('ambiguous run association')
                associations[key] = campaign['id']
        undated = unassigned = dated = 0
        gaps = []
        for instance in registry.get('instances', []):
            project = identities.get(instance['repo'])
            if not project or project not in public:
                gaps.append('project source unavailable')
                continue
            snapshot = json.loads(file_at(api, repo, f'snapshots/{instance["instance"]}.json', revision))
            if snapshot.get('github') != project or not re.fullmatch(r'[0-9a-f]{40}', snapshot.get('commit', '')):
                raise ValueError('snapshot identity mismatch')
            summary = snapshot['summary']
            runs = {}
            for record in summary.get('records', []):
                measured = record.get('provenance', {}).get('measured_at')
                if not measured:
                    undated += 1
                    continue
                measured_time = instant(measured)
                if measured_time > now + timedelta(minutes=5):
                    raise ValueError('future measurement')
                cid = associations.get((project, record.get('run_id')), record.get('campaign_id'))
                if cid not in by_campaign or not record.get('run_id'):
                    unassigned += 1
                    continue
                # Association must be producer-declared; never infer from timing,
                # filenames, setup resemblance or a project-wide render timestamp.
                key = (cid, record['run_id'])
                run = runs.setdefault(key, {'time': measured_time, 'count': 0})
                run['time'] = max(run['time'], measured_time)
                run['count'] += 1
                dated += 1
            for (cid, run_id), run in runs.items():
                row = by_campaign[cid]
                eid = 'pulse:run:' + fingerprint([project, cid, run_id])
                e = {'id': eid, 'time': stamp(run['time']), 'kind': 'measurement',
                     'summary': f'Measurements recorded · {run["count"]} records · acceptance not inferred',
                     'url': f'https://github.com/{repo}/blob/{revision}/snapshots/{instance["instance"]}.json'}
                row['events'] = [x for x in row['events'] if x['id'] != eid] + [e]
        cutoff = now - timedelta(days=30)
        for row in rows:
            row['events'] = sorted((e for e in row['events'] if instant(e['time']) >= cutoff), key=lambda e: (e['time'], e['id']), reverse=True)[:100]
        if undated:
            gaps.append(f'{undated} measurement records lack event times')
        if unassigned:
            gaps.append(f'{unassigned} dated records lack explicit campaign/run association')
        return {'status': 'partial' if gaps else 'ok', 'reason': '; '.join(gaps) or None,
                'checked': stamp(now), 'revision': revision, 'rows': rows,
                'dated_records': dated, 'undated_records': undated, 'unassigned_records': unassigned}
    except (CollectionError, ValueError, KeyError, TypeError, yaml.YAMLError):
        return dict(previous, status='stale', reason='Pulse evidence unavailable or invalid')


def publish(cache, now):
    rows = []
    for row in cache.get('rows', []):
        events = [e for e in row['events'] if instant(e['time']) >= now - timedelta(days=30)][:20]
        if not events:
            continue
        rows.append({k: row[k] for k in ('id', 'repo', 'board', 'board_url', 'title', 'state')} |
                    {'events': events, 'time': events[0]['time'], 'history_count': len(row['events']), 'source_status': cache['status']})
    return rows
