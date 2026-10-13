"""Offline evidence/coverage tests; no GitHub or scientific execution."""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import activity_feed as af

NOW = datetime(2026, 10, 13, 20, tzinfo=timezone.utc)
REPO = 'Example/PyAutoScientist'
REGISTRY = {REPO: {'board': 'scientist', 'board_url': 'https://example.github.io/PyAutoScientist/'}}
TIME = '2026-10-13T19:00:00Z'


def issue(n=1, **changes):
    return dict(number=n, title='A small task', created_at=TIME, updated_at=TIME,
                state='open', closed_at=None, body='', **changes)


def comment(body='## Progress\nPrivate-looking long transcript must never be copied', **changes):
    d = dict(id=9, body=body, created_at='2026-10-13T19:05:00Z', updated_at='2026-10-13T19:05:00Z',
             issue_url=f'https://api.github.com/repos/{REPO}/issues/1', html_url=f'https://github.com/{REPO}/issues/1#issuecomment-9', user={'type': 'User'})
    d.update(changes)
    return d


class Fake:
    def __init__(self, issues=None, comments=None, pulls=None, private=False, fail=False, budget=100):
        self.issues, self.comments, self.pulls = issues or [], comments or [], pulls or {}
        self.private, self.fail = private, fail
        self.requests, self.budget = 0, budget

    def get(self, path):
        self.requests += 1
        if '/users/' in path:
            return {'type': 'Organization'}
        if '/pulls/' in path:
            return self.pulls[int(path.rsplit('/', 1)[1])]
        raise AssertionError(path)

    def pages(self, path, params):
        self.requests += 1
        if path == '/orgs/Example/repos':
            return [{'full_name': REPO, 'private': self.private}]
        if self.fail:
            raise af.CollectionError('GitHub unavailable')
        return copy.deepcopy(self.comments if path.endswith('/comments') else self.issues)


def test_task_pr_grouped_but_not_fuzzy_title_match():
    pr = issue(2, pull_request={})
    pr3 = issue(3, pull_request={})
    api = Fake([issue(), pr, pr3], pulls={2: {'body': 'Closes #1', 'merged_at': '2026-10-13T19:20:00Z'}, 3: {'body': 'Similar task #1'}})
    _, feed = af.collect(REGISTRY, {}, api, NOW)
    assert len(feed['tasks']) == 2
    task = next(t for t in feed['tasks'] if t['id'].endswith('#1'))
    assert task['events'][0]['summary'] == 'PR merged'
    assert len(task['events']) == 3


def test_comment_edits_not_new_events_and_no_raw_text_export():
    cache, _ = af.collect(REGISTRY, {}, Fake([issue()], [comment()]), NOW)
    cache, feed = af.collect(REGISTRY, cache, Fake([issue()], [comment(body='## Blocked\nsecretish text', updated_at=TIME)]), NOW)
    events = feed['tasks'][0]['events']
    assert len(events) == 2
    assert events[0]['summary'] == 'Blocker reported'
    assert events[0]['time'] == '2026-10-13T19:05:00Z'
    assert 'secretish' not in json.dumps(cache)
    assert 'transcript' not in json.dumps(cache)


def test_refresh_is_not_an_event_and_no_fake_completion():
    cache, feed = af.collect(REGISTRY, {}, Fake([issue()]), NOW)
    _, newer = af.collect(REGISTRY, cache, Fake(), NOW)
    assert newer['tasks'][0]['events'] == feed['tasks'][0]['events']
    assert newer['tasks'][0]['events'][0]['summary'] == 'Task opened'


def test_failed_source_retains_last_known_without_advancing_cursor():
    cache, _ = af.collect(REGISTRY, {}, Fake([issue()]), NOW)
    old_cursor = cache['sources'][REPO]['cursor']
    cache, feed = af.collect(REGISTRY, cache, Fake(fail=True), NOW)
    assert cache['sources'][REPO]['cursor'] == old_cursor
    assert feed['tasks'][0]['source_status'] == 'stale'
    assert feed['coverage'][0]['status'] == 'stale'


def test_private_source_never_exports_even_cached_content():
    cache, _ = af.collect(REGISTRY, {}, Fake([issue()]), NOW)
    cache, feed = af.collect(REGISTRY, cache, Fake(private=True), NOW)
    assert not feed['tasks']
    assert 'A small task' not in json.dumps(cache)
    assert feed['coverage'][0]['status'] == 'unavailable'


