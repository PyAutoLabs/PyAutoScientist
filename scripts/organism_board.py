"""scripts/organism_board.py — the PyAutoScientist Dashboard.

The umbrella ROUTER over the organism's live dashboards: one row per organ
board — Brain (operations), Mind (tasks), Heart (health), Hands (releases),
Memory (knowledge) — each carrying that board's own live headline and link,
topped by a "where to work next" banner keyed off the Heart's verdict (Heart
red/yellow → start at the health board; green → pick a task on the Mind
board). A glance here tells you WHICH board to open; the work happens there.

**Sources** (plain HTTPS, no tokens): the Heart/Hands/Memory boards each
publish a shields ``badge.json`` beside their page — their own headline in
their own words — and the Mind's counts are parsed from its committed
``dashboard.md``. Every row degrades to "unavailable" honestly; nothing is
recomputed here (each organ's board stays the authority on itself).

**Identity** derives from ``git remote`` (an adopting fork gets its own URLs
for free). Rendered fresh by ``.github/workflows/organism_board.yml`` into
GitHub Pages + ``badge.json`` + the README strip between the
``scientist:begin/end`` markers — nothing is committed except the strip.

Usage:
    python scripts/organism_board.py [--md | --md-brief | --html | --badge | --json]
Tests: ``python -m pytest tests/`` (run ad hoc; this repo has no CI gate).
"""

from __future__ import annotations

import datetime
import html as _html
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]

# The family look lives once, in the Brain (``board/_theme.py``): the
# stylesheet, the hero that redraws this organ's logo as a mark, and the
# cross-board footer. It is imported rather than copied, so the look moves for
# the whole family at once — organism_board.yml checks PyAutoBrain out beside
# this repo, and a local run finds the sibling checkout the same way the other
# PyAuto tools resolve each other.
BOARD_KEY = "organism"  # this board's entry in the Brain's palette table


def _workspace_root() -> Path:
    """Where the sibling PyAuto checkouts live: `$PYAUTO_ROOT`, else `~/Code`.

    The org's own directory name is an instance fact, so it is never written
    here — a workspace that does not follow the default sets `$PYAUTO_ROOT`
    (the same variable the dev-flow doors read).
    """
    return Path(os.environ.get("PYAUTO_ROOT") or Path.home() / "Code")


def theme():
    """The shared theme module, or a RuntimeError naming the fix.

    Only the html path needs it; ``--md``/``--badge``/``--json`` never call
    here, so the digest keeps working with no PyAutoBrain in reach.
    """
    for cand in (os.environ.get("PYAUTO_BRAIN"), HOME / "PyAutoBrain",
                 HOME.parent / "PyAutoBrain",
                 _workspace_root() / "PyAutoBrain"):
        if not cand:
            continue
        board = Path(cand) / "board"
        if (board / "_theme.py").is_file():
            if str(board) not in sys.path:
                sys.path.insert(0, str(board))
            import _theme
            return _theme
    raise RuntimeError(
        "the shared board theme (PyAutoBrain/board/_theme.py) is not in reach "
        "— check PyAutoBrain out beside this repo or set PYAUTO_BRAIN")


# The five boards, in routing order. (name, repo, what the board is,
# the door command a 📋 chip copies.) Brain publishes the same badge.json
# headline contract as Heart/Hands/Memory (brain_board.yml).
BOARDS = (
    ("Brain", "PyAutoBrain", "operations — the morning door: what needs you", "/board"),
    ("Mind", "PyAutoMind", "tasks — pick what to work on", "/start_dev <prompt-path>"),
    ("Heart", "PyAutoHeart", "health — is the organism ok?", "/health"),
    ("Hands", "PyAutoHands", "releases — what shipped", "/release"),
    ("Memory", "PyAutoMemory", "knowledge — papers and wikis", "/memory <topic>"),
)

MIND_COUNT_RE = re.compile(r"^\|\s*\[([A-Za-z ]+)\]\([^)]*\)[^|]*\|\s*(\d+)\s*\|",
                           re.MULTILINE)


def _owner() -> str:
    out = subprocess.run(["git", "-C", str(HOME), "remote", "get-url", "origin"],
                         capture_output=True, text=True).stdout.strip()
    m = re.search(r"[:/]([^/:]+)/[^/]+?(?:\.git)?/?$", out)
    return m.group(1) if m else ""


