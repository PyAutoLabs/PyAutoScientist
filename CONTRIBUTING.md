# Contributing to PyAutoLabs

Thank you for contributing to PyAutoLabs. Bug reports, feature ideas,
documentation improvements, examples, tests and code changes are all welcome.

PyAutoLabs software is developed through natural language. A contribution starts
as a plain-English description of what should change and why — not as a diff.
That description is then planned, implemented, tested and released through
[PyAutoScientist](https://github.com/PyAutoLabs/PyAutoScientist), an ecosystem of
agentic-AI coding agents directed by a human maintainer. You are welcome to
describe what you want in words, to write the code yourself, or to do anything in
between; contributions are held to the same standard either way.

If that sounds like a lot of AI to trust with scientific software, start with the
next section. It is the honest answer, and it comes first for a reason.

## How the Code Is Tested

Confidence in this software does not come from who, or what, typed it. It comes
from evidence that it behaves correctly, gathered at four levels.

**Unit tests.** Each library carries its own suite covering individual components
and their numerical behaviour — roughly 3,900 tests in total:

| Library | Tests |
|---|---|
| [PyAutoFit](https://github.com/PyAutoLabs/PyAutoFit) | 1,261 |
| [PyAutoGalaxy](https://github.com/PyAutoLabs/PyAutoGalaxy) | 985 |
| [PyAutoArray](https://github.com/PyAutoLabs/PyAutoArray) | 844 |
| [PyAutoLens](https://github.com/PyAutoLabs/PyAutoLens) | 471 |
| [PyAutoCTI](https://github.com/PyAutoLabs/PyAutoCTI) | 271 |
| [PyAutoNerves](https://github.com/PyAutoLabs/PyAutoNerves) | 135 |

**Every workspace script is a test.** This is the part that matters most, and it
is easy to miss. The example scripts, guides and tutorials are not illustrative
snippets that quietly drift out of date — they are executed as a test suite.
Release validation runs *every* script in ten repositories:

| Repository | Scripts | What it covers |
|---|---|---|
| [autolens_workspace](https://github.com/PyAutoLabs/autolens_workspace) | 373 | Every documented PyAutoLens use case |
| [autogalaxy_workspace](https://github.com/PyAutoLabs/autogalaxy_workspace) | 172 | Every documented PyAutoGalaxy use case |
| [autofit_workspace](https://github.com/PyAutoLabs/autofit_workspace) | 40 | Every documented PyAutoFit use case |
| [autolens_workspace_test](https://github.com/PyAutoLabs/autolens_workspace_test) | 146 | Integration and regression scripts |
| [autofit_workspace_test](https://github.com/PyAutoLabs/autofit_workspace_test) | 63 | Integration and regression scripts |
| [autogalaxy_workspace_test](https://github.com/PyAutoLabs/autogalaxy_workspace_test) | 61 | Integration and regression scripts |
| [HowToLens](https://github.com/PyAutoLabs/HowToLens) | 47 | The lensing tutorial series |
| [HowToGalaxy](https://github.com/PyAutoLabs/HowToGalaxy) | 33 | The galaxy tutorial series |
| [HowToFit](https://github.com/PyAutoLabs/HowToFit) | 21 | The model-fitting tutorial series |
| [euclid_strong_lens_modeling_pipeline](https://github.com/PyAutoLabs/euclid_strong_lens_modeling_pipeline) | 6 | The Euclid production pipeline |

That is roughly 960 scripts exercising the public API end to end. A change that
breaks how a user actually uses the software fails this run, even when every unit
test still passes. The `*_workspace_test` repositories are dedicated integration
suites rather than user-facing tutorials, and exist specifically to catch
regressions in complex workflows — inversions, interferometry, multi-dataset
fits, database and aggregator use, and the JAX likelihood paths.

**Every pull request runs a smoke gate.** A curated fast subset of the workspace
scripts runs on every push and pull request, installed against the real
dependency chain — PyAutoNerves → PyAutoFit → PyAutoArray → PyAutoGalaxy →
PyAutoLens — so cross-repository breakage surfaces on your PR rather than at
release.

**Nothing releases without a health verdict.**
[PyAutoHeart](https://github.com/PyAutoLabs/PyAutoHeart) independently assesses
repository health and emits the authoritative GREEN / YELLOW / RED judgement on
whether it is safe to release. It is not advisory; it gates the release.

Beyond automation, important scientific results are validated against analytic
calculations, established implementations, benchmark datasets and published
results.

The principle behind all of this is set out in the
[PyAuto AI Policy](AI_POLICY.md): a feature is not complete because the code runs
and looks plausible. Its original natural-language requirements are expected to
become tests and runnable examples that demonstrate the requested behaviour.
Building that scaffolding is central to how the project establishes that its
software works.

## The PyAutoScientist Ecosystem

In March 2026, after more than a decade of exclusively human-led development,
PyAutoLabs transitioned to a fully natural-language, agentic-AI development
ecosystem called
[PyAutoScientist](https://github.com/PyAutoLabs/PyAutoScientist). It is organised
as a software organism whose repositories mirror the roles of human organs:

| Organ | Repository | What it does |
|---|---|---|
| Mind | [PyAutoMind](https://github.com/PyAutoLabs/PyAutoMind) | Captures intent. Every task begins here as a plain-English file recording *what* should be done and why, tracked from initial idea to completed implementation. |
| Brain | [PyAutoBrain](https://github.com/PyAutoLabs/PyAutoBrain) | The reasoning centre, working out *how* — classifying, planning and routing each task through specialist coding agents. |
| Hands | [PyAutoHands](https://github.com/PyAutoLabs/PyAutoHands) | The executor. It packages the libraries, generates notebooks from scripts, tags versions and releases to PyPI. |
| Heart | [PyAutoHeart](https://github.com/PyAutoLabs/PyAutoHeart) | The health monitor, whose GREEN / YELLOW / RED verdict is the authoritative "is it safe to release?" gate. |
| Memory | [PyAutoMemory](https://github.com/PyAutoLabs/PyAutoMemory) | Long-term scientific memory — cross-linked literature wikis with verifiable citations, consulted before design decisions. |
| Gut | [PyAutoGut](https://github.com/PyAutoLabs/PyAutoGut) | Holds condemned material — stale branches, dead code — as recoverable git references, then voids it on a sweep. |
| Nerves | [PyAutoNerves](https://github.com/PyAutoLabs/PyAutoNerves) | The configuration and serialization layer (`autonerves`) connecting the project's conventions to every library. |

Because intent is recorded in the Mind and connected to an issue, a branch, a
pull request and a dated completion record, there is a public trail from the
original English request through to the released behaviour. You can read why a
change was needed, how it was interpreted, what was decided during
implementation, and how it was validated. When much of the implementation is
produced through natural-language interaction with AI, that traceability is what
keeps the work inspectable — and lets you question or reproduce it.

## How to Contribute

### 1. Open an Issue (recommended)

The simplest and most effective contribution is a well-described issue on the
repository your task concerns. Describe the problem or the feature in plain
English; you do not need to propose an implementation.

Issues are picked up by James Nightingale through PyAutoBrain's community agent —
the organism's *ears*, which surveys every repository for contributions awaiting
a response. We will then discuss the change with you: what it should do, how it
should behave, and what "correct" looks like. Once that is settled, PyAutoBrain's
feature agent implements it, and the result comes back to your issue.

To make that discussion productive, include the context another person needs to
act on it:

- **Bugs** — a minimal reproducible example, the full traceback, your operating
  system, and your Python and package versions.
- **Features** — the problem, the intended behaviour, and the smallest useful
  scope. Example Python is especially helpful for API proposals.
- **Substantial changes** — raise the approach before investing in an
  implementation.

Search the repository's existing issues first, and use the provided form.

### 2. Run the Ecosystem Yourself

If you are comfortable with agentic AI development, you can set PyAutoScientist
up locally and contribute directly — describing your change in natural language,
letting the agents implement and validate it, and opening the pull request
yourself. Review then happens at the PR.

Be aware that the ecosystem is not yet set up for others to use. Making it
genuinely adoptable is work in progress; today it still carries assumptions about
local layout and tooling that are not documented well enough for you to stand it
up unaided. If you want to go this route, please
[get in touch](https://github.com/PyAutoLabs/PyAutoScientist/issues) and we will
do the setup together — that is the fastest path for you, and it tells us what
needs fixing.

The [adoption guide](https://pyautoscientist.readthedocs.io/en/latest/adoption/guide.html)
describes the fork-and-pull model in the meantime.

### 3. Contributing Without AI

Traditional, hand-written pull requests remain entirely welcome, and are reviewed
to the same standard as everything else. Nothing here requires you to use AI.

One thing to know: the first pass over your pull request will be made by an AI
reviewing agent rather than by a human reading the diff directly. It checks the
change against the repository's conventions, runs the validation, and reports
what it finds. A human then reads that report, forms a judgement and decides —
merging is always a human act. If the review raises something you disagree with,
say so on the PR; you are talking to a person.

## What We Expect From a Submission

Whether written by you, by an agent, or by both, a contribution should arrive
with:

- **A plain-English statement of what changed and why.** If the intent, the scope
  and the standard of success cannot be described in words, the change is not
  ready. This is as true of hand-written work as of AI-assisted work.
- **Evidence that it behaves correctly.** A unit test for numerical behaviour, a
  runnable workspace example for a user-facing workflow, or both. Turning the
  original requirement into a test is the point, not an afterthought.
- **Any public API change named,** together with its impact on the workspaces,
  tutorials and downstream libraries.
- **Provenance checked** for generated code. AI can reproduce patterns from
  existing software without saying so, so check licence compatibility, cite the
  original scientific method or package, and add references to
  [CITATIONS.md](https://github.com/PyAutoLabs/PyAutoLens/blob/main/CITATIONS.md)
  where appropriate.
- **The repository's own rules followed.** Each repository's `AGENTS.md` and
  `README.md` document its setup, architecture, test commands and editing rules.

The full contract — validation, attribution, licensing, confidentiality,
disclosure and human accountability — is in the
[PyAuto AI Policy](AI_POLICY.md). Please read it before submitting AI-assisted
work.

## Repository-Specific Notes

PyAutoLabs repositories have different roles. Consult the repository's
`AGENTS.md` and `README.md`, where present, before editing.

**Source libraries** contain the installable Python packages. Install the target
repository from source, add or update tests alongside behavioural changes, run
the suite named in its `AGENTS.md`, and document any public API change and its
downstream impact. Keep dependencies flowing in the direction that repository
documents.

**Workspaces and tutorials** contain runnable examples and teaching material.
Edit the source scripts under `scripts/` and preserve their narrative
explanations — the prose is what makes the examples teachable. Where notebooks
are generated from scripts, **never edit the notebooks directly**; regenerate
them through the repository's documented PyAutoHands workflow. Run the curated
smoke tests before submitting.

**Workspace-test repositories** are integration suites, not user-facing
tutorials. Preserve the intent of their checks, and never weaken a script to hide
a library regression.

**PyAutoScientist organ repositories** form a living reference implementation
used for daily development. Their `main` branches move quickly and carry no
compatibility promise for the workflow itself. Adopt them by fork-and-pull, keep
local changes within their documented extension surfaces, and pin anything you
rely on. Issues and pull requests are welcome, though abstractions for
hypothetical use cases may be declined in favour of needs demonstrated by a
working system.

## Pull Requests

1. Fork the repository and create a focused branch from `main`.
2. Read its `AGENTS.md` and follow the repository-specific editing rules.
3. Make one coherent change, with tests and documentation where appropriate.
4. Run the repository's documented validation commands.
5. Explain what changed, why, how it was tested, and whether any public API or
   sibling repository is affected.

CI must pass before a pull request can be merged, and every change — AI-assisted
or not — is merged by a human.

## Code of Conduct

Participation in every PyAutoLabs repository is governed by the shared
[PyAutoLabs Code of Conduct](CODE_OF_CONDUCT.md).
