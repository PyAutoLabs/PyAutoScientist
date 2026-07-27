# Contributing to PyAutoLabs

Thank you for contributing to PyAutoLabs. Bug reports, feature ideas,
documentation improvements, examples, tests, and code changes are all welcome.
Contributions may be written with or without AI assistance; they are reviewed
to the same standards.

## Start with an Issue

Search the relevant repository's existing issues before opening a new one.
When filing an issue, use the provided form and include the context needed for
another person to act on it:

- For bugs, provide a minimal reproducible example, the full traceback, your
  operating system, and your Python and package versions.
- For features, explain the problem, the intended behavior, and the smallest
  useful scope. Example Python is especially helpful for API proposals.
- For substantial changes, discuss the approach with the maintainers before
  investing in an implementation.

## Choose the Right Development Path

PyAutoLabs repositories have different roles. Consult the repository's
`AGENTS.md` and `README.md`, where present, for its setup, architecture, test
commands, and editing rules.

### Source Libraries

The PyAuto source libraries contain the installable Python packages. Install
the target repository from source, add or update tests with behavioral changes,
run the suite named in its `AGENTS.md`, and document any public API change and
its downstream impact. Keep dependencies flowing in the direction documented
by that repository.

### Workspaces and Tutorials

Workspace and HowTo repositories contain runnable examples and teaching
material. Edit their source scripts and preserve their narrative explanations.
Where notebooks are generated from scripts, never edit the notebooks directly;
regenerate them with the repository's documented PyAutoHands workflow. Run the
curated smoke tests before submitting a pull request.

Workspace-test repositories are integration suites rather than user-facing
tutorials. Preserve the intent of their checks and never weaken a script to
hide a library regression.

### PyAutoScientist Organ Repositories

PyAutoBrain, PyAutoMind, PyAutoHands, PyAutoHeart, PyAutoMemory, and the other
organ repositories form a living reference implementation used for daily
development. Their `main` branches move quickly and carry no compatibility
promise for the workflow itself. Adopt them by fork-and-pull, keep local
changes within their documented extension surfaces, and pin anything you rely
on. Issues and pull requests are welcome, but abstractions for hypothetical use
cases may be declined in favor of the needs demonstrated by a working system.

See the [PyAutoScientist adoption guide](https://pyautoscientist.readthedocs.io/en/latest/adoption/guide.html)
for the fork-and-pull model.

## Maintainer Workflow

Maintainer-driven work starts as a prompt in
[PyAutoMind](https://github.com/PyAutoLabs/PyAutoMind), then runs through the
PyAutoBrain development workflow:

1. Record the intent as a typed PyAutoMind prompt.
2. Run `start-dev` to classify the task, prepare the plan, and create or resume
   its issue.
3. Use `start-library` or `start-workspace` to create an isolated task
   worktree.
4. Use `ship-library` or `ship-workspace` to validate the change and open the
   pull request.

External contributors do not need to use this internal workflow. Opening a
clear issue or pull request in the relevant repository is enough.

## Pull Requests

1. Fork the repository and create a focused branch from `main`.
2. Read its `AGENTS.md` and follow the repository-specific editing rules.
3. Make one coherent change, with tests and documentation where appropriate.
4. Run the repository's documented validation commands.
5. Explain what changed, why, how it was tested, and whether any public API or
   sibling repository is affected.

All changes require human review, including AI-assisted changes. CI must pass
before a pull request can be merged.

AI-assisted contributions must also follow the shared
[PyAuto AI Policy](AI_POLICY.md), including its requirements for validation,
attribution, licensing, confidentiality, disclosure, and human accountability.

## Code of Conduct

Participation in every PyAutoLabs repository is governed by the shared
[PyAutoLabs Code of Conduct](CODE_OF_CONDUCT.md).
