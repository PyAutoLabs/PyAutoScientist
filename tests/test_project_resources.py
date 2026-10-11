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
