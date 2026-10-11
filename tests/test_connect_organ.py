"""Connection validation, record preservation and resumed setup through Broca."""
import copy
import json
from pathlib import Path
import stat
import sys
import urllib.error

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import connect_organ as connector
import instance_profile
import organism_board as board


@pytest.fixture
def pilot(tmp_path, monkeypatch):
    instance, repos = tmp_path / "instance.json", tmp_path / "repos.yaml"
    instance.write_text(json.dumps({"schema_version": 1, "name": "Mira Scientist",
        "repo": "scientist", "pages_url": "https://example.invalid/mira/",
        "projects": "projects.json", "organs": {}}))
    instance.chmod(0o640)
    repos.write_text("repos:\n  scientist:\n    github: Research/Mira\n"
                     "  guides:\n    github: Research/Communication\n")
    (tmp_path / "projects.json").write_text(json.dumps({"schema_version": 1,
        "resources": {}, "projects": {"spectra": {"name": "Spectra",
        "kind": "scientific_project", "public": True, "resources": {}}}}))
    (tmp_path / "research-note.md").write_text("Keep baseline selection A.\n")
    feed = {"schema_version": 1, "organ": "broca", "repo": "Communication",
        "status": "green", "headline": "No assistant required", "items": [],
        "updated": "2020-01-01T00:00:00Z", "pages_url": "https://example.invalid/guides/"}
    requests = []
    def get(url):
        requests.append(url)
        return json.dumps(feed)
    monkeypatch.setattr(board, "_get", get)
    args = ["--instance", str(instance), "--repos", str(repos), "--organ", "broca",
            "--repo", "guides", "--pages-url", "https://example.invalid/guides/"]
    return instance, repos, feed, requests, args


def snapshot(root):
    return {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}


def test_preview_connect_resume_and_render(pilot, monkeypatch, capsys):
    instance, repos, feed, requests, args = pilot
    original = snapshot(instance.parent)
    assert connector.main(args) == 0
    assert snapshot(instance.parent) == original
    assert "Preview only" in capsys.readouterr().out
    assert connector.main(args + ["--apply"]) == 0
    connected = snapshot(instance.parent)
    assert [k for k in original if original[k] != connected[k]] == ["instance.json"]
    assert stat.S_IMODE(instance.stat().st_mode) == 0o640
    assert connector.main(args + ["--apply"]) == 0
    assert snapshot(instance.parent) == connected
    assert requests == ["https://example.invalid/guides/state.json"] * 3
    profile, _ = instance_profile.load(instance, repos, board.theme())
    rendered = board.render(board.collect(instance=profile), "html")
    assert 'id="board-broca"' in rendered
    assert "Mira Scientist" in rendered
    assert 'id="board-heart"' not in rendered
    def unavailable(url):
        raise urllib.error.URLError("offline")
    monkeypatch.setattr(board, "_get", unavailable)
    data = board.collect(instance=profile)
    assert data["boards"][0]["error"] == "Evidence unavailable"
    assert 'id="board-broca"' in board.render(data, "html")
    with pytest.raises(SystemExit):
        connector.main(args + ["--apply"])
    assert snapshot(instance.parent) == connected


@pytest.mark.parametrize("change", [
    {"organ": "heart"}, {"repo": "PyAutoBroca"}, {"schema_version": 999},
    {"pages_url": "https://example.invalid/somewhere-else/"},
    {"updated": "not-a-date"}, {"status": "success"},
])
def test_invalid_evidence_never_connects(pilot, change):
    instance, _, feed, _, args = pilot
    before = snapshot(instance.parent)
    feed.update(change)
    with pytest.raises(SystemExit) as exc:
        connector.main(args + ["--apply"])
    assert exc.value.code == 2
    assert snapshot(instance.parent) == before


