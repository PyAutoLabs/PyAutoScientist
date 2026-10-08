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
CHECKIN_PROMPT = (
    "Use this chat as an ongoing entry point to PyAutoLabs. Read PyAutoScientist/AGENTS.md "
    "and use the board skill to inspect relevant operational evidence. Load other organs and "
    "project context as the request requires.\n\n"
    "When I give no particular direction, provide a concise overview of the organism’s "
    "current position: significant progress, blockers, decisions needing my attention and "
    "useful next steps. Check evidence freshness and coverage, linking to the owning boards "
    "rather than reproducing every queue.\n\n"
    "When I supply a question, idea or task, make that the main focus. Help me clarify what I "
    "want to achieve and identify the appropriate organ, project and workflow. Explain the "
    "routing briefly and continue through it in this conversation where possible. Do not "
    "repeat the organism-wide review on every follow-up.\n\n"
    "Help me work through requests that span several organs. Identify dependencies, establish "
    "an appropriate order and keep decisions connected across the work. Respect each organ’s "
    "ownership of its records, judgments and execution procedures.\n\n"
    "When I ask about the organism itself, help me examine its architecture, workflows, "
    "missing capabilities or unnecessary complexity. Ground recommendations in the existing "
    "system and discuss concrete options and tradeoffs before proposing changes.\n\n"
    "Carry clearly authorized work through the appropriate skills, retaining decisions and "
    "approvals already given in this conversation. Ask when a missing decision materially "
    "changes the next step. Preserve applicable development, compute, community-reply, merge "
    "and release approval requirements.\n\n"
    "Keep authoritative task state, scientific records and execution in their owning "
    "repositories. After taking action, report the outcome, where any changes were recorded "
    "and what remains unresolved. Stop at the session deliverable without scheduling "
    "background follow-up."
)

BOARD_KEY = "organism"  # this board's entry in the Brain's palette table


def _workspace_root() -> Path:
    """Find the workspace containing the sibling PyAuto checkouts.

    The org's own directory name is an instance fact, so it is never written
    here — a workspace that does not follow the default sets `$PYAUTO_ROOT`
    (the same variable the dev-flow doors read).
    """
    if os.environ.get("PYAUTO_ROOT"):
        return Path(os.environ["PYAUTO_ROOT"])
    for parent in (HOME, *HOME.parents):
        if (parent / ".pyauto-root").is_file():
            return parent
    return Path.home() / "Code"


def theme():
    """The shared theme module, or a RuntimeError naming the fix.

    Only the html path needs it; ``--md``/``--badge``/``--json`` never call
    here, so the digest keeps working with no PyAutoBrain in reach.
    """
    for cand in (os.environ.get("PYAUTO_BRAIN"), HOME / "PyAutoBrain",
                 HOME.parent / "PyAutoBrain",
                 _workspace_root() / "organs" / "PyAutoBrain",
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
    ("Brain", "PyAutoBrain", "operations — the morning door: what needs you", "Use the board skill."),
    ("Mind", "PyAutoMind", "tasks — pick what to work on", "Use the start-dev skill. <prompt-path>"),
    ("Heart", "PyAutoHeart", "health — is the organism ok?", "Use the health skill."),
    ("Hands", "PyAutoHands", "releases — what shipped", "Use the release skill."),
    ("Memory", "PyAutoMemory", "knowledge — papers and wikis", "Use the memory skill. <topic>"),
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
        return ("Evidence gaps, nothing known-bad — re-run checks via Use the health skill., "
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

# The same word in the shared section-status vocabulary (Brain
# ``section_layout``). Anything the Heart did not say — an unreadable badge, an
# unfamiliar word — is "unknown", never green.
_SECTION_STATUS = {"RED": "red", "YELLOW": "yellow", "STALE": "stale", "GREEN": "green"}

SECTION_ID = "dashboards"


def _row_id(name: str) -> str:
    """The stable fragment of one organ row (``#board-heart``)."""
    return "board-" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def section_summaries(snapshot: dict) -> dict:
    """Owner-computed header facts for the collapsed "Organ dashboards" section.

    The count is how many boards actually answered out of how many are listed,
    so a missing headline reads as a gap ("4 of 5 reporting"), not as a quiet
    zero. The status is the Heart's own word, labelled as such; it routes, it
    does not restate release readiness.
    """
    rows = snapshot.get("boards") or []
    word = heart_word(snapshot)
    info: dict = {
        "status": _SECTION_STATUS.get(word, "unknown"),
        "label": "Heart " + (word if word in _SECTION_STATUS else "unknown"),
    }
    if rows:
        live = sum(1 for b in rows if b.get("headline"))
        info["count"] = f"{live} of {len(rows)} reporting"
    return {SECTION_ID: info}

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


def _render_html(snapshot: dict) -> str:
    t = theme()
    work_links = [
        {"label": b["name"] + " repository",
         "href": f"https://github.com/{snapshot['owner']}/{b['repo']}"}
        for b in snapshot.get("boards") or []
        if snapshot.get("owner") and b.get("repo")
    ]
    panel = t.orchestration_panel("scientist", "", "", CHECKIN_PROMPT,
                                  organ="scientist", work_links=work_links,
                                  refreshed_at=(snapshot.get("generated")
                                                if snapshot.get("boards") and all(row.get("headline") is not None
                                                                                for row in snapshot["boards"])
                                                else None),
                                  refresh_url=(f"https://github.com/{snapshot['owner']}/PyAutoScientist/actions/workflows/organism_board.yml"
                                               if snapshot.get("owner") else None))
    word = heart_word(snapshot)
    rows = []
    for b in snapshot.get("boards") or []:
        head = _html.escape(b.get("headline") or "unavailable")
        link = (f"<a href=\"{_html.escape(b['url'], quote=True)}\">"
                f"{_html.escape(b['name'])}</a>" if b.get("url")
                else _html.escape(b["name"]))
        rows.append(
            f"<div class='organ' id='{_row_id(b['name'])}'>"
            f"{_copy_btn(b['door'], 'copy the door command for an AI assistant chat')}"
            f"<p><span class='name'>{link}</span> "
            f"<span class='head'>{head}</span>"
            f"<span class='role'>{_html.escape(b['role'])}</span></p></div>")
    hero = t.hero(BOARD_KEY, "Dashboard", navigation=[
        {"href": b["url"], "label": b["name"]}
        for b in snapshot.get("boards") or [] if b.get("url")
    ])
    # Brain's shared layout puts the slogan panel above the navigation cards
    # and folds the titled section into a collapsed native disclosure; the
    # verdict banner stays outside it so the routing answer is always visible.
    return t.section_layout(f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PyAutoScientist Dashboard</title>
<style>{t.css(BOARD_KEY)}{_EXTRA_CSS}</style>
</head>
<body>
{hero}
{panel}
<p class="verdict {_VERDICT_CLS.get(word, '')}"><b>{_html.escape(route_hint(snapshot))}</b></p>
<section class="dashboards">
<h2 id="{SECTION_ID}">Organ dashboards</h2>
{''.join(rows)}
</section>
<p class="muted mdsrc"><a href="dashboard.md">markdown version</a></p>
<footer>Rendered by <code>scripts/organism_board.py</code> from the boards'
own published headlines · generated {_html.escape(str(snapshot.get('generated') or '?'))}.</footer>
<script>{t.JS}</script>
</body></html>
""", section_summaries(snapshot))


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