def test_closed_unmerged_is_not_merged():
    pr = issue(2, pull_request={}); pr.update(closed_at=TIME, state='closed')
    _, feed = af.collect(REGISTRY, {}, Fake([pr], pulls={2: {}}), NOW)
    assert {e['summary'] for e in feed['tasks'][0]['events']} == {'PR opened', 'PR closed without merge'}


def test_bot_noise_omitted_and_unstructured_comment_link_only():
    bot = comment(user={'type': 'Bot'}, id=10)
    _, feed = af.collect(REGISTRY, {}, Fake([issue()], [comment('Hello <script>'), bot]), NOW)
    assert len(feed['tasks'][0]['events']) == 2
    assert feed['tasks'][0]['events'][0]['summary'] == 'Discussion update recorded'


def test_invalid_source_does_not_poison_good_cache():
    bad = issue(); bad['created_at'] = 'not a date'
    cache, feed = af.collect(REGISTRY, {}, Fake([bad]), NOW)
    assert feed['coverage'][0]['status'] == 'stale'
    assert not feed['tasks']


def test_retention_and_foreign_link_safety():
    old = issue(); old['created_at'] = '2020-01-01T00:00:00Z'
    _, feed = af.collect(REGISTRY, {}, Fake([old]), NOW)
    assert not feed['tasks']
    with pytest.raises(ValueError):
        af.event(REPO, 1, 'x', TIME, 'progress', 'x', 'x', 'https://evil.example/', NOW)
    with pytest.raises(ValueError):
        af.instant('2026-10-13T19:00:00')


def test_grouping_requires_one_unambiguous_directive():
    assert af.closing_issue('```\nCloses #1\n```') is None
    assert af.closing_issue('Closes #1\nFixes #2') is None
    assert af.closing_issue('Closes https://github.com/Other/Repo/issues/1') is None


def test_budget_and_pagination_fail_explicitly():
    api = af.GitHub(budget=0)
    with pytest.raises(af.CollectionError, match='budget'):
        api.get('/repos/Example/Repo')
    api.get = lambda _: [{}] * 100
    with pytest.raises(af.CollectionError, match='pagination'):
        api.pages('/repos/Example/Repo/issues', {})


def test_server_snapshot_escapes_and_keeps_instance_out():
    bad = issue(); bad['title'] = '</script><script>alert(1)</script>'
    _, feed = af.collect(REGISTRY, {}, Fake([bad]), NOW)
    rendered = af.render_html(feed)
    assert '<script>alert(1)' not in rendered
    assert '&lt;/script&gt;' in rendered
    assert 'Development and Pulse campaign activity' in rendered


def test_partial_pr_scan_retains_events_and_resumes_without_duplicates():
    class Bounded(Fake):
        def get(self, path):
            if '/pulls/3' in path:
                raise af.CollectionError('request budget reached')
            return super().get(path)
    rows = [issue(2, pull_request={}), issue(3, pull_request={})]
    cache, feed = af.collect(REGISTRY, {}, Bounded(rows, pulls={2: {}}), NOW)
    assert len(feed['tasks']) == 1
    assert feed['coverage'][0]['status'] == 'partial'
    assert 'cursor' not in cache['sources'][REPO]
    # PR2 has no supplied response: a duplicate detail fetch would fail this test.
    cache, feed = af.collect(REGISTRY, cache, Fake(rows, pulls={3: {}}), NOW)
    assert len(feed['tasks']) == 2
    assert feed['coverage'][0]['status'] == 'ok'
    assert cache['sources'][REPO]['cursor']


def test_same_second_merge_wins_over_creation():
    row = issue(2, pull_request={})
    _, feed = af.collect(REGISTRY, {}, Fake([row], pulls={2: {'merged_at': TIME}}), NOW)
    assert feed['tasks'][0]['events'][0]['kind'] == 'merged'


def test_scientist_routes_to_its_own_board_when_no_organ_tag(tmp_path):
    p = tmp_path / 'repos.yaml'
    p.write_text('repos:\n  PyAutoScientist:\n    github: Example/PyAutoScientist\n  PyAutoFit:\n    github: Example/PyAutoFit\n')
    registry = af.sources(p)
    assert registry['Example/PyAutoScientist']['board'] == 'scientist'
    assert registry['Example/PyAutoFit']['board'] == 'mind'
