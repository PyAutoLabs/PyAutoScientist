# PyAutoScientist — Agent Guidance

This file is for AI coding agents (Claude Code, Codex, Cursor, etc.) and humans
discovering this repository. It is the agent-agnostic source of truth; Claude
Code loads it via the `@AGENTS.md` import in `CLAUDE.md`.

## What this repo is

**PyAutoScientist is the umbrella landing repo for the PyAuto organism** — a
human-led AI software-development system. It presents the organism (what it is,
how to fork it) through the docs and links in `README.md`; it is not a framework
you install, and it holds no organism code of its own. The organs that do the
work are peer repositories — see the body map in `PyAutoMind/repos.yaml` and the
canonical boundaries in `PyAutoBrain/ORGANISM.md`.

## Editing rules

- **The organ table in `README.md` is generated** from `PyAutoMind/repos.yaml`
  (between the `repos_sync:organs` markers). Do not hand-edit it — change
  `repos.yaml`, then run `python3 PyAutoMind/scripts/repos_sync.py --write`.
- **The RTD documentation source does not live here yet.** The published docs at
  https://pyautoscientist.readthedocs.io are built from **`PyAutoBrain/docs/`**;
  edit the docs there.

## Future intent (not now — Phase 3, demand-gated)

Migrating the RTD docs source *into* this repo — so PyAutoScientist becomes the
real documentation centre rather than a landing page pointing at Brain's `docs/`
— is a recorded future step. It is deliberately deferred until there is demand;
do not start it as part of routine work.

<!-- repos_sync:history:begin -->
## Never rewrite history

Never rewrite pushed history on any repo with a remote — no `git init` over a
tracked repo, no force-push to `main`, no fresh-start "Initial commit", no
`filter-repo` / `filter-branch` / `rebase -i` on pushed branches. To get a
clean tree: `git fetch origin && git reset --hard origin/main && git clean -fd`.
<!-- repos_sync:history:end -->

<!-- repos_sync:deliverable:begin -->
## Sessions end at their deliverable

A session ends when it reports its deliverable — never arm anything that
outlives the turn to wait for CI, a review or a merge: no `send_later`, no
`subscribe_pr_activity`, no `CronCreate`, no `ScheduleWakeup`, no `/loop`, no
`RemoteTrigger` create/update/run. Judge once, report, stop; the human re-runs
`/prm` (or the batch review) when it is green. Measured: five batch members
armed hourly check-ins on 2026-08-31, and a mobile `/prm` re-armed a 60-minute
`send_later` hourly all night on 2026-09-03 with no task active, draining usage.
<!-- repos_sync:deliverable:end -->
