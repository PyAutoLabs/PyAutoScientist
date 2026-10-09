# PyAutoScientist — Agent Guidance

This file is for AI coding agents (Claude Code, Codex, Cursor, etc.) and humans
discovering this repository. It is the agent-agnostic source of truth; Claude
Code loads it via the `@AGENTS.md` import in `CLAUDE.md`.

## What this repo is

**PyAutoScientist is the umbrella landing repo for the PyAuto organism** — a
human-led AI software-development system. It presents the organism (what it is,
how to fork it) through the docs and links in `README.md`; it is not a framework
you install, and owns the Scientist overview renderer and reporting guidance. The organs that do the
work are peer repositories — see the body map in `PyAutoMind/repos.yaml` and the
canonical boundaries in `PyAutoBrain/ORGANISM.md`.

## Scientist home and reporting

The cockpit Scientist tab embeds this repository's dashboard. It is the entry
point for cross-organ summaries and coordination; individual organs retain
their authoritative records and task procedures. For a high-level summary over
the last 24 hours or another requested period, follow [REPORTING.md](REPORTING.md).
The copyable dashboard prompt points here. Current status cards are not a
historical activity ledger.

The dashboard uses Brain's shared hero/panel, registry and state validator.
Its organ disclosures stay visible as a grid, without another outer disclosure
or duplicate organ navigation. Each expanded organ has at most three concise
rows. `scripts/overview.js` is inlined at render time and refreshes published
feeds without replacing open disclosures or prompt controls.

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

<!-- repos_sync:filing:begin -->
## Where to file

Questions, help with code or an analysis, ideas, bug reports and results from a
user or collaborator — or an agent acting for one — go to
<https://github.com/orgs/PyAutoLabs/discussions> in the matching category
(Help & Questions, Ideas & Proposals, Bugs & Errors, Show and tell;
Announcements is maintainers-only), never to this repo's Issues. An agent never
runs `gh issue create` for such a report: it drafts the title, category and
body and hands them to the human (sessions cannot create Discussions). Only the
development flow — Mind prompt → `/start_dev` → `/create_issue` → one issue per
task → PR — opens issues here. Why: `PyAutoMind/policy/community_surface.md`.
<!-- repos_sync:filing:end -->

<!-- repos_sync:standards:begin -->
## Shared standards

Before changing a shared interface, consult the applicable
[organism standard](https://github.com/PyAutoLabs/PyAutoBrain/blob/main/docs/standards.md)
on demand, identify affected consumers, and validate their adoption. Change
generated guidance at its canonical source and regenerate.

For board changes, follow the applicable sizing, navigation and orchestration
standards and reuse Brain’s shared components. Keep domain data, prompt meaning
and approval boundaries with the board’s owner.
<!-- repos_sync:standards:end -->
