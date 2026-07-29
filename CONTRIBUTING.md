# Contributing to PyAutoLabs

Thank you for contributing to PyAutoLabs. Bug reports, feature ideas, documentation improvements, scientific examples, tests and code changes are all welcome.

PyAutoLabs uses `PyAutoScientist`, a **fully natural-language, agentic-AI development ecosystem**. The simplest way to contribute is therefore to describe what you want in natural language through a GitHub issue. You do not need to install PyAutoScientist, use an AI coding agent or understand the internal development machinery.

Contributions written without AI assistance remain equally welcome. Every contribution is evaluated against the same scientific, testing and documentation standards.

## If you were directed here from another repository

This is the shared contribution guide for the entire [PyAutoLabs](https://github.com/PyAutoLabs) organisation. You may have been directed here from a scientific library such as [PyAutoLens](https://github.com/PyAutoLabs/PyAutoLens), a user-facing workspace or another PyAutoLabs repository.

Your issue or pull request should normally be submitted to the repository from which you were directed. For example, a PyAutoLens bug should be reported on the [PyAutoLens issue tracker](https://github.com/PyAutoLabs/PyAutoLens/issues), not on PyAutoScientist. Use this document for the shared contribution process, then follow the `README.md` and `AGENTS.md` in the relevant repository for its specific architecture, development setup and test commands.

Issues should be submitted directly to PyAutoScientist only when they concern the development ecosystem or the shared policies and documentation held in this repository.

## Ways to contribute

### 1. Open a GitHub issue

This is the recommended route for most contributors.

Search the relevant repository’s existing issues and then open a new issue describing the problem or requested behaviour in plain English. You should include enough context for someone unfamiliar with your work to understand what is needed:

* For bugs, provide a minimal reproducible example, the full traceback, the expected and actual behaviour, your operating system, and your Python and package versions.
* For features, explain the scientific or technical problem, the intended behaviour and the smallest useful scope. Example Python is especially helpful for proposed APIs.
* For scientific methods, explain the underlying assumptions and provide links to relevant papers, algorithms or existing implementations.
* For substantial changes, begin with an issue so that the approach can be discussed before time is invested in implementation.

The community agent within [`PyAutoBrain`](https://github.com/PyAutoLabs/PyAutoBrain)—the **Ears** of the PyAutoScientist organism—monitors issues and pull requests across PyAutoLabs. It helps James Nightingale triage new submissions, identify missing information and prepare responses.

James will discuss the request with you where necessary. Once the intended behaviour is clear, an actionable issue can be routed through the relevant PyAutoBrain feature, bug, documentation or workspace agent for implementation. The original issue remains the public record connecting your natural-language request to the resulting code and pull request.

### 2. Develop using PyAutoScientist

Contributors who are comfortable with agentic-AI development may run the PyAutoScientist ecosystem locally and use its natural-language workflows directly.

In this workflow, a plain-English development requirement is recorded in [`PyAutoMind`](https://github.com/PyAutoLabs/PyAutoMind), planned and routed by [`PyAutoBrain`](https://github.com/PyAutoLabs/PyAutoBrain), implemented in an isolated branch or worktree, validated and then submitted as a pull request.

PyAutoScientist is a working system used for daily PyAutoLabs development, but its installation and adoption process is not yet fully prepared for external contributors. If you want to try this route, please contact James Nightingale so that the ecosystem can be set up and tested with you.

The current [PyAutoScientist adoption guide](https://pyautoscientist.readthedocs.io/en/latest/adoption/guide.html) documents the intended fork-and-pull model.

### 3. Contributing without AI

Traditional contributions written without AI assistance remain fully supported.

You may fork the relevant repository, create a focused branch, make the change yourself and open a conventional pull request. When the pull request is submitted, the Ears of PyAutoBrain will identify and triage it, and specialist agents may perform the first technical inspection of the change, its tests and its wider impact.

This agent-assisted first pass helps the maintainer understand contributions consistently across a large ecosystem. It does not lower the standards applied to the pull request or remove human accountability: James remains responsible for contributor communication, consequential review decisions and whether the change is merged.

## Repository-specific development

Each PyAutoLabs repository has its own `README.md` and, where present, `AGENTS.md`. Read these before making changes because they define the repository’s architecture, development setup, test commands and editing rules.

### Source libraries

Source libraries such as [PyAutoLens](https://github.com/PyAutoLabs/PyAutoLens), [PyAutoGalaxy](https://github.com/PyAutoLabs/PyAutoGalaxy), [PyAutoArray](https://github.com/PyAutoLabs/PyAutoArray) and [PyAutoFit](https://github.com/PyAutoLabs/PyAutoFit) contain the installable Python packages.

Install the target repository from source, add or update tests for behavioural changes, run the documented test suite and describe any effect on public APIs or downstream libraries.

### Workspaces and tutorials

Workspace and HowTo repositories contain runnable examples and teaching material. Edit their source scripts and preserve their narrative explanations.

Where notebooks are generated from scripts, edit the Python scripts and regenerate the notebooks using the documented PyAutoHands workflow rather than editing notebooks directly.

### Workspace-test repositories

Workspace-test repositories are integration suites rather than user-facing tutorials. They mirror complete scientific workflows using faster test configurations.

Preserve the scientific intent of their checks and never weaken or remove a test merely to hide a library regression.

### PyAutoScientist organ repositories

The organ repositories form the working PyAutoScientist reference implementation. Their `main` branches may change rapidly while the ecosystem is prepared for wider adoption.

Read their local guidance, keep changes within documented extension points and discuss significant architectural changes before implementation.

## Testing and trust

Natural-language and agentic-AI development make it easier to translate ideas into code, but they do not reduce the validation required before that code is accepted.

PyAuto uses several complementary layers of testing:

* **Unit tests:** Each source library has an extensive test suite covering numerical behaviour, data structures and public APIs. For example, see the [PyAutoLens unit tests](https://github.com/PyAutoLabs/PyAutoLens/tree/main/test_autolens).
* **Pull-request smoke tests:** User-facing workspaces run curated scripts and notebooks on pushes and pull requests to identify API breakages quickly.
* **Full workspace validation:** The release process runs the complete set of runnable scripts in user-facing workspaces such as [`autolens_workspace`](https://github.com/PyAutoLabs/autolens_workspace). Any scripts that cannot be run automatically must be listed explicitly, with a reason, in `config/build/no_run.yaml`.
* **Dedicated integration workspaces:** Repositories such as [`autolens_workspace_test`](https://github.com/PyAutoLabs/autolens_workspace_test) mirror complete scientific workflows using fast test configurations. These are run against both the development branches and released versions of the libraries.
* **Release-readiness checks:** [`PyAutoHeart`](https://github.com/PyAutoLabs/PyAutoHeart) monitors unit tests, workspace validation, open pull requests, version compatibility and other health signals before a release proceeds.

New functionality should be accompanied by tests or runnable examples that demonstrate the intended behaviour. A change is not complete merely because generated code runs or looks plausible.

## What contributors are responsible for

Whether you contribute through an issue, PyAutoScientist or a traditional pull request, you should be able to explain in natural language:

* what should change and why;
* the scientific or technical assumptions involved;
* the intended behaviour;
* how the result should be tested;
* any effect on public APIs, workspaces or downstream repositories; and
* how you determined that the implementation is correct.

Contributors are also responsible for:

* adding or updating unit tests and workspace examples where appropriate;
* running the validation commands documented by the target repository;
* documenting public API changes and their downstream impact;
* checking the provenance and licence of adapted code;
* citing published methods and existing software where appropriate; and
* ensuring that private, embargoed or collaborator-controlled information is not submitted to an unapproved AI service.

AI-assisted contributions must follow the shared [PyAuto AI Policy](AI_POLICY.md). The policy does not require every line of code to have been manually written or read line by line by a human. It requires the contributor and maintainer to understand the purpose and important scientific decisions, and to provide tests and examples that demonstrate the behaviour.

## How PyAutoScientist works

PyAutoScientist is organised as a software organism. Its organs divide development responsibilities while preserving the connection between the original natural-language request and the released software.

| Organ      | Repository                                                 | Responsibility                                                                                                                                                                                       |
| ---------- | ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Mind**   | [PyAutoMind](https://github.com/PyAutoLabs/PyAutoMind)     | Records what should be done: intent, goals, priorities and workflow state. It tracks work from a plain-English prompt through its GitHub issue, branch, pull request and completion record.          |
| **Brain**  | [PyAutoBrain](https://github.com/PyAutoLabs/PyAutoBrain)   | Determines how work should be done by classifying, planning, decomposing and routing it through specialist agents. The Ears are a community-facing conductor within the Brain, not a separate organ. |
| **Heart**  | [PyAutoHeart](https://github.com/PyAutoLabs/PyAutoHeart)   | Determines whether the ecosystem is healthy and provides the authoritative release-readiness verdict.                                                                                                |
| **Hands**  | [PyAutoHands](https://github.com/PyAutoLabs/PyAutoHands)   | Executes builds and releases, including package creation, notebook generation, tagging and publication to PyPI.                                                                                      |
| **Memory** | [PyAutoMemory](https://github.com/PyAutoLabs/PyAutoMemory) | Provides long-term scientific knowledge through literature wikis, concepts, bibliographies and verifiable citations.                                                                                 |
| **Gut**    | [PyAutoGut](https://github.com/PyAutoLabs/PyAutoGut)       | Holds obsolete or condemned development material as recoverable Git references before its eventual removal.                                                                                          |
| **Nerves** | [PyAutoNerves](https://github.com/PyAutoLabs/PyAutoNerves) | Provides the shared configuration and serialization layer connecting the conventions used by the scientific libraries and workspaces.                                                                |

The normal call chain is:

`Mind → Brain → Heart (validation gate) → Hands (execution)`

Humans lead the process by describing the desired outcome, discussing scientific and technical decisions, responding to contributors and approving consequential actions.

## Code of Conduct

Participation in every PyAutoLabs repository is governed by the shared [PyAutoLabs Code of Conduct](CODE_OF_CONDUCT.md).
