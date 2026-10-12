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
COMMON_CHECKIN_PROMPT = (
    "When I give no particular direction, provide a concise overview of the organism’s "
    "work across connected organs over the last 24 hours, plus its current position: significant progress, blockers, decisions needing my attention and "
    "useful next steps. Check evidence freshness and coverage, linking to the owning boards "
    "rather than reproducing every queue.\n\n"
    "For a summary over a given time period, use that period instead of the last 24 hours. "
    "State the start, end and timezone. Check dated records in every connected organ, distinguish "
    "completed outcomes from work still in progress and decisions awaiting me, and link "
    "the evidence. Deduplicate work spanning organs. A dashboard refresh is not a completed "
    "event; current snapshots alone cannot establish a historical summary. Report coverage "
    "gaps separately from verified inactivity, and separate events within the period from "
    "older blockers that remain open. Keep the summary high level. "
    "Determine overnight or recent activity on demand from those owner records and, "
    "when needed, workflow runs covering the requested interval. Do not rely on a "
    "fixed latest-run digest from Brain or create scheduled collection for this review. "
    "Account for pagination and unavailable history; distinguish failed, blocked, "
    "in-progress and absent runs without treating missing access as inactivity.\n\n"
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

CHECKIN_PROMPT = (
    "Use this chat as an ongoing entry point to PyAutoLabs. Read PyAutoScientist/AGENTS.md "
    "and PyAutoScientist/REPORTING.md. Use the board skill to inspect relevant operational evidence. Load other organs and "
    "project context as the request requires.\n\n"
    + COMMON_CHECKIN_PROMPT
)


def instance_prompt(instance):
    return (f"Use this chat as an ongoing entry point to {instance['name']}. "
            "Read this Scientist checkout’s AGENTS.md, STARTER.md and REPORTING.md, "
            "then its explicit instance profile and project relationships. "
            "Consult only connected, unpaused organs and relevant project-owned sources. "
            "Do not assume optional organs, an agent harness or remote access are installed. "
            "Help connect existing projects using their canonical repository identities; "
            "ask about purpose, visibility and needed capabilities before changing setup. "
            "Keep missing evidence distinct from unconfigured organs.\n\n"
            + COMMON_CHECKIN_PROMPT)


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


def collect(owner: str | None = None, instance: dict | None = None) -> dict:
    owner = owner if owner is not None else (_owner() if instance is None else None)
    if instance is None and not owner:
        raise ValueError("Cannot resolve the repository owner")
    rows = boards(owner) if instance is None else instance["boards"]
    # theme() resolves the matching Brain checkout and its validator.
    theme()
    from _state import validate_state

    def read(row):
        row = dict(row, headline=None, color=None, feed=None, error=None)
        if row.get("paused"):
            row.update(headline="Observation paused", color="grey")
            return row
        try:
            feed = json.loads(_get(row["url"] + "state.json"))
            errors = validate_state(feed)
            if (errors or feed["organ"] != row["key"] or feed["repo"] != row["repo"]
                    or (instance is not None and feed["pages_url"].rstrip("/") != row["url"].rstrip("/"))):
                raise ValueError("Invalid organ feed")
            row.update(feed=feed, headline=feed["headline"], color=feed["status"])
        except (urllib.error.URLError, TimeoutError, ValueError, OSError):
            row["error"] = "Evidence unavailable"
        return row

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        collected = list(executor.map(read, rows))
    snapshot = {"generated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "owner": owner, "boards": collected}
    if instance is not None:
        snapshot["instance"] = {k: v for k, v in instance.items() if k != "boards"}
    return snapshot


# --- pure helpers ---------------------------------------------------------------
def _heart(snapshot: dict) -> dict | None:
    for b in snapshot.get("boards") or []:
        if b["name"] == "Heart":
            return b
    return None


def heart_word(snapshot: dict) -> str:
    h = _heart(snapshot)
    if not h or h.get("paused") or not h.get("headline"):
        return "UNKNOWN"
    if h.get("feed"):
        return h["feed"]["status"].upper()
    return h["headline"].split()[0].upper().strip("·")


def route_hint(snapshot: dict) -> str:
    """Where to work next, keyed off the Heart's verdict."""
    if "instance" in snapshot:
        if not snapshot.get("boards"):
            return "No organs connected. Connect a project, then add only the organs it needs."
        return "Inspect connected organ evidence before choosing the next action; missing evidence is not a passing result."
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
    from project_resources import markdown_text
    name = snapshot.get("instance", {}).get("name", "PyAutoScientist")
    lines = [f"# {markdown_text(name)} Dashboard", "",
             f"_{route_hint(snapshot)}_", "",
             "| Dashboard | Says | |", "|---|---|---|"]
    for b in snapshot.get("boards") or []:
        head = b.get("headline") or "unavailable"
        link = f"[{b['name']}]({b['url']})" if b.get("url") else b["name"]
        lines.append(f"| {link} | {head} | {b['role']} |")
    for pending in snapshot.get("instance", {}).get("setup", []):
        lines.append(f"| {pending['name']} | Setup incomplete; not connected | {pending['role']} |")
    if "project_resources" in snapshot:
        from project_resources import render_markdown
        lines.extend(["", render_markdown(snapshot["project_resources"])])
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
.project-card ul{list-style:none;padding:0;margin:0}
.project-card li{margin:0 0 .35rem}
.available-resource{border:1px dashed var(--line);border-radius:6px}
.available-resource>summary{color:var(--muted);cursor:pointer;padding:.65rem;min-height:44px;box-sizing:border-box}
.availability-label{font-size:.8rem;margin-left:.4rem}
.available-resource-body{padding:0 .75rem .75rem 1.25rem}
.available-resource-body label{display:block;margin-bottom:.35rem}
.available-resource-body textarea{font:inherit;width:100%;box-sizing:border-box;resize:vertical;background:var(--bg);color:var(--fg);border:1px solid var(--line);padding:.65rem}
.organ-catalogue textarea,.organ-content textarea{width:100%;box-sizing:border-box;min-height:7rem;font:inherit}
.organ-catalogue{margin-block:1rem}
.organ-catalogue details>summary{color:var(--muted,#666)}
.organ-grid :focus-visible{outline:3px solid var(--accent);outline-offset:3px}
@media(max-width:64rem){.organ-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:40rem){.organ-grid{grid-template-columns:1fr}.organ-content .summary-row{grid-template-columns:1fr;gap:.15rem}}
"""


def _render_html(snapshot: dict) -> str:
    t = theme()
    owner = snapshot.get("owner")
    instance = snapshot.get("instance")
    name = instance["name"] if instance is not None else "PyAutoScientist"
    source = instance["source_url"] if instance is not None else (f"https://github.com/{owner}/PyAutoScientist" if owner else None)
    prompt = CHECKIN_PROMPT if instance is None else instance_prompt(instance)
    panel = t.orchestration_panel(
        "scientist", "", "", prompt, organ="scientist",
        work_links=([{"label": (name if instance is not None else "Scientist") + " repository", "href": source}] if source else []),
        refreshed_at=(snapshot.get("generated") if snapshot.get("boards") and
                      all(row.get("headline") is not None and not row.get("paused") for row in snapshot["boards"]) else None),
        refresh_url=(source + "/actions/workflows/organism_board.yml" if source and instance is None else None))
    from project_resources import render_html as render_projects
    projects_html = render_projects(snapshot["project_resources"]) if "project_resources" in snapshot else ""
    links = ({row["key"]: row["url"] for row in snapshot["boards"]} if instance is not None
             else t.board_links(f"https://{owner.lower()}.github.io", BOARD_KEY) if owner else {})
    footer = t.boards_footer(links, BOARD_KEY)
    rows = []
    for row in snapshot.get("boards") or []:
        key = row.get("key", row["name"].lower())
        organ_name = _html.escape(row["name"])
        ident = _row_id(row["name"])
        # Server fallback is explicitly a publication snapshot, not a live check.
        head = _html.escape(row.get("headline") or "Evidence unavailable")
        url = _html.escape(row["url"], quote=True)
        lifecycle = "Paused" if row.get("paused") else "Connected" if instance is not None else "Snapshot"
        note = ("Scientist observation paused; owner jobs are unaffected." if row.get("paused")
                else "Published " + str(snapshot.get("generated") or "unknown"))
        rows.append(f"""<details class="organ-card" id="{ident}" data-organ="{key}">
<summary><span class="organ-icon" aria-hidden="true">{t.mark(key)}</span><span>{organ_name}</span><span class="organ-status">{lifecycle}</span></summary>
<div class="organ-content"><dl><div class="summary-row"><dt>Published status</dt><dd>{head}</dd></div></dl>
<div class="organ-foot"><span data-freshness>{_html.escape(note)}</span><a href="{url}">Open {organ_name} →</a></div></div></details>""")
    catalogue = ""
    if instance is not None:
        for pending in instance.get("setup", []):
            key = pending["key"]
            prompt_text = (f"Resume setup for {pending['name']} in my existing Mind task. "
                           "Read my profile and canonical map first. Validate the owner setup and published feed, "
                           "then preview connect_organ.py before applying. Preserve existing records.")
            rows.append(f'<details class="organ-card" id="setup-{key}"><summary>'
                        f'{_html.escape(pending["name"])} · Setup incomplete</summary>'
                        f'<div class="organ-content"><p>Not connected. No feed requested.</p>'
                        f'<p>{_html.escape(pending["role"])}</p><textarea readonly aria-label="Resume {key} setup">'
                        f'{_html.escape(prompt_text)}</textarea></div></details>')
        entries = []
        for available in instance.get("available", []):
            key = available["key"]
            prompt_text = (f"Help me add {available['name']} ({available['role']}) to this Scientist. "
                           "Read my existing profile, canonical map and Mind task. Confirm the purpose, repository "
                           "identity and public board location; preview organ_lifecycle.py setup before applying. "
                           "Keep it setup incomplete until connect_organ.py validates its published feed.")
            entries.append(f'<details><summary>{_html.escape(available["name"])} · Available to add</summary>'
                           f'<p>{_html.escape(available["role"])}</p><textarea readonly aria-label="Add {key}">'
                           f'{_html.escape(prompt_text)}</textarea></details>')
        if entries:
            catalogue = '<details class="organ-catalogue"><summary>Available organs</summary>' + ''.join(entries) + '</details>'
    data = json.dumps(snapshot, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    script = (HOME / "scripts" / "overview.js").read_text(encoding="utf-8")
    banner = (t.hero(BOARD_KEY, "Dashboard", display_name=name) if instance is not None
              else t.hero(BOARD_KEY, "Dashboard"))
    # Native per-organ disclosures keep the overview visible; do not put the
    # whole grid inside section_layout's extra collapsed H2 group.
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_html.escape(name)} Dashboard</title><style>{t.css(BOARD_KEY)}{_EXTRA_CSS}</style></head>
<body>{banner}{panel}
{projects_html}
<h2 id="dashboards-heading">Dashboards</h2>
{'<p>No organs connected. Add a connection when your project needs it.</p>' if instance is not None and not snapshot.get("boards") else ''}
<div id="dashboards" class="organ-grid" aria-label="Organ summaries">{''.join(rows)}</div>
{catalogue}
<noscript><p>Publication snapshot. Open an organ for its latest evidence.</p></noscript>
{footer}
<script type="application/json" id="scientist-snapshot">{data}</script>
<script>{t.JS}</script><script>{script}</script></body></html>"""


def badge_endpoint(snapshot: dict) -> dict:
    word = heart_word(snapshot)
    h = _heart(snapshot)
    color = (h or {}).get("color") or "lightgrey"
    mind = next((b for b in snapshot.get("boards") or [] if b["name"] == "Mind"), {})
    backlog = (mind.get("counts") or {}).get("Backlog")
    msg = word if backlog is None else f"{word} · {backlog} tasks queued"
    if "instance" in snapshot and not snapshot.get("boards"):
        msg, color = "No organs connected", "lightgrey"
    return {"schemaVersion": 1, "label": snapshot.get("instance", {}).get("name", "organism"), "message": msg, "color": color}


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
    import yaml

    ap = argparse.ArgumentParser(prog="organism_board", description=__doc__)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--md", action="store_true")
    g.add_argument("--md-brief", action="store_true")
    g.add_argument("--html", action="store_true")
    g.add_argument("--badge", action="store_true")
    g.add_argument("--json", action="store_true")
    g.add_argument("--catalogue", action="store_true", help="export public resource relationships offline; no feed collection")
    ap.add_argument("--instance", type=Path, help="opt-in instance profile; selects only explicitly connected organs")
    ap.add_argument("--projects", type=Path,
                    help="instance-owned project/resource configuration")
    ap.add_argument("--repos", type=Path, help="canonical Mind repos.yaml (required outside a configured workspace)")
    ap.add_argument("--check-projects", action="store_true", help="validate relationships offline; do not collect feeds")
    ap.add_argument("--check-instance", action="store_true", help="validate the profile and project relationships offline")
    ns = ap.parse_args(argv)
    from project_resources import load
    repos_path = ns.repos
    if repos_path is None:
        if os.environ.get("PYAUTO_MIND"):
            repos_path = Path(os.environ["PYAUTO_MIND"]) / "repos.yaml"
        else:
            # Use Brain's manifest-backed resolver rather than guessing a layout.
            brain = Path(theme().__file__).resolve().parents[1]
            sys.path.insert(0, str(brain / "agents"))
            from _repo_paths import repo_path
            repos_path = repo_path(_workspace_root(), "PyAutoMind", required=True) / "repos.yaml"
    try:
        instance = None
        projects_path = HOME / "config" / "projects.json"
        if ns.instance:
            from instance_profile import load as load_instance
            instance, projects_path = load_instance(ns.instance, repos_path, theme())
        elif ns.check_instance:
            ap.error("--check-instance requires --instance")
        projects = load(ns.projects or projects_path, repos_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        ap.error(f"project configuration unavailable or invalid: {exc}")
    if ns.check_projects or ns.check_instance:
        print(f"Project configuration valid: {len(projects['projects'])} public projects")
        return 0
    if ns.catalogue:
        from project_resources import catalogue
        print(json.dumps(catalogue(projects), indent=2))
        return 0
    snap = collect(instance=instance)
    snap["project_resources"] = projects
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
