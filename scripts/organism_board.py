"""scripts/organism_board.py — the PyAutoScientist Dashboard.

The Scientist home presents concise disclosures over owner-published state.json
feeds. Brain supplies the shared theme, organ registry and feed validator.
The browser refreshes feeds without resetting open cards or prompt controls;
the publication snapshot remains a labelled fallback without JavaScript.
Scientist coordinates and reports; the organs retain their records and work.

**Identity** derives from ``git remote`` (an adopting fork gets its own URLs
for free). Rendered fresh by ``.github/workflows/organism_board.yml`` into
GitHub Pages + ``badge.json`` + the README strip between the
``scientist:begin/end`` markers — nothing is committed except the strip.

Usage:
    python scripts/organism_board.py [--md | --md-brief | --html | --badge | --json]
Tests: ``python -m pytest tests/`` (run ad hoc; this repo has no CI gate).
"""

from __future__ import annotations

import concurrent.futures
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
    "and PyAutoScientist/REPORTING.md. Use the board skill to inspect relevant operational evidence. Load other organs and "
    "project context as the request requires.\n\n"
    "When I give no particular direction, provide a concise overview of the organism’s "
    "work across all organs over the last 24 hours, plus its current position: significant progress, blockers, decisions needing my attention and "
    "useful next steps. Check evidence freshness and coverage, linking to the owning boards "
    "rather than reproducing every queue.\n\n"
    "For a summary over a given time period, use that period instead of the last 24 hours. "
    "State the start, end and timezone. Check dated records in every organ, distinguish "
    "completed outcomes from work still in progress and decisions awaiting me, and link "
    "the evidence. Deduplicate work spanning organs. A dashboard refresh is not a completed "
    "event; current snapshots alone cannot establish a historical summary. Report coverage "
    "gaps separately from verified inactivity, and separate events within the period from "
    "older blockers that remain open. Keep the summary high level.\n\n"
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

    The collector uses its canonical board registry and matching state validator;
    the HTML renderer also uses its branding and orchestration controls.
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