def _get(url: str) -> str:
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def collect(owner: str | None = None) -> dict:
    owner = owner if owner is not None else _owner()
    low = owner.lower()
    snapshot: dict = {
        "generated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "owner": owner,
        "boards": [],
    }
    for name, repo, role, door in BOARDS:
        row = {"name": name, "repo": repo, "role": role, "door": door,
               "url": f"https://{low}.github.io/{repo}/" if low else "",
               "headline": None, "color": None}
        try:
            if name == "Mind":
                md = _get(f"https://raw.githubusercontent.com/{owner}/{repo}/main/dashboard.md")
                counts = {label: int(n) for label, n in MIND_COUNT_RE.findall(md)}
                if counts:
                    row["headline"] = " · ".join(
                        f"{v} {k.lower()}" for k, v in counts.items())
                    row["counts"] = counts
            else:
                badge = json.loads(_get(row["url"] + "badge.json"))
                row["headline"] = str(badge.get("message") or "")
                row["color"] = str(badge.get("color") or "")
        except (urllib.error.URLError, TimeoutError, ValueError, OSError):
            pass
        snapshot["boards"].append(row)
    return snapshot


# --- pure helpers ---------------------------------------------------------------
def _heart(snapshot: dict) -> dict | None:
    for b in snapshot.get("boards") or []:
        if b["name"] == "Heart":
            return b
    return None


def heart_word(snapshot: dict) -> str:
    h = _heart(snapshot)
    if not h or not h.get("headline"):
        return "UNKNOWN"
    return h["headline"].split()[0].upper().strip("·")


def route_hint(snapshot: dict) -> str:
    """Where to work next, keyed off the Heart's verdict."""
    word = heart_word(snapshot)
    if word in ("RED", "YELLOW"):
        return ("The Heart is " + word +
                " — start at the PyAutoHeart Dashboard and fix what's blocking.")
    if word == "STALE":
        return ("Evidence gaps, nothing known-bad — re-run checks via /health, "
                "then pick a task on the PyAutoMind Dashboard.")
    if word == "GREEN":
        return "All clear — pick a task on the PyAutoMind Dashboard."
    return "Heart verdict unavailable — check the PyAutoHeart Dashboard first."


def _render_md(snapshot: dict) -> str:
    lines = ["# PyAutoScientist Dashboard", "",
             f"_{route_hint(snapshot)}_", "",
             "| Dashboard | Says | |", "|---|---|---|"]
    for b in snapshot.get("boards") or []:
        head = b.get("headline") or "unavailable"
        link = f"[{b['name']}]({b['url']})" if b.get("url") else b["name"]
        lines.append(f"| {link} | {head} | {b['role']} |")
    return "\n".join(lines)


def _render_md_brief(snapshot: dict) -> str:
    bits = []
    for b in snapshot.get("boards") or []:
        head = b.get("headline") or "unavailable"
        bits.append(f"[{b['name']}]({b['url']}) {head}" if b.get("url")
                    else f"{b['name']} {head}")
    return " · ".join(bits)


def _copy_btn(payload: str, label: str = "copy") -> str:
    """A one-tap payload chip. The behaviour is the family's shared script
    (``_theme.JS``): a delegated click handler reading ``data-cmd``."""
    return (f"<button class='copy' type='button' "
            f"title='{_html.escape(label, quote=True)}' "
            f"data-cmd=\"{_html.escape(payload, quote=True)}\">\U0001f4cb</button>")


_HEART_CLS = {"RED": "fail", "YELLOW": "warn", "STALE": "info", "GREEN": "ok"}

# The Heart's word in the theme's verdict vocabulary. Unknown stays neutral:
# "we could not read the Heart" is not a verdict, and colouring it as one
# would say something the page does not know.
_VERDICT_CLS = {"RED": "bad", "YELLOW": "warn", "STALE": "warn", "GREEN": "ok"}

