# ChatGPT orchestration route

This is a **thin entry adapter**, not a new PyAutoScientist organ, agent, or
task-state system. The canonical workflow remains in
[PyAutoBrain](https://github.com/PyAutoLabs/PyAutoBrain), while
[PyAutoMind](https://github.com/PyAutoLabs/PyAutoMind) remains the sole record
of what the organism is trying to do and where each task has reached.

Use this route when the human is already working in an ordinary ChatGPT
conversation and wants that conversation to remain the scientist-facing
orchestrator.

## Start from ChatGPT

Copy this into the ChatGPT conversation, with the GitHub integration connected:

```text
Start this PyAutoMind task using the ChatGPT route: <prompt-path-or-task>.

Keep this ChatGPT conversation as the top-level orchestrator. Follow the
canonical PyAutoBrain development workflow and PyAutoMind lifecycle. Use the
GitHub capabilities available in this conversation for repository and PR work
when they are sufficient. If a phase needs capabilities this conversation does
not have — for example a local filesystem, shell, package imports, tests,
scientific runs, profiling, worktrees, an independent reviewer when required,
or a remote compute environment —
handoff only that smallest coherent execution phase to a supported execution
environment. Bring the resulting diff, commit and validation evidence back into
this same Mind task and continue the Brain review / Heart / PR workflow here.

Do not create a second task-state system and do not automate the ChatGPT web
client or treat a ChatGPT session as an API.
```

If the task has not yet been filed in Mind, use the normal `/start_dev`
semantics rather than inventing a Chat-specific lifecycle.

## Adapter contract

On entry, read the current versions of these canonical sources rather than
copying their policy here:

- `PyAutoMind/active.md` and the referenced prompt — intent and shared task
  state.
- `PyAutoBrain/skills/WORKFLOW.md` — organ boundaries, development flow,
  cross-harness behaviour and task-state rules.
- `PyAutoBrain/skills/start_dev/` — classification, planning, branch survey,
  issue and lifecycle flow.
- `PyAutoBrain/skills/GITHUB_ACCESS.md` — mapping GitHub operations onto the
  surface the current session actually exposes.
- `PyAutoBrain/skills/MODEL_DELEGATION.md` — the bounded-worker contract.
- `PyAutoBrain/AUTONOMY.md` — approval and autonomy gates.

The current conversation is the **orchestration environment**. Execution is a
separate question. Inspect the capabilities actually available now; do not
infer them from the product or model name. In particular, GitHub integrations
can differ in repository scope and read/write permissions.

Stay in ChatGPT for work its current capabilities can honestly complete:
repository inspection, architecture reasoning, planning, GitHub-native edits,
issues/branches/commits/PRs/reviews, and CI inspection where those actions are
available. Existing repository CI can supply execution evidence when it
actually covers the required validation; do not manufacture a temporary
workflow merely to obtain a shell. CI evidence does **not** replace the Heart
verdict. If this conversation cannot obtain a fresh authoritative Heart reading,
treat that as a missing capability and obtain only that bounded evidence before
shipping.

Escalate only when the task's required evidence needs a capability the current
conversation lacks. Independent review counts: a second pass in the same
conversation is not an independent reviewer. A bounded execution or review
request should identify the existing
Mind task, exact repository/branch/commit, permitted scope, required commands
or scientific checks, and the evidence to return. It should not receive the
whole original task merely because one test has to run.

When substantial implementation itself depends on runtime behaviour — for
example environment-specific debugging, scientific/numerical validation,
profiling, HPC/SSH work, generated artefacts that must be checked locally, or
large worktree-coordinated changes — route that coherent phase to an execution
environment from the outset while keeping Brain decisions, Mind state, review,
Heart gating and human merge decisions in the orchestrating conversation.

## Definition of done is unchanged

The route used to perform the work is not evidence that it is correct.
Applicable unit/integration/smoke/scientific validation, independent review,
Heart gating, PR review, human merge requirements and release rules remain the
same as for any other PyAutoScientist task.

Cross-environment continuation uses the existing Mind task and branch/commit
evidence. Record the real harness/session metadata when known; never fabricate a
resume command or create a ChatGPT-specific ledger.