def boards(owner: str) -> list[dict]:
    """Canonical membership/order from Brain; Scientist never summarizes itself."""
    t = theme()
    links = t.board_links(f"https://{owner.lower()}.github.io", current=BOARD_KEY)
    if not links:
        raise RuntimeError("Brain board registry unavailable")
    return [{"name": t.organ(key)["organ"], "key": key,
             "repo": url.rstrip("/").rsplit("/", 1)[-1], "url": url,
             "role": t.organ(key)["function"]}
            for key, url in links.items()]


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
    if not owner:
        raise ValueError("Cannot resolve the repository owner")
    rows = boards(owner)
    # theme() resolves the matching Brain checkout and its validator.
    from _state import validate_state

    def read(row):
        row = dict(row, headline=None, color=None, feed=None, error=None)
        try:
            feed = json.loads(_get(row["url"] + "state.json"))
            errors = validate_state(feed)
            if errors or feed["organ"] != row["key"] or feed["repo"] != row["repo"]:
                raise ValueError("Invalid organ feed")
            row.update(feed=feed, headline=feed["headline"], color=feed["status"])
        except (urllib.error.URLError, TimeoutError, ValueError, OSError):
            row["error"] = "Evidence unavailable"
        return row

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        collected = list(executor.map(read, rows))
    return {"generated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "owner": owner, "boards": collected}


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
    if h.get("feed"):
        return h["feed"]["status"].upper()
    return h["headline"].split()[0].upper().strip("·")


def route_hint(snapshot: dict) -> str:
    """Where to work next, keyed off the Heart's verdict."""
    word = heart_word(snapshot)
    if word in ("RED", "YELLOW"):
        return ("The Heart is " + word +
                " — start at the PyAutoHeart Dashboard and fix what's blocking.")
    if word == "STALE":
        return ("Heart evidence is stale — re-run checks via Use the health skill., "
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


def _row_id(name: str) -> str:
    """The stable fragment of one organ row (``#board-heart``)."""
    return "board-" + re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


_EXTRA_CSS = """
.organ-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.75rem;align-items:start;margin-top:1.25rem}
.organ-card{min-width:0;border:1px solid var(--line);border-radius:12px;background:var(--bg)}
.organ-card[open]{grid-column:1/-1}
.organ-card>summary{cursor:pointer;min-height:64px;padding:1rem;display:flex;gap:.65rem;align-items:center;font-weight:700;list-style:none}
.organ-card>summary::-webkit-details-marker{display:none}
.organ-card>summary::after{content:'⌄';margin-left:auto}
.organ-card[open]>summary::after{content:'⌃'}
.organ-icon svg{width:30px;height:30px;display:block}
.organ-status{font-size:.8rem;font-weight:500;color:var(--muted)}
.organ-status[data-status=red]{color:var(--bad)}
.organ-status[data-status=green]{color:var(--ok)}
.organ-content{padding:0 1rem 1rem}
.organ-content dl{margin:0;display:grid;gap:.6rem}
.organ-content .summary-row{display:grid;grid-template-columns:9rem 1fr;gap:.75rem}
.organ-content dt{font-size:.88rem;color:var(--muted)}
.organ-content dd{margin:0;overflow-wrap:anywhere}
.organ-content a{display:inline-block;min-height:44px}
.organ-foot{display:flex;justify-content:space-between;gap:1rem;align-items:center;margin:.8rem 0 0;font-size:.82rem;color:var(--muted);flex-wrap:wrap}
.organ-foot a{min-height:44px;display:inline-flex;align-items:center}
.organ-grid :focus-visible{outline:3px solid var(--accent);outline-offset:3px}
@media(max-width:64rem){.organ-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:40rem){.organ-grid{grid-template-columns:1fr}.organ-content .summary-row{grid-template-columns:1fr;gap:.15rem}}
"""


def _render_html(snapshot: dict) -> str:
    t = theme()
    owner = snapshot.get("owner")
    panel = t.orchestration_panel(
        "scientist", "", "", CHECKIN_PROMPT, organ="scientist",
        work_links=([{"label": "Scientist repository", "href": f"https://github.com/{owner}/PyAutoScientist"}] if owner else []),
        refreshed_at=(snapshot.get("generated") if snapshot.get("boards") and
                      all(row.get("headline") is not None for row in snapshot["boards"]) else None),
        refresh_url=(f"https://github.com/{owner}/PyAutoScientist/actions/workflows/organism_board.yml" if owner else None))
    rows = []
    for row in snapshot.get("boards") or []:
        key = row.get("key", row["name"].lower())
        name = _html.escape(row["name"])
        ident = _row_id(row["name"])
        # Server fallback is explicitly a publication snapshot, not a live check.
        head = _html.escape(row.get("headline") or "Evidence unavailable")
        url = _html.escape(row["url"], quote=True)
        rows.append(f"""<details class="organ-card" id="{ident}" data-organ="{key}">
<summary><span class="organ-icon" aria-hidden="true">{t.mark(key)}</span><span>{name}</span><span class="organ-status">Snapshot</span></summary>
<div class="organ-content"><dl><div class="summary-row"><dt>Published status</dt><dd>{head}</dd></div></dl>
<div class="organ-foot"><span data-freshness>Published {_html.escape(str(snapshot.get('generated') or 'unknown'))}</span><a href="{url}">Open {name} →</a></div></div></details>""")
    data = json.dumps(snapshot, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    script = (HOME / "scripts" / "overview.js").read_text(encoding="utf-8")
    # Native per-organ disclosures keep the overview visible; do not put the
    # whole grid inside section_layout's extra collapsed H2 group.
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>PyAutoScientist Dashboard</title><style>{t.css(BOARD_KEY)}{_EXTRA_CSS}</style></head>
<body>{t.hero(BOARD_KEY, "Dashboard")}{panel}
<div id="dashboards" class="organ-grid" aria-label="Organ summaries">{''.join(rows)}</div>
<noscript><p>Publication snapshot. Open an organ for its latest evidence.</p></noscript>
<script type="application/json" id="scientist-snapshot">{data}</script>
<script>{t.JS}</script><script>{script}</script></body></html>"""


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