# What the shared sheet has no opinion on: this board is a router, so its one
# page-specific shape is the organ row — a name, that board's own headline,
# and what it is for. Written against the theme's variables, so it follows the
# accent rather than setting a second palette.
_EXTRA_CSS = """
.organ{display:flex;gap:.6rem;align-items:flex-start;padding:.55rem .35rem;
 margin:0 -.35rem;border-bottom:1px solid var(--line);border-radius:7px}
.organ:hover{background:var(--tint)}
.organ p{margin:0;flex:1}
.organ .name{display:inline-block;min-width:4.6rem;font-weight:700}
.organ .head{font-weight:600}
.organ .role{display:block;color:var(--muted);font-size:.88em}
footer{margin-top:2.4rem;padding-top:1rem;border-top:1px solid var(--line);
 color:var(--muted);font-size:.82em}
"""


_LEDE = ("One row per organ, each speaking in its own words. This page "
         "routes; the work happens on the board you open. Tap \U0001f4cb to "
         "put that board's door command on your clipboard for a Claude Code "
         "chat.")


def _render_html(snapshot: dict) -> str:
    t = theme()
    word = heart_word(snapshot)
    rows = []
    for b in snapshot.get("boards") or []:
        head = _html.escape(b.get("headline") or "unavailable")
        link = (f"<a href=\"{_html.escape(b['url'], quote=True)}\">"
                f"{_html.escape(b['name'])}</a>" if b.get("url")
                else _html.escape(b["name"]))
        rows.append(
            f"<div class='organ'>"
            f"{_copy_btn(b['door'], 'copy the door command for a Claude Code chat')}"
            f"<p><span class='name'>{link}</span> "
            f"<span class='head'>{head}</span>"
            f"<span class='role'>{_html.escape(b['role'])}</span></p></div>")
    hero = t.hero(BOARD_KEY, "Dashboard", _LEDE)
    # The way back from the Pages board to the repository front door; the
    # owner comes from the snapshot (the git remote), so the segment drops
    # out when the origin is unknown.
    gh_owner = snapshot.get("owner")
    github_link = (f' · <a href="https://github.com/{gh_owner}/PyAutoScientist'
                   '/blob/main/README.md">GitHub Page</a>' if gh_owner else "")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PyAutoScientist Dashboard</title>
<style>{t.css(BOARD_KEY)}{_EXTRA_CSS}</style>
</head>
<body>
{hero}
<p class="verdict {_VERDICT_CLS.get(word, '')}"><b>{_html.escape(route_hint(snapshot))}</b></p>
{''.join(rows)}
<p class="muted mdsrc"><a href="dashboard.md">markdown version</a>{github_link}</p>
<footer>Rendered by <code>scripts/organism_board.py</code> from the boards'
own published headlines · generated {_html.escape(str(snapshot.get('generated') or '?'))}.</footer>
<script>{t.JS}</script>
</body></html>
"""


def badge_endpoint(snapshot: dict) -> dict:
    word = heart_word(snapshot)
    h = _heart(snapshot)
    color = (h or {}).get("color") or "lightgrey"
    mind = next((b for b in snapshot.get("boards") or [] if b["name"] == "Mind"), {})
    backlog = (mind.get("counts") or {}).get("Backlog")
    msg = word if backlog is None else f"{word} · {backlog} tasks queued"
    return {"schemaVersion": 1, "label": "organism", "message": msg, "color": color}


def render(snapshot: dict, fmt: str = "md") -> str:
    if fmt == "md":
        return _render_md(snapshot)
    if fmt == "md-brief":
        return _render_md_brief(snapshot)
    if fmt == "html":
        return _render_html(snapshot)
    if fmt == "badge":
        return json.dumps(badge_endpoint(snapshot))
    if fmt == "json":
        return json.dumps(snapshot, indent=2, sort_keys=True)
    raise ValueError(f"unknown fmt: {fmt!r}")


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(prog="organism_board", description=__doc__)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--md", action="store_true")
    g.add_argument("--md-brief", action="store_true")
    g.add_argument("--html", action="store_true")
    g.add_argument("--badge", action="store_true")
    g.add_argument("--json", action="store_true")
    ns = ap.parse_args(argv)
    snap = collect()
    fmt = "md"
    for name, label in (("md", "md"), ("md_brief", "md-brief"),
                        ("html", "html"), ("badge", "badge"), ("json", "json")):
        if getattr(ns, name):
            fmt = label
            break
    print(render(snap, fmt))
    return 0


if __name__ == "__main__":
    sys.exit(main())
