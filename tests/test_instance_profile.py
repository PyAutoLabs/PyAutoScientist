"""Independent starter isolation and connected-feed identity, with no network."""
import copy
import json
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import instance_profile as profiles
import organism_board as ob


@pytest.fixture
def configured(tmp_path):
    config = {'schema_version': 1, 'name': 'Mira & <Research>', 'repo': 'scientist',
              'pages_url': 'https://research.example/mira', 'projects': 'projects.json',
              'organs': {}}
    body = {'repos': {'scientist': {'github': 'ExampleResearch/Mira'},
                      'plans': {'github': 'ExampleResearch/ResearchPlans'}}}
    (tmp_path / 'projects.json').write_text(json.dumps({'schema_version': 1, 'resources': {}, 'projects': {}}))
    path, repos = tmp_path / 'instance.json', tmp_path / 'repos.yaml'
    repos.write_text(yaml.safe_dump(body))
    def load(updated=None):
        path.write_text(json.dumps(updated or config))
        return profiles.load(path, repos, ob.theme())
    return config, load, path, repos


def test_empty_instance_is_independent_and_makes_no_requests(configured, monkeypatch, capsys):
    config, load, path, repos = configured
    load()
    monkeypatch.setattr(ob, '_get', lambda *_: pytest.fail('empty starter contacted a feed'))
    monkeypatch.setattr(ob, '_owner', lambda: pytest.fail('explicit profile read framework remote'))
    before = {p: p.read_bytes() for p in path.parent.iterdir()}
    assert ob.main(['--instance', str(path), '--repos', str(repos), '--html']) == 0
    page = capsys.readouterr().out
    assert 'Mira &amp; &lt;Research&gt;' in page
    assert '<b>Mira &amp; &lt;Research&gt;</b>' in page
    assert 'https://github.com/ExampleResearch/Mira' in page
    assert 'No public projects configured.' in page
    assert 'No organs connected.' in page
    assert 'class="boards"' not in page
    assert 'class="organ-card"' not in page
    assert 'PyAutoLabs' not in page
    assert 'PyAutoFit' not in page
    assert 'Use the health skill.' not in page
    assert all(p.read_bytes() == data for p, data in before.items())


def test_selected_connection_uses_canonical_repo_and_custom_host(configured, monkeypatch):
    config, load, _, _ = configured
    config['organs']['mind'] = {'repo': 'plans', 'pages_url': 'https://research.example/boards/plans'}
    profile, _ = load()
    urls = []
    feed = {'schema_version': 1, 'organ': 'mind', 'repo': 'ResearchPlans', 'status': 'green',
            'headline': 'No tasks yet', 'updated': '2026-10-11T12:00:00Z',
            'pages_url': 'https://research.example/boards/plans/', 'items': []}
    def get(url):
        urls.append(url)
        return json.dumps(feed)
    monkeypatch.setattr(ob, '_get', get)
    snap = ob.collect(instance=profile)
    assert urls == ['https://research.example/boards/plans/state.json']
    assert len(snap['boards']) == 1
    assert snap['boards'][0]['error'] is None
    assert snap['boards'][0]['repo'] == 'ResearchPlans'
    page = ob.render(snap, 'html')
    assert '<b>Mira &amp; &lt;Research&gt;</b>' in page
    assert 'data-organ="mind"' in page
    assert 'https://research.example/boards/plans/' in page
    assert 'id="board-heart"' not in page
    assert 'pyautolabs.github.io' not in page
    assert snap['instance']['pages_url'] == 'https://research.example/mira/'
    assert 'projects' not in snap['instance']
    assert ob.render(snap, 'md').startswith('# Mira &amp; &lt;Research&gt; Dashboard')
    snap['instance']['name'] = '[Mira](https://example.com/)'
    assert ob.render(snap, 'md').startswith(r'# \[Mira\](https://example.com/) Dashboard')
    feed['repo'] = 'PyAutoMind'
    bad = ob.collect(instance=profile)
    assert bad['boards'][0]['error'] == 'Evidence unavailable'
    assert bad['boards'][0]['feed'] is None
    assert 'data-organ="mind"' in ob.render(bad, 'html')
    assert profile['boards'][0].get('error') is None  # collection never mutates config


def test_offline_check_never_collects(configured, monkeypatch, capsys):
    _, load, path, repos = configured
    load()
    monkeypatch.setattr(ob, 'collect', lambda **_: pytest.fail('offline validation collected feeds'))
    assert ob.main(['--instance', str(path), '--repos', str(repos), '--check-instance']) == 0
    assert '0 public projects' in capsys.readouterr().out


@pytest.mark.parametrize('field,value', [
    ('schema_version', True), ('name', ''), ('name', 'two\nlines'), ('repo', 'missing'),
    ('pages_url', 'javascript:alert(1)'), ('pages_url', 'https://user:pass@example.com/'),
    ('pages_url', 'https://example.com/?private=yes'), ('pages_url', 'https://example.com/#anchor'),
    ('projects', '../projects.json'), ('projects', '/private/projects.json'),
    ('organs', {'unknown': {}}), ('organs', {'organism': {}}),
    ('organs', {'mind': {'repo': 'missing', 'pages_url': 'https://example.com/'}}),
    ('organs', {'mind': {'repo': 'plans'}}), ('organs', []),
])
def test_invalid_profile_fails_before_collection(configured, field, value):
    config, load, _, _ = configured
    config = copy.deepcopy(config)
    config[field] = value
    with pytest.raises(ValueError):
        load(config)


def test_profile_requires_its_own_projects_file(configured, monkeypatch):
    _, load, path, repos = configured
    load()
    (path.parent / 'projects.json').unlink()
    monkeypatch.setattr(ob, 'collect', lambda **_: pytest.fail('invalid profile collected feeds'))
    with pytest.raises(SystemExit) as exc:
        ob.main(['--instance', str(path), '--repos', str(repos), '--json'])
    assert exc.value.code == 2


def test_connect_project_without_assistant_reuses_body_map(configured, monkeypatch, capsys):
    _, load, path, repos = configured
    load()
    body = yaml.safe_load(repos.read_text())
    body['repos']['ocean-code'] = {'github': 'ExampleResearch/OceanModels'}
    repos.write_text(yaml.safe_dump(body))
    projects = {'schema_version': 1,
                'resources': {'code': {'name': 'Ocean models', 'repo': 'ocean-code', 'public': True}},
                'projects': {'ocean': {'name': 'Ocean study', 'kind': 'scientific_project',
                                       'public': True, 'resources': {'software': ['code']}}}}
    (path.parent / 'projects.json').write_text(json.dumps(projects))
    monkeypatch.setattr(ob, '_get', lambda *_: pytest.fail('project-only instance collected an organ'))
    assert ob.main(['--instance', str(path), '--repos', str(repos), '--json']) == 0
    snap = json.loads(capsys.readouterr().out)
    assert snap['boards'] == []
    project = snap['project_resources']['projects'][0]
    assert project['name'] == 'Ocean study'
    assert project['groups'][0]['resources'][0]['links'][0]['url'] == 'https://github.com/ExampleResearch/OceanModels'
    assert all(g['relation'] != 'assistants' for g in project['groups'])
    assert 'Ocean study' in ob.render(snap, 'html')
