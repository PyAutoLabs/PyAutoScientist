"""Publication boundaries and reusable relationship semantics (offline)."""

import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import project_resources as pr
import organism_board as ob


@pytest.fixture
def inputs():
    return ({"schema_version": 1,
             "resources": {
                 "library": {"name": "Shared code", "repo": "stable-code", "public": True},
                 "docs": {"name": "Guide", "repo": "stable-code", "path": "guide/start here.md",
                          "ref": "release/1", "published_url": "https://docs.example.org/", "public": True},
                 "private": {"name": "Secret records", "repo": "hidden", "public": False}},
             "projects": {
                 "alpha": {"name": "Alpha", "kind": "software_family", "public": True,
                           "resources": {"software": ["library"], "documentation": ["docs"], "records": ["private"]}},
                 "beta": {"name": "Beta", "kind": "scientific_project", "public": True,
                          "resources": {"dependencies": ["library"]}}}},
            {"repos": {"stable-code": {"github": "OtherLab/renamed-code"},
                       "hidden": {"github": "PrivateOwner/secret"}}})


def test_shared_resources_optional_assistants_and_distinct_project_kinds(inputs):
    result = pr.resolve(*inputs)
    first, second = result["projects"]
    assert first["groups"][0]["resources"][0] == second["groups"][0]["resources"][0]
    assert not any(g["relation"] == "assistants" for p in result["projects"] for g in p["groups"])
    assert first["kind"] != second["kind"]
    doc = first["groups"][1]["resources"][0]
    assert doc["links"][0]["url"] == "https://github.com/OtherLab/renamed-code/tree/release%2F1/guide/start%20here.md"
    assert doc["links"][1]["url"] == "https://docs.example.org/"


def test_private_and_unapproved_items_never_reach_snapshot_or_html(inputs):
    config, body_map = inputs
    config["projects"]["secret"] = {"name": "Hidden project", "kind": "scientific_project"}
    del config["resources"]["docs"]["public"]
    result = pr.resolve(config, body_map)
    output = json.dumps(result) + pr.render_html(result)
    for hidden in ("Hidden project", "Secret records", "PrivateOwner", "secret", "Guide", "docs.example.org"):
        assert hidden not in output
    assert inputs[0]["resources"]["private"]["public"] is False


@pytest.mark.parametrize("field,value", [
    ("repo", "not-registered"), ("repo", []), ("path", "../private"),
    ("path", "/etc/passwd"), ("path", "docs\\private"),
    ("published_url", "javascript:alert(1)"), ("published_url", "//evil.test"),
    ("published_url", "https://name:password@example.org"),
    ("published_url", "https://example.org\n.evil.test"),
    ("published_url", "https://example.org\\evil"), ("public", "true"),
    ("unexpected", True),
    ("ref", ".."), ("ref", "bad\nref"),
])
def test_invalid_resource_configuration_fails_closed(inputs, field, value):
    config, body_map = inputs
    config["resources"]["library"][field] = value
    with pytest.raises(ValueError):
        pr.resolve(config, body_map)


@pytest.mark.parametrize("relations", [{"software": ["missing"]}, {"software": ["library", "library"]},
                                        {"unknown": []}, {"software": "library"}, {"software": [{}]}])
def test_bad_relationships_are_not_silently_omitted(inputs, relations):
    inputs[0]["projects"]["alpha"]["resources"] = relations
    with pytest.raises(ValueError):
        pr.resolve(*inputs)


def test_versions_empty_projects_and_external_only_resource(inputs):
    config, body_map = inputs
    config["schema_version"] = 2
    with pytest.raises(ValueError):
        pr.resolve(config, body_map)
    assert pr.resolve({"schema_version": 1}, {"repos": {}}) == {"schema_version": 1, "projects": []}
    config["schema_version"] = 1
    config["projects"]["alpha"]["resources"] = {}
    del config["resources"]["docs"]["repo"]
    del config["resources"]["docs"]["path"]
    del config["resources"]["docs"]["ref"]
    assert "No public resources configured" in pr.render_html(pr.resolve(config, body_map))


def test_labels_are_escaped_and_disclosures_work_without_javascript(inputs):
    inputs[0]["projects"]["alpha"]["name"] = '<script>alert("x")</script>'
    result = pr.resolve(*inputs)
    html = pr.render_html(result)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "<script>" not in pr.render_markdown(result)
    assert "&lt;script&gt;" in pr.render_markdown(result)
    assert '<details class="organ-card project-card" id="project-alpha">' in html
    assert ' open' not in html
    assert '<a href="https://docs.example.org/">Published</a>' in html


def test_renaming_identity_changes_links_without_changing_relationships(inputs):
    original = copy.deepcopy(inputs[0])
    inputs[1]["repos"]["stable-code"]["github"] = "IndependentResearch/NewName"
    result = pr.resolve(*inputs)
    assert result["projects"][0]["groups"][0]["resources"][0]["links"][0]["url"].endswith("IndependentResearch/NewName")
    assert inputs[0] == original


