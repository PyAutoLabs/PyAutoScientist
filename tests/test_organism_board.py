"""tests/test_organism_board.py — the umbrella router board (fixture-only).

Run with `python -m pytest tests/`, also exercised by board_tests.yml. What matters:
routing follows the Heart verdict, every fmt renders from a snapshot, rows
degrade to "unavailable", and the html is self-contained.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import organism_board as ob  # noqa: E402


def test_theme_finds_grouped_brain_from_outer_workspace(tmp_path, monkeypatch):
    brain_board = tmp_path / "organs" / "PyAutoBrain" / "board"
    brain_board.mkdir(parents=True)
    (brain_board / "_theme.py").write_text("GROUPED_THEME = True\n")
    monkeypatch.setenv("PYAUTO_ROOT", str(tmp_path))
    monkeypatch.delenv("PYAUTO_BRAIN", raising=False)
    monkeypatch.setattr(ob, "HOME", tmp_path / "PyAutoScientist")
    monkeypatch.delitem(sys.modules, "_theme", raising=False)
    monkeypatch.setattr(sys, "path", sys.path.copy())
    try:
        assert ob.theme().GROUPED_THEME
    finally:
        sys.modules.pop("_theme", None)


def test_workspace_root_marker_stays_at_outer_root(tmp_path, monkeypatch):
    scientist = tmp_path / "organs" / "PyAutoScientist"
    scientist.mkdir(parents=True)
    (tmp_path / ".pyauto-root").touch()
    monkeypatch.delenv("PYAUTO_ROOT", raising=False)
    monkeypatch.setattr(ob, "HOME", scientist)
    assert ob._workspace_root() == tmp_path


def _snap(heart="GREEN · 100", color="brightgreen"):
    return {
        "generated": "2026-06-01T00:00:00+00:00",
        "owner": "SomeOrg",
        "boards": [
            {"name": "Mind", "repo": "PyAutoMind", "role": "tasks",
             "door": "Use the start-dev skill. <prompt-path>",
             "url": "https://someorg.github.io/PyAutoMind/",
             "headline": "2 in flight · 9 backlog", "color": None,
             "counts": {"In flight": 2, "Backlog": 9}},
            {"name": "Heart", "repo": "PyAutoHeart", "role": "health",
             "door": "Use the health skill.", "url": "https://someorg.github.io/PyAutoHeart/",
             "headline": heart, "color": color},
            {"name": "Hands", "repo": "PyAutoHands", "role": "releases",
             "door": "Use the release skill.", "url": "https://someorg.github.io/PyAutoHands/",
             "headline": None, "color": None},
            {"name": "Memory", "repo": "PyAutoMemory", "role": "knowledge",
             "door": "Use the memory skill. <topic>", "url": "https://someorg.github.io/PyAutoMemory/",
             "headline": "10 pages · 50% cited", "color": "blueviolet"},
        ],
    }


def test_routing_follows_the_heart():
    assert "pick a task on the PyAutoMind Dashboard" in ob.route_hint(_snap("GREEN · 100"))
    assert "start at the PyAutoHeart Dashboard" in ob.route_hint(_snap("RED · 40"))
    assert "start at the PyAutoHeart Dashboard" in ob.route_hint(_snap("YELLOW · 70"))
    assert "re-run checks" in ob.route_hint(_snap("STALE · 65"))
    assert "unavailable" in ob.route_hint(
        {"boards": [{"name": "Heart", "headline": None}]})


def test_every_fmt_renders_and_degrades():
    s = _snap()
    for fmt in ("md", "md-brief", "html", "badge", "json"):
        out = ob.render(s, fmt)
        assert out
    assert "unavailable" in ob.render(s, "md")  # the Hands row degraded


def test_badge_carries_verdict_and_backlog():
    b = json.loads(ob.render(_snap("RED · 40", "red"), "badge"))
    assert b == {"schemaVersion": 1, "label": "organism",
                 "message": "RED · 9 tasks queued", "color": "red"}


def test_html_is_self_contained_with_door_chips():
    out = ob.render(_snap(), "html")
    assert out.lstrip().startswith("<!doctype html>")
    # the header links the markdown twin and the repository front door
    assert '<a href="dashboard.md">markdown version</a>' in out
    assert ('<a href="https://github.com/SomeOrg/PyAutoScientist/blob/main/'
            'README.md">GitHub Page</a>') in out
    assert "Use the health skill." in out and "Use the start-dev skill." in out and "data-cmd=" in out
    assert "src=" not in out and "<link" not in out.lower()
    assert "fetch(" not in out and "XMLHttpRequest" not in out
    stripped = re.sub(r'data-cmd="[^"]*"', "", out)
    stripped = re.sub(r"<textarea\b[^>]*>.*?</textarea>", "", stripped, flags=re.S)
    for m in re.finditer(r"(?:http|https)://", stripped):
        before = stripped[max(0, m.start() - 30):m.start()]
        assert 'href="' in before or "href='" in before


def test_html_wears_the_shared_family_theme():
    # The look is the Brain's `board/_theme.py`, not a stylesheet copied in
    # here: the page must carry this board's hero (mark, wordmark, tagline)
    # and its accent, or it has silently fallen out of the family.
    t = ob.theme()
    out = ob.render(_snap(), "html")
    assert t.MARKS[ob.BOARD_KEY] in out
    assert t.ORGANS[ob.BOARD_KEY]["tagline"] in out
    assert t.ORGANS[ob.BOARD_KEY]["ink_dark"] in out
    assert "#58a6ff" not in out  # the old hard-coded GitHub blue


def test_mind_counts_parser():
    md = ("| Where | Count |\n|---|---:|\n"
          "| [In flight](#a) (`active/`) | 4 |\n| [Backlog](#b) (`draft/`) | 151 |\n")
    counts = {k: int(v) for k, v in ob.MIND_COUNT_RE.findall(md)}
    assert counts == {"In flight": 4, "Backlog": 151}


def test_panel_links_each_work_owner_and_preserves_doors():
    snap = _snap()
    rendered = ob.render(snap, "html")
    assert 'data-orchestration-panel' in rendered
    assert 'Work on GitHub:' in rendered
    assert "Carry clearly authorized work through the appropriate skills" in rendered
    assert "Preserve applicable development, compute, community-reply, merge and release approval requirements." in rendered
    for row in snap["boards"]:
        assert f'https://github.com/SomeOrg/{row["repo"]}' in rendered
    assert rendered.count("copy the door command") == len(snap["boards"])
    assert rendered.index('data-orchestration-panel') < rendered.index("class='organ'")


def test_panel_refresh_uses_router_capture(monkeypatch):
    theme = ob.theme()
    calls = []
    monkeypatch.setattr(theme, "orchestration_panel", lambda *a, **kw: calls.append(kw) or "")
    snap = _snap()
    snap["boards"][2]["headline"] = "Release information collected"
    ob.render(snap, "html")
    assert calls[0]["refreshed_at"] == snap["generated"]
    assert calls[0]["refresh_url"] == "https://github.com/SomeOrg/PyAutoScientist/actions/workflows/organism_board.yml"

    snap["boards"][2]["headline"] = None
    ob.render(snap, "html")
    assert calls[-1]["refreshed_at"] is None
    snap["boards"] = []
    ob.render(snap, "html")
    assert calls[-1]["refreshed_at"] is None
