"""scripts/organism_board.py — the PyAutoScientist organism board.

The umbrella ROUTER over the organism's live dashboards: one row per organ
board — Mind (tasks), Heart (health), Hands (releases), Memory (knowledge) —
each carrying that board's own live headline and link, topped by a
"where to work next" banner keyed off the Heart's verdict (Heart red/yellow →
start at the health board; green → pick a task on the Mind board). A glance
here tells you WHICH board to open; the work happens there.

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
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

HOME = Path(__file__).resolve().parents[1]

# The four boards, in routing order. (name, repo, what the board is,
# the door command a 📋 chip copies.)
BOARDS = (
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
                " — start at the health board and fix what's blocking.")
    if word == "STALE":
        return ("Evidence gaps, nothing known-bad — re-run checks via /health, "
                "then pick a task on the Mind board.")
    if word == "GREEN":
        return "All clear — pick a task on the Mind board."
    return "Heart verdict unavailable — check the health board first."


def _render_md(snapshot: dict) -> str:
    lines = ["# PyAutoScientist organism board", "",
             f"_{route_hint(snapshot)}_", "",
             "| Board | Says | |", "|---|---|---|"]
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
    return (f"<button class='copy' type='button' "
            f"title='{_html.escape(label, quote=True)}' "
            f"data-copy=\"{_html.escape(payload, quote=True)}\" "
            f"onclick='cp(this)'>📋</button>")


_HEART_CLS = {"RED": "fail", "YELLOW": "warn", "STALE": "info", "GREEN": "ok"}


def _render_html(snapshot: dict) -> str:
    word = heart_word(snapshot)
    cls = _HEART_CLS.get(word, "unobs")
    rows = []
    for b in snapshot.get("boards") or []:
        head = _html.escape(b.get("headline") or "unavailable")
        link = (f"<a href=\"{_html.escape(b['url'], quote=True)}\">"
                f"{_html.escape(b['name'])}</a>" if b.get("url")
                else _html.escape(b["name"]))
        rows.append(
            f"<tr><td class='name'>{link}</td>"
            f"<td><span class='head'>{head}</span> "
            f"<span class='meta'>{_html.escape(b['role'])}</span> "
            f"{_copy_btn(b['door'], 'copy the door command for a Claude Code chat')}"
            f"</td></tr>")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PyAutoScientist — {word}</title>
<style>
  :root {{ color-scheme: light dark; }}
  * {{ box-sizing: border-box; }}
  body {{ font: 15px/1.5 -apple-system, Segoe UI, Roboto, sans-serif;
         margin: 0; padding: 2rem 1rem; background: #0d1117; color: #c9d1d9; }}
  .wrap {{ max-width: 760px; margin: 0 auto; }}
  h1 {{ font-size: 1.3rem; margin: 0 0 .5rem; }}
  .banner {{ padding: .6rem .9rem; border-radius: 8px; font-weight: 600;
            margin: 0 0 1.25rem; }}
  .banner.ok {{ background: #12261c; color: #3fb950; }}
  .banner.warn {{ background: #2a2110; color: #d29922; }}
  .banner.fail {{ background: #2d1517; color: #f85149; }}
  .banner.info {{ background: #10202f; color: #58a6ff; }}
  .banner.unobs {{ background: #1b1f24; color: #8b949e; }}
  table {{ width: 100%; border-collapse: collapse; }}
  td {{ padding: .6rem .5rem; border-top: 1px solid #21262d; vertical-align: top; }}
  td.name {{ font-weight: 700; white-space: nowrap; width: 6.5rem; }}
  .head {{ font-weight: 600; }}
  .meta {{ color: #8b949e; font-size: .9rem; }}
  a {{ color: #58a6ff; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  button.copy {{ background: #21262d; border: 1px solid #30363d; border-radius: 6px;
                color: #c9d1d9; cursor: pointer; padding: .05rem .45rem;
                margin-left: .35rem; font-size: .85rem; line-height: 1.4; }}
  button.copy:hover {{ background: #30363d; }}
  footer {{ margin-top: 2rem; color: #8b949e; font-size: .8rem; }}
</style>
<script>
function cp(b){{var t=b.getAttribute('data-copy');
 if(navigator.clipboard&&navigator.clipboard.writeText){{
   navigator.clipboard.writeText(t).then(function(){{ok(b)}},function(){{fb(t)}});
 }}else{{fb(t)}}}}
function ok(b){{b.textContent='✓';setTimeout(function(){{b.textContent='📋'}},1200)}}
function fb(t){{window.prompt('Copy this:',t)}}
</script></head>
<body><div class="wrap">
  <h1>PyAutoScientist organism board</h1>
  <p class="banner {cls}">{_html.escape(route_hint(snapshot))}</p>
  <table>{''.join(rows)}</table>
  <p class="meta">Each row is that organ's own board speaking in its own
  words — open it to work there. 📋 copies the board's door command for a
  Claude Code chat.</p>
  <footer>Rendered by <code>scripts/organism_board.py</code> from the boards'
  own published headlines · generated {_html.escape(str(snapshot.get('generated') or '?'))}.</footer>
</div></body></html>
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
