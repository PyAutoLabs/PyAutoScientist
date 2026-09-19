# PyAutoScientist

[![organism](https://img.shields.io/endpoint?url=https://pyautolabs.github.io/PyAutoScientist/badge.json)](https://pyautolabs.github.io/PyAutoScientist/)

**PyAutoScientist enables human-led, natural-language software development** — an experimental reference implementation by James Nightingale. Humans describe what the software should do, why it is needed, and how success should be judged; specialist AI agents help plan, implement, test, and prepare releases. Humans remain responsible for scientific objectives, contributor communication, and consequential decisions. Using this ecosystem is optional: you do not need to adopt PyAutoScientist or use AI to contribute to PyAutoLabs.

See the **[PyAutoScientist Dashboard](https://pyautolabs.github.io/PyAutoScientist/)**
to watch the organism live and know where to work: it shows each organ's own
dashboard headline, topped by a "where to work next" hint (if the Heart is
green, you go pick a task on the Mind):

- **[PyAutoMind Dashboard](https://pyautolabs.github.io/PyAutoMind/)**: planned and active development tasks on the scientist's mind.
- **[PyAutoHeart Dashboard](https://pyautolabs.github.io/PyAutoHeart/)**: the health of every repository, rolled into the authoritative GREEN/STALE/YELLOW/RED release verdict.
- **[PyAutoHands Dashboard](https://pyautolabs.github.io/PyAutoHands/)**: what shipped — the released library versions and the release train's recent runs.
- **[PyAutoMemory Dashboard](https://pyautolabs.github.io/PyAutoMemory/)**: the scientist's long-term knowledge — the reading queue, citation work and each sub-wiki's maturity.

📖 **Docs:** https://pyautoscientist.readthedocs.io<br>
🍴 **Adoption guide:** https://pyautoscientist.readthedocs.io/en/latest/adoption/guide.html

## From natural language to trusted software

Making development accessible through natural language does not reduce the standard of evidence required before code is accepted or released.

PyAuto uses several layers of testing:

* The scientific libraries have extensive unit-test suites covering their numerical behaviour and public APIs.
* User-facing workspaces run curated smoke tests on every push and pull request.
* Release validation runs the full set of runnable workspace scripts, including the examples in [`autolens_workspace`](https://github.com/PyAutoLabs/autolens_workspace). Scripts that genuinely cannot be run automatically are listed explicitly, with reasons, in each workspace’s `config/build/no_run.yaml`.
* Dedicated integration repositories such as [`autolens_workspace_test`](https://github.com/PyAutoLabs/autolens_workspace_test) mirror complete modelling workflows while replacing expensive non-linear searches with fast test configurations.
* [`PyAutoHeart`](https://github.com/PyAutoLabs/PyAutoHeart) monitors repository health and provides the release-readiness gate used before software is published.

Natural-language requirements are translated into tests, examples and documentation that demonstrate the requested behaviour. AI-generated code is not considered complete simply because it runs or appears plausible.

The shared [PyAuto AI Policy](AI_POLICY.md) describes the principles governing natural-language development, validation, attribution, licensing and human responsibility.

## The organs

PyAutoScientist is organised as a software organism whose repositories mirror the roles of human organs:

<!-- repos_sync:organs:begin -->
| Organ | Repo | Role |
|---|---|---|
| Brain | [PyAutoBrain](https://github.com/PyAutoLabs/PyAutoBrain) | Works out *how*: classifies, plans and routes work through specialist reasoning and coding agents. |
| Mind | [PyAutoMind](https://github.com/PyAutoLabs/PyAutoMind) | Captures intent: every piece of work begins as a plain-English description of *what* should change and is tracked from the initial idea to its completed implementation. |
| Cortex | [PyAutoCortex](https://github.com/PyAutoLabs/PyAutoCortex) | Holds the science body map and one ledger per science project — the runs on the cluster and a dated log of what was set off, seen and learned — so a project is picked up where it was left, apart from software development. |
| Memory | [PyAutoMemory](https://github.com/PyAutoLabs/PyAutoMemory) | Provides long-term scientific knowledge through cross-linked literature wikis, concepts and verifiable citations. |
| Heart | [PyAutoHeart](https://github.com/PyAutoLabs/PyAutoHeart) | Monitors repository health and supplies the authoritative GREEN/YELLOW/RED release-readiness verdict. |
| Hands | [PyAutoHands](https://github.com/PyAutoLabs/PyAutoHands) | Executes builds and releases: packages libraries, generates notebooks, creates tags and publishes releases to PyPI. |
| Nerves | [PyAutoNerves](https://github.com/PyAutoLabs/PyAutoNerves) | Provides the configuration and serialization layer connecting shared conventions across the scientific libraries and workspaces. |
| Gut | [PyAutoGut](https://github.com/PyAutoLabs/PyAutoGut) | Holds stale branches, dead code and other condemned material as recoverable Git references before it is permanently removed. |
<!-- repos_sync:organs:end -->

PyAutoBrain also contains specialist agents that act like additional senses and capabilities. For example, its community agent serves as the organism’s **Ears**, listening to the shared Discussions hub and user-submitted GitHub issues, helping the human maintainer discuss them with contributors and routing actionable work into development.

The Cortex keeps scientific experiments on a separate track from software development. An experiment is written down as a question with the result that will settle it stated in advance, waits for whatever software work it depends on to be finished, runs on a computing cluster, and then comes back for the human maintainer to judge. Its board shows every experiment currently on that track — waiting to start, running, or waiting on a verdict — and is published at <https://pyautolabs.github.io/PyAutoCortex/>. The verdicts themselves are recorded in the Cortex and nowhere else: a conclusion written only into a project’s own notes does not count, which is what keeps the record of what the science actually found complete.

The software developed by the organism lives across the [PyAutoLabs](https://github.com/PyAutoLabs) organisation. See the [PyAutoLabs front door](https://pyautolabs.github.io) for the full repository map.

## Project History

In March 2026, following more than a decade of exclusively human-led software development, PyAutoLabs transitioned to a fully natural-language, agentic-AI development ecosystem called `PyAutoScientist`. The software it now develops grew out of that decade of human-led work: [PyAutoLens](https://github.com/PyAutoLabs/PyAutoLens) (strong gravitational lensing), [PyAutoGalaxy](https://github.com/PyAutoLabs/PyAutoGalaxy) (galaxy structure and morphology), [PyAutoFit](https://github.com/PyAutoLabs/PyAutoFit) (Bayesian model fitting), [PyAutoArray](https://github.com/PyAutoLabs/PyAutoArray) (scientific data structures) and [PyAutoCTI](https://github.com/PyAutoLabs/PyAutoCTI) (CCD charge-transfer calibration), together with their workspaces and tutorials.

## Contributing

Start with [PyAutoLabs Discussions](https://github.com/orgs/PyAutoLabs/discussions) for questions, ideas, and proposals. Confirmed reproducible bugs and agreed implementation work belong in the affected repository's issue tracker. You may also submit a conventional pull request, with or without AI assistance.

Read the [organization-wide contribution guide](https://github.com/PyAutoLabs/.github/blob/main/CONTRIBUTING.md) for the available development paths and standards. For changes to PyAutoScientist itself, also follow this repository's local agent guidance.

## Community

The [shared community hub](https://github.com/orgs/PyAutoLabs/discussions) welcomes users of every PyAutoLabs repository. Contribution, conduct, and support guidance are maintained in [PyAutoLabs/.github](https://github.com/PyAutoLabs/.github); please read the [Code of Conduct](https://github.com/PyAutoLabs/.github/blob/main/CODE_OF_CONDUCT.md) before participating. The [AI Policy](AI_POLICY.md) remains here and is linked explicitly by other repositories.

## License

Released under the [MIT License](https://opensource.org/licenses/MIT). Copyright (c) 2026 Jammy2211.