def test_board_integration_and_offline_cli(inputs, tmp_path, monkeypatch, capsys):
    config, body_map = inputs
    config_path, repos_path = tmp_path / "projects.json", tmp_path / "repos.yaml"
    config_path.write_text(json.dumps(config))
    repos_path.write_text(json.dumps(body_map))  # JSON is YAML-compatible.
    monkeypatch.setattr(ob, "collect", lambda: pytest.fail("offline check collected feeds"))
    assert ob.main(["--check-projects", "--projects", str(config_path), "--repos", str(repos_path)]) == 0
    assert "2 public projects" in capsys.readouterr().out
    snapshot = {"owner": "Example", "boards": [], "project_resources": pr.load(config_path, repos_path)}
    html = ob.render(snapshot, "html")
    assert html.index('data-orchestration-panel') < html.index('id="projects"') < html.index('id="dashboards"')
    assert "Alpha" in ob.render(snapshot, "md")
    assert "Secret records" not in ob.render(snapshot, "json")


def test_routes_combine_display_rows_without_losing_typed_relationships(inputs):
    config, body_map = inputs
    config["resources"]["communication"] = {
        "name": "Communication", "public": True, "published_url": "https://example.org/board/"}
    config["routes"] = {"documentation": "communication", "workspaces": "communication"}
    config["projects"]["alpha"]["resources"]["workspaces"] = ["library"]
    snapshot = pr.resolve(config, body_map)
    groups = snapshot["projects"][0]["groups"]
    assert {g["relation"] for g in groups} == {"software", "workspaces", "documentation"}
    rows = pr.display_groups(snapshot["projects"][0])
    assert [r["label"] for r in rows] == ["Software", "Communication"]
    assert [r["id"] for r in rows[1]["resources"]] == ["library", "docs"]
    page = pr.render_html(snapshot)
    assert '<dt><a href="https://example.org/board/">Communication</a></dt>' in page
    assert '<a href="https://github.com/OtherLab/renamed-code">Shared code</a>' in page
    assert '[Communication](https://example.org/board/)' in pr.render_markdown(snapshot)


def test_private_dashboard_falls_back_without_leaking_metadata(inputs):
    config, body_map = inputs
    config["resources"]["private"]["published_url"] = "https://private.example.org/"
    config["routes"] = {"documentation": "private"}
    snapshot = pr.resolve(config, body_map)
    assert "dashboard" not in snapshot["projects"][0]["groups"][1]
    assert "private.example.org" not in json.dumps(snapshot)
    assert "<dt>Documentation</dt>" in pr.render_html(snapshot)


@pytest.mark.parametrize("routes", [[], {"typo": "docs"}, {"profiling": "missing"},
                                    {"profiling": []}, {"tests": "library"}])
def test_bad_routes_are_rejected(inputs, routes):
    inputs[0]["routes"] = routes
    with pytest.raises(ValueError):
        pr.resolve(*inputs)


def test_dashboard_headings_remain_visible_and_separate(inputs):
    snapshot = {"owner": "Example", "boards": [], "project_resources": pr.resolve(*inputs)}
    page = ob.render(snapshot, "html")
    assert page.index('<h2 id="projects-heading">Projects</h2>') < page.index('<h2 id="dashboards-heading">Dashboards</h2>') < page.index('id="dashboards"')


def test_catalogue_deduplicates_public_relationships():
    from project_resources import catalogue, resolve
    config = {'schema_version': 1, 'resources': {
        'shared': {'name': 'Guide', 'repo': 'guide', 'public': True},
        'secret': {'name': 'Secret', 'repo': 'guide', 'public': False}},
        'projects': {key: {'name': key, 'kind': 'scientific_project', 'public': public,
                          'resources': {'tutorials': ['shared', 'secret']}}
                     for key, public in [('one', True), ('two', True), ('private', False)]}}
    result = catalogue(resolve(config, {'repos': {'guide': {'github': 'Example/Guide'}}}))
    assert len(result['resources']) == 1
    resource = result['resources'][0]
    assert resource['repo'] == 'guide'
    assert resource['github'] == 'Example/Guide'
    assert [p['id'] for p in resource['projects']] == ['one', 'two']
    assert 'Secret' not in str(result) and 'private' not in str(result)


def test_owner_deep_links_preserve_sources_and_snapshot(inputs):
    config, body_map = inputs
    config["resources"]["communication"] = {
        "name": "Broca", "public": True, "published_url": "https://example.org/broca/"}
    config["routes"] = {"documentation": "communication"}
    snapshot = pr.resolve(config, body_map)
    before = copy.deepcopy(snapshot)
    rows = pr.display_groups(snapshot["projects"][0])
    docs = next(row for row in rows if row["label"] == "Broca")["resources"][0]
    assert {link["url"] for link in docs["links"]} == {
        "https://docs.example.org/", "https://example.org/broca/#resource-docs",
        "https://github.com/OtherLab/renamed-code/tree/release%2F1/guide/start%20here.md"}
    assert snapshot == before