def test_failed_setup_can_resume_without_reinitializing(pilot, monkeypatch):
    instance, _, feed, _, args = pilot
    before = snapshot(instance.parent)
    monkeypatch.setattr(board, "_get", lambda _: "not json")
    with pytest.raises(SystemExit):
        connector.main(args + ["--apply"])
    assert snapshot(instance.parent) == before
    monkeypatch.setattr(board, "_get", lambda _: json.dumps(feed))
    assert connector.main(args + ["--apply"]) == 0
    assert json.loads(instance.read_text())["organs"]["broca"]["repo"] == "guides"


@pytest.mark.parametrize("status", ["red", "yellow", "grey", "green"])
def test_connection_does_not_require_healthy_or_fresh_evidence(pilot, status, capsys):
    _, _, feed, _, args = pilot
    feed["status"] = status
    connector.main(args + ["--apply"])
    output = capsys.readouterr().out
    assert f"Feed: {status}" in output and "2020-01-01" in output


def test_conflicting_connection_refuses_without_fetch(pilot, monkeypatch):
    instance, _, _, _, args = pilot
    connector.main(args + ["--apply"])
    before = instance.read_bytes()
    monkeypatch.setattr(board, "_get", lambda _: pytest.fail("conflict fetched evidence"))
    args[-1] = "https://example.invalid/different/"
    with pytest.raises(SystemExit):
        connector.main(args + ["--apply"])
    assert instance.read_bytes() == before


@pytest.mark.parametrize("filename", ["instance.json", "repos.yaml", "projects.json"])
def test_changed_inputs_reject_stale_plan(pilot, filename):
    instance, repos, _, _, _ = pilot
    prepared = connector.plan(instance, repos, "broca", "guides", "https://example.invalid/guides/")
    path = instance.parent / filename
    path.write_bytes(path.read_bytes() + b"\n")
    before = snapshot(instance.parent)
    with pytest.raises(ValueError, match="input changed"):
        connector.apply(prepared)
    assert snapshot(instance.parent) == before


def test_atomic_replace_failure_preserves_original_and_cleans_temp(pilot, monkeypatch):
    instance, repos, _, _, _ = pilot
    prepared = connector.plan(instance, repos, "broca", "guides", "https://example.invalid/guides/")
    before = snapshot(instance.parent)
    def fail(*args):
        raise OSError("write refused")
    monkeypatch.setattr(connector.os, "replace", fail)
    with pytest.raises(OSError):
        connector.apply(prepared)
    assert snapshot(instance.parent) == before


def test_other_connections_are_preserved(pilot):
    instance, _, _, requests, args = pilot
    config = json.loads(instance.read_text())
    config["organs"]["mind"] = {"repo": "scientist", "pages_url": "https://example.invalid/plans/"}
    previous = copy.deepcopy(config)
    instance.write_text(json.dumps(config))
    connector.main(args + ["--apply"])
    config = json.loads(instance.read_text())
    del config["organs"]["broca"]
    assert config == previous
    assert requests == ["https://example.invalid/guides/state.json"]


@pytest.mark.parametrize("key,value", [("--organ", "unknown"), ("--repo", "missing"),
                                      ("--pages-url", "http://example.invalid/")])
def test_invalid_choices_do_not_fetch_or_write(pilot, monkeypatch, key, value):
    instance, _, _, _, args = pilot
    before = snapshot(instance.parent)
    args[args.index(key) + 1] = value
    monkeypatch.setattr(board, "_get", lambda _: pytest.fail("invalid choice fetched"))
    with pytest.raises(SystemExit):
        connector.main(args + ["--apply"])
    assert snapshot(instance.parent) == before


def test_symlink_profile_is_refused(pilot):
    instance, _, _, _, args = pilot
    real = instance.with_name("real.json")
    instance.rename(real)
    instance.symlink_to(real)
    original = real.read_bytes()
    with pytest.raises(SystemExit):
        connector.main(args + ["--apply"])
    assert instance.is_symlink() and real.read_bytes() == original
