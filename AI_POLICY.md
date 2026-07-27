# PyAuto AI Policy

Natural language is the foundation of PyAuto’s approach to artificial
intelligence. Our goal is to allow users and developers to begin by clearly
describing what they want to achieve, while AI translates that intent into the
necessary software APIs, syntax and implementation.

Natural language does not remove the need for expertise. Instead, it helps
distinguish between knowledge that is essential to the science and technical
detail that can reasonably be delegated to AI.

Use natural language to remove unnecessary barriers, but not to bypass the
knowledge required to direct, understand and validate the work.

This policy describes how that principle applies to the use, teaching and
development of PyAuto software. It is informed by
[*How to Craft the Right Language AI Policy For Your Research Group (Some
Assembly Required)*](https://arxiv.org/abs/2607.20836), which argues that AI
policies should reflect the values of the communities adopting them.

PyAuto combines three priorities:

- **Natural-language accessibility:** reducing the technical distance between
  a scientific idea and its implementation.
- **Learning and expertise:** helping users develop the knowledge required to
  describe, direct and evaluate an analysis.
- **Scientific trustworthiness:** validating AI-assisted work through testing,
  reproducible examples, attribution and transparent development records.

This is a living policy and will evolve alongside the capabilities and risks
of AI systems.

## Natural language as the starting point

PyAuto aims to make natural language the primary starting point for scientific
analysis and software development.

As a rule of thumb, before delegating a consequential task to AI, you should be
able to describe:

- what you are trying to achieve;
- the relevant data and assumptions;
- the intended scientific or technical method;
- the expected output; and
- how you will determine whether the result is correct.

If you cannot yet describe these clearly, you may not have the knowledge
required to direct or validate the task. In this situation, AI should first
help you learn, explore the available approaches and refine your description—not
immediately produce a final scientific result.

The [PyAutoLens AI Assistant](https://github.com/PyAutoLabs/autolens_assistant)
demonstrates this approach. A user can describe a lens-modelling problem in
natural language, including the dataset, lens and source models, computational
requirements and desired figures. The assistant translates this scientific
description into the appropriate PyAutoLens workflow without requiring the user
to know every Python class, configuration option or API call.

A new user may not initially be able to provide such a detailed description.
They can instead begin with questions, discuss the available modelling
approaches or use Teacher Mode to build the knowledge needed to formulate the
analysis. Natural language is therefore both an interface for performing tasks
and a means of learning how to define them.

## AI must support learning

All PyAuto AI support must include routes for developing the knowledge and
expertise needed to use the software responsibly. AI should be able to:

- explain the scientific and statistical concepts underlying an analysis;
- help users express their objectives and assumptions more precisely;
- describe the available modelling choices and their consequences;
- explain generated code and results;
- identify assumptions, limitations and possible failure modes; and
- direct users to human-readable learning material and runnable examples.

The principal learning resources are:

- [HowToLens](https://github.com/PyAutoLabs/HowToLens), which teaches
  gravitational lensing, Bayesian inference and lens modelling from first
  principles;
- the [autolens_workspace](https://github.com/PyAutoLabs/autolens_workspace),
  which provides runnable examples and guides covering PyAutoLens use cases;
  and
- the guided and Teacher modes provided by the
  [PyAutoLens AI Assistant](https://github.com/PyAutoLabs/autolens_assistant).

AI should cultivate the understanding required to hold a meaningful scientific
conversation about the task. It should not turn researchers into passive
reviewers of generated work. The person using AI remains responsible for the
scientific decisions, interpretation of the results and recognition of when
additional expertise is required.

## Removing unnecessary syntax

Natural language can appropriately replace knowledge of syntax that is
incidental to the scientific objective.

For example, a researcher may understand how they want a figure to look without
knowing the exact Matplotlib API needed to adjust its axes, labels, colour map or
layout. Similarly, they may understand the intended structure of a paper or
equation without remembering the required LaTeX commands. In these cases,
natural language allows the researcher to communicate the desired result while
AI handles the implementation details.

Understanding the inner workings or complete syntax of Matplotlib or LaTeX is
not normally integral to the lensing science being performed. Requiring
researchers to master every incidental API before making a small change would
create an unnecessary barrier.

This does not mean that knowledge is unnecessary. Some general understanding of
the tool or domain is usually needed to describe the intended result, steer the
AI and recognize incorrect output. The required expertise should depend on the
consequences of the task: detailed knowledge of Matplotlib syntax is rarely
essential, whereas understanding the assumptions of a lens mass model is.

The distinction is between:

- syntax and implementation details, which can often be safely delegated
  through natural language; and
- scientific concepts, assumptions and judgments, which the researcher must
  understand sufficiently to describe and defend.

## AI-assisted software development

The same natural-language principle applies to PyAuto software development.
Development begins with a plain-English description of what should change, why
it should change, the expected behaviour and how success will be demonstrated.
AI can then translate this intent into source code, tests, examples and
documentation.

PyAuto does not require every line of Python source code to have been manually
written or read line by line by a human. Confidence in software does not arise
from human authorship alone; it arises from evidence that the software behaves
correctly.

AI-assisted changes must therefore be validated at the appropriate levels:

- **Unit tests** test individual components and numerical behaviour, as
  illustrated by the
  [PyAutoLens test suite](https://github.com/PyAutoLabs/PyAutoLens/tree/main/test_autolens).
- **End-to-end workspace examples** demonstrate that complete scientific
  workflows run correctly using the public API in the
  [autolens_workspace](https://github.com/PyAutoLabs/autolens_workspace).
- **Integration and dedicated test scripts** exercise complex workflows through
  the
  [autolens_workspace_test](https://github.com/PyAutoLabs/autolens_workspace_test)
  and other task-specific validation repositories.
- **Scientific validation** compares important results with analytic
  calculations, established implementations, benchmark datasets, published
  results or expert judgment where appropriate.

An AI-generated feature is not complete merely because the code runs or appears
plausible. Its original natural-language requirements should be translated into
tests and examples that demonstrate the requested behaviour. Building this test
scaffolding is central to how PyAuto establishes that AI-assisted software
works.

Tests do not remove the need to understand the scientific assumptions or public
interfaces. The person who proposes, reviews or releases an AI-assisted change
remains accountable for its behaviour and for the adequacy of its validation.

## Attribution, licensing and software plagiarism

AI systems may reproduce or adapt patterns from existing software, algorithms
and publications without identifying their origin. Natural-language generation
can obscure this provenance because the user may receive working code without
being shown where its ideas or implementation originated.

AI-generated code must therefore be treated as having uncertain provenance
until it has been reviewed. Contributors must:

- investigate whether substantial or specialized generated code resembles an
  existing implementation;
- identify and cite the original scientific method or software where
  appropriate;
- check that any reused implementation is compatible with its original
  licence;
- avoid incorporating code whose licence or provenance is unclear; and
- add relevant papers and software references to the
  [PyAutoLens citations documentation](https://github.com/PyAutoLabs/PyAutoLens/blob/main/CITATIONS.md).

If an implementation substantially follows an existing published method or
software package, attribution is required even if the AI did not reveal the
connection. AI assistance does not remove normal responsibilities concerning
plagiarism, copyright, licensing or scientific citation.

## Open and traceable natural-language development

PyAutoScientist is the open, human-led AI development ecosystem used across
PyAuto. Its purpose is to turn natural-language scientific and software
requirements into planned, tested and released code while retaining a
traceable connection to the original human intent.

Development begins in [PyAutoMind](https://github.com/PyAutoLabs/PyAutoMind),
where a plain-English description records what should be done and why. This
description is connected to a GitHub issue, development branch, pull request
and dated completion record. Planning and agent responsibilities are documented
through [PyAutoBrain](https://github.com/PyAutoLabs/PyAutoBrain), while
repository health and release readiness are independently monitored by
[PyAutoHeart](https://github.com/PyAutoLabs/PyAutoHeart).

Together with Git history, tests, issues and pull requests, this provides an
end-to-end public record of:

- the original natural-language request;
- why the change was needed;
- how the request was interpreted and planned;
- what decisions were made during implementation;
- what tests and scientific validation were performed; and
- how the change reached the released software.

This traceability is particularly important when much of the implementation is
produced through natural-language interactions with AI. It allows the community
to compare the original intent with the final behaviour and to inspect,
question, reproduce or improve the work.

## Data, confidentiality and disclosure

Private, embargoed, personal or collaborator-controlled information must not be
submitted to an AI service unless its use has been authorized and the service’s
storage, training and privacy terms are appropriate.

Researchers must also follow the AI and disclosure policies of their
institution, collaboration, journal or funding body. Where disclosure is
required, it should describe how AI participated in the work and how its
outputs were checked—not merely state that an AI tool was used.

## Responsibility checklist

Before accepting AI-assisted scientific or software work, ask:

- Can I clearly describe in natural language what was done and why?
- Do I understand the scientific assumptions and consequences?
- Can I explain and defend the important decisions?
- Can the result be independently checked or reproduced?
- Have appropriate tests, examples and validation been added?
- Have citations, provenance and licensing been checked?
- Is the development history connected to the original intent?
- Was all information shared with the AI permitted to be shared?

If the answer to any relevant question is no, the work is not yet complete.

## AI statement

This policy was written using natural-language instructions to guide ChatGPT
5.6 Sol. The human author defined the principles, supplied the examples,
evaluated the outputs and iteratively refined the final text, and retains
responsibility for its content.
