import base64
import copy
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import activity_feed as af
import pulse_activity as pa
from test_activity_feed import NOW

REPO = 'Example/PyAutoPulse'
PROJECT = 'Example/autolens_profiling'
PUBLIC = {REPO, PROJECT}
IDS = {'autolens_profiling': PROJECT}
SHA = 'a' * 40
LEDGER = {'version': 1, 'last_checkin': '2026-10-13T17:51:40Z',
          'campaigns': [{'id': 'imaging', 'title': 'Imaging', 'status': 'active', 'next': 'Review inputs', 'updated': '2026-10-13'}], 'tasks': []}


class API:
    def __init__(self, ledger=None, records=None):
        self.ledger = copy.deepcopy(ledger or LEDGER)
        self.records = records or []

    def get(self, path):
        if '/commits/' in path:
            return {'sha': SHA}
        assert path.endswith('?ref=' + SHA)
        if '/campaigns.yaml?' in path:
            data = self.ledger
        elif '/registry.yaml?' in path:
            data = {'schema': 1, 'instances': [{'repo': 'autolens_profiling', 'instance': 'lens'}]}
        else:
            data = {'github': PROJECT, 'commit': SHA, 'summary': {'records': self.records}}
        return {'type': 'file', 'encoding': 'base64', 'content': base64.b64encode(json.dumps(data).encode()).decode()}


def collect(api, previous=None, public=PUBLIC):
    return pa.collect_pulse(api, REPO, 'main', public, IDS, previous or {}, NOW)


def test_unchanged_checkin_does_not_create_new_event():
    first = collect(API())
    api = API(); api.ledger['last_checkin'] = '2026-10-13T18:51:40Z'; api.ledger['campaigns'][0]['updated'] = '2026-10-14'
    second = collect(api, first)
    assert second['rows'][0]['events'] == first['rows'][0]['events']
    assert second['rows'][0]['state'] == 'active'
    assert 'running' not in second['rows'][0]['events'][0]['summary']


def test_meaningful_changes_and_task_progress_group_under_campaign():
    first = collect(API())
    api = API(); api.ledger['last_checkin'] = '2026-10-13T18:51:40Z';api.ledger['tasks'] = [{'id': 'new-task', 'campaign': 'imaging', 'status': 'blocked', 'next': 'Need data'}]
    second = collect(api, first)
    assert len(second['rows']) == 1
    assert len(second['rows'][0]['events']) == 2
    assert 'Task update: new-task' in second['rows'][0]['events'][0]['summary']
    assert len(pa.publish(second, NOW)) == 1


def test_undated_measurements_are_coverage_gaps_not_activity():
    source = collect(API(records=[{'run_id': 'r1', 'campaign_id': 'imaging', 'provenance': {'measured_at': None}}]))
    assert source['status'] == 'partial'
    assert source['undated_records'] == 1
    assert all(e['kind'] == 'checkin' for e in source['rows'][0]['events'])


def test_dated_measurements_group_by_explicit_owner_association():
    ledger = copy.deepcopy(LEDGER);ledger['campaigns'][0]['runs'] = [{'repo': 'autolens_profiling', 'run_id': 'r1'}]
    records = [{'run_id': 'r1', 'provenance': {'measured_at': '2026-10-13T18:00:00Z'}}] * 3
    first = collect(API(ledger, records));second = collect(API(ledger, records), first)
    events = [e for e in second['rows'][0]['events'] if e['kind'] == 'measurement']
    assert len(events) == 1
    assert '3 records' in events[0]['summary']
    assert 'acceptance not inferred' in events[0]['summary']
    assert events[0]['time'] == '2026-10-13T18:00:00Z'


def test_unassigned_dated_record_is_not_guessed_into_campaign():
    source = collect(API(records=[{'run_id': 'r1', 'setup_id': 'imaging/hst', 'provenance': {'measured_at': '2026-10-13T18:00:00Z'}}]))
    assert source['unassigned_records'] == 1
    assert len(source['rows'][0]['events']) == 1


def test_invalid_or_failed_source_keeps_old_evidence_but_private_drops_it():
    first = collect(API());api = API();api.ledger['last_checkin'] = 'tomorrow'
    failed = collect(api, first)
    assert failed['status'] == 'stale'
    assert failed['rows'] == first['rows']
    assert not collect(API(), first, public=set())['rows']


def test_per_repository_allowance_leaves_budget_for_other_sources():
    parent = af.GitHub(budget=60)
    parent.get = lambda path: setattr(parent, 'requests', parent.requests + 1) or {}
    bounded = af.RepositoryBudget(parent, limit=3)
    for _ in range(3): bounded.get('/repos/Example/A')
    try:
        bounded.get('/repos/Example/A')
        assert False, 'allowance should stop'
    except af.CollectionError as exc:
        assert 'repository allowance' in str(exc)
    peer = af.RepositoryBudget(parent)
    peer.get('/repos/Example/B')
    assert parent.requests == 4


def test_explicit_profiling_routes(tmp_path):
    p = tmp_path / 'repos.yaml';p.write_text('repos:\n  autofit_profiling:\n    github: Example/autofit_profiling\n')
    assert af.sources(p, {'autofit_profiling': 'pulse'})['Example/autofit_profiling']['board'] == 'pulse'


def test_large_snapshot_uses_pinned_blob_not_download_url():
    class Large(API):
        def get(self, path):
            if '/contents/snapshots/' in path:
                return {'type': 'file', 'encoding': 'none', 'size': 4000000, 'sha': 'b' * 40}
            if '/git/blobs/' in path:
                assert path.endswith('b' * 40)
                return super().get(f'/repos/{REPO}/contents/snapshots/lens.json?ref={SHA}')
            return super().get(path)
    assert collect(Large())['status'] == 'ok'


def test_expired_campaign_history_is_not_published_on_source_failure():
    first = collect(API())
    first['rows'][0]['events'][0]['time'] = '2020-01-01T00:00:00Z'
    assert pa.publish(dict(first, status='stale'), NOW) == []