def test_available_resources_are_not_connected_or_exported(inputs):
    config, body_map = inputs
    before = pr.catalogue(pr.resolve(*inputs))
    config['projects']['alpha']['available'] = {
        'inference': {'name': 'renamed_experiments', 'public': True},
        'assistants': {'name': 'optional_helper', 'public': True}}
    snapshot = pr.resolve(config, body_map)
    assert pr.catalogue(snapshot) == before
    inference = next(g for g in snapshot['projects'][0]['groups'] if g['relation'] == 'inference')
    assert inference['resources'] == []
    assert inference['available'][0]['id'] == 'inference'
    page = pr.render_html(snapshot)
    assert 'Available to add' in page and 'readonly' in page
    assert 'renamed_experiments</span>' in page
    assert 'href="https://github.com/renamed_experiments' not in page
    assert r'renamed\_experiments' in pr.render_markdown(snapshot)
    assert 'Do not infer identity or access from names' in page


@pytest.mark.parametrize('available', [
    [], {'unknown': {'name': 'x'}}, {'software': {'name': 'x'}},
    {'tests': {'name': 'x', 'repo': 'library'}},
    {'tests': {'name': 'x', 'public': 'true'}},
    {'tests': {'name': ''}}, {'tests': 'x'},
    {'tests': {'name': 'x', 'status': 'active'}},
    {'documentation': {'name': 'already-connected', 'public': True}},
])
def test_available_configuration_rejects_ambiguous_states(inputs, available):
    inputs[0]['projects']['alpha']['available'] = available
    with pytest.raises(ValueError):
        pr.resolve(*inputs)


def test_private_available_entries_and_routes_never_leak(inputs):
    config, body_map = inputs
    config['projects']['alpha']['available'] = {
        'tests': {'name': 'private-tests', 'public': False},
        'inference': {'name': 'unapproved-inference'},
        'workspaces': {'name': 'public-workspace', 'public': True}}
    config['projects']['beta']['public'] = False
    config['projects']['beta']['available'] = {'tests': {'name': 'private-project-tests', 'public': True}}
    config['resources']['private']['published_url'] = 'https://private.example.org/'
    config['routes'] = {'workspaces': 'private'}
    result = pr.resolve(config, body_map)
    for output in [json.dumps(result), pr.render_html(result), pr.render_markdown(result)]:
        assert 'public-workspace' in output
        for private in ['private-tests', 'unapproved-inference', 'private-project-tests', 'private.example.org']:
            assert private not in output


def test_available_uses_dashboard_groups_without_inventing_detail_anchor(inputs):
    config, body_map = inputs
    config['resources']['broca'] = {'name': 'Broca', 'published_url': 'https://example.org/broca/', 'public': True}
    config['routes'] = {'documentation': 'broca', 'workspaces': 'broca'}
    config['projects']['alpha']['available'] = {'workspaces': {'name': 'any-name', 'public': True}}
    snapshot = pr.resolve(config, body_map)
    row = next(r for r in pr.display_groups(snapshot['projects'][0]) if r['label'] == 'Broca')
    assert [r['id'] for r in row['resources']] == ['docs']
    assert [r['id'] for r in row['available']] == ['workspaces']
    page = pr.render_html(snapshot)
    assert '#resource-docs' in page
    assert '#resource-workspaces' not in page


def test_available_transition_to_connected_is_explicit_and_name_independent(inputs):
    config, body_map = inputs
    config['projects']['alpha']['available'] = {'workspaces': {'name': 'hint-only', 'public': True}}
    config['projects']['alpha']['resources']['workspaces'] = ['private']
    with pytest.raises(ValueError, match='already connected'):
        pr.resolve(*inputs)  # private connections must not look unconfigured
    del config['projects']['alpha']['available']['workspaces']
    config['projects']['alpha']['resources']['workspaces'] = ['library']
    page = pr.render_html(pr.resolve(*inputs))
    assert 'hint-only' not in page and 'Available to add' not in page
    assert 'https://github.com/OtherLab/renamed-code' in page


def test_available_labels_are_plain_text_and_rendering_preserves_inputs(inputs):
    inputs[0]['projects']['alpha']['available'] = {
        'tests': {'name': '</textarea><script>bad()</script>', 'public': True}}
    before = copy.deepcopy(inputs)
    snapshot = pr.resolve(*inputs)
    page = pr.render_html(snapshot)
    assert '<script>bad()' not in page and '&lt;script&gt;bad()' in page
    assert inputs == before


def test_connected_example_is_offline_and_independent(monkeypatch, capsys):
    root = Path(__file__).resolve().parents[1]
    folder = root / 'examples' / 'connected-project'
    monkeypatch.setattr(ob, '_get', lambda *a, **k: pytest.fail('example fetched a feed'))
    args = ['--instance', str(folder / 'instance.json'), '--repos', str(folder / 'repos.yaml')]
    assert ob.main(args + ['--html']) == 0
    page = capsys.readouterr().out
    assert 'Mira Scientist' in page and 'SpectralAnalysis' in page
    assert page.count('class="available-resource"') == 8
    assert 'autolens' not in page.lower()
    assert ob.main(args + ['--catalogue']) == 0
    catalogue = json.loads(capsys.readouterr().out)
    assert [r['repo'] for r in catalogue['resources']] == ['spectra-code']
