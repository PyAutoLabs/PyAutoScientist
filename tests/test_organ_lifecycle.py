"""Configuration transitions are independent of owner evidence and execution."""
import json
import pytest

from test_connect_organ import pilot, snapshot
import connect_organ as connector
import instance_profile
import organism_board as board
import organ_lifecycle as lifecycle


def prepare(pilot, action):
    instance, repos, _, _, _ = pilot
    return lifecycle.plan(instance, repos, 'broca', action, 'guides', 'https://example.invalid/guides/')


def test_setup_connection_pause_resume_preserves_records(pilot):
    instance, repos, feed, requests, args = pilot
    before = snapshot(instance.parent)
    p = prepare(pilot, 'setup')
    assert snapshot(instance.parent) == before and requests == []
    assert connector.apply(p)
    pending = snapshot(instance.parent)
    assert not connector.apply(prepare(pilot, 'setup'))
    assert snapshot(instance.parent) == pending
    profile, _ = instance_profile.load(instance, repos, board.theme())
    data = board.collect(instance=profile)
    assert data['boards'] == [] and requests == []
    page = board.render(data, 'html')
    assert 'Setup incomplete' in page and 'Available organs' in page
    assert 'id="board-broca"' not in page and 'id="setup-broca"' in page
    connector.main(args + ['--apply'])
    config = json.loads(instance.read_text())
    assert 'broca' not in config['organ_setup']
    assert config['organs']['broca']['repo'] == 'guides'
    assert connector.apply(prepare(pilot, 'pause'))
    paused = snapshot(instance.parent)
    requests.clear()
    profile, _ = instance_profile.load(instance, repos, board.theme())
    data = board.collect(instance=profile)
    assert requests == [] and data['boards'][0]['feed'] is None
    assert 'Paused' in board.render(data, 'html')
    assert not connector.apply(prepare(pilot, 'pause'))
    with pytest.raises(SystemExit):
        connector.main(args + ['--apply'])
    assert snapshot(instance.parent) == paused and requests == []
    feed['repo'] = 'Wrong'
    with pytest.raises(ValueError):
        prepare(pilot, 'resume')
    assert snapshot(instance.parent) == paused
    feed['repo'] = 'Communication'; feed['status'] = 'grey'
    assert connector.apply(prepare(pilot, 'resume'))
    config = json.loads(instance.read_text())
    assert not config['organs']['broca'].get('paused', False)
    assert snapshot(instance.parent)['research-note.md'] == before['research-note.md']
    assert snapshot(instance.parent)['projects.json'] == before['projects.json']


@pytest.mark.parametrize('action', ['pause', 'resume'])
def test_disconnected_cannot_pause_or_resume(pilot, action):
    before = snapshot(pilot[0].parent)
    with pytest.raises(ValueError, match='connected'):
        prepare(pilot, action)
    assert snapshot(pilot[0].parent) == before and pilot[3] == []


@pytest.mark.parametrize('filename', ['instance.json', 'repos.yaml', 'projects.json'])
def test_offline_transition_rejects_changed_inputs(pilot, filename):
    prepared = prepare(pilot, 'setup')
    path = pilot[0].parent / filename
    path.write_bytes(path.read_bytes()+b'\n')
    before = snapshot(pilot[0].parent)
    with pytest.raises(ValueError, match='input changed'):
        connector.apply(prepared)
    assert snapshot(pilot[0].parent) == before


def test_failed_promotion_keeps_pending_and_conflict_never_fetches(pilot):
    instance, _, feed, requests, args = pilot
    connector.apply(prepare(pilot, 'setup'))
    before = snapshot(instance.parent)
    feed['pages_url'] = 'https://example.invalid/wrong/'
    with pytest.raises(SystemExit):
        connector.main(args + ['--apply'])
    assert snapshot(instance.parent) == before
    requests.clear()
    with pytest.raises(ValueError, match='conflict'):
        lifecycle.plan(instance, pilot[1], 'broca', 'setup', 'guides', 'https://example.invalid/other/')
    assert requests == []


@pytest.mark.parametrize('bad', ['overlap', 'paused-string', 'pending-key', 'pending-fields'])
def test_bad_schema_is_rejected(pilot, bad):
    instance, repos, _, _, args = pilot
    connector.main(args + ['--apply'])
    cfg = json.loads(instance.read_text())
    if bad == 'overlap': cfg['organ_setup'] = {'broca': cfg['organs']['broca']}
    elif bad == 'paused-string': cfg['organs']['broca']['paused'] = 'true'
    elif bad == 'pending-key': cfg['organ_setup'] = {'fake': {}}
    else: cfg['organ_setup'] = {'mind': {'repo': 'guides', 'pages_url': 'https://example.invalid/', 'local_path': '/private'}}
    instance.write_text(json.dumps(cfg))
    with pytest.raises(ValueError): instance_profile.load(instance, repos, board.theme())


def test_setup_cli_preview_and_missing_arguments(pilot):
    instance, repos, _, requests, args = pilot
    before = snapshot(instance.parent)
    assert lifecycle.main(['setup'] + args) == 0
    assert snapshot(instance.parent) == before and not requests
    with pytest.raises(SystemExit):
        lifecycle.main(['setup', '--instance', str(instance), '--repos', str(repos), '--organ', 'broca'])
    assert snapshot(instance.parent) == before


def test_paused_heart_is_not_a_readiness_verdict():
    snap = {"boards": [{"name": "Heart", "paused": True, "headline": "Observation paused", "color": "grey"}]}
    assert board.heart_word(snap) == "UNKNOWN"
