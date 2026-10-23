# PyAutoLabs AI Options

Every PyAutoLabs science assistant runs inside an **AI coding agent**: a tool that reads the assistant
repository, runs Python on your computer and looks at the results. That is what lets the assistant install
the software, plot your data, run fits and check the figures they produce. You do not have to run anything
to use it. Asking questions, planning an analysis and learning in Teacher Mode happen in the same agent.

This page covers every assistant. Pick an agent below, then go back to your assistant's README for its
starting prompt.

| Assistant | Repository | Library |
|-----------|------------|---------|
| PyAutoLens Assistant | [autolens_assistant](https://github.com/PyAutoLabs/autolens_assistant) | strong gravitational lensing |
| PyAutoGalaxy Assistant | [autogalaxy_assistant](https://github.com/PyAutoLabs/autogalaxy_assistant) | galaxy morphology and structure |
| PyAutoFit Assistant | [autofit_assistant](https://github.com/PyAutoLabs/autofit_assistant) | probabilistic model fitting |
| PyAutoCTI Assistant | [autocti_assistant](https://github.com/PyAutoLabs/autocti_assistant) | charge transfer inefficiency |

**The short version.** Claude Code and Codex are recommended and both are paid. GitHub Copilot CLI and
OpenCode are free ways to try an assistant. A browser chat with a GitHub connector is good for reading and
discussion, but it cannot run code. Prices and quotas below are as of October 2026; check the linked
provider pages, because they change often.

In the commands below, replace `<assistant>` with the repository name from the table, for example
`autolens_assistant`.

## Claude Code (recommended, paid)

Claude Code is Anthropic's coding agent. It runs in the terminal, a desktop app and IDE extensions. It
reads the assistant's `AGENTS.md` instructions and registers the code-gate hook from the project settings
(`.claude/settings.json`). The hook blocks stale library API written from memory before it runs.

**What you need.** A Claude subscription (Pro or Max, or a Team or Enterprise seat), usage billing through
the Claude Console, or a cloud provider your institution already uses (Amazon Bedrock, Google Cloud,
Microsoft Foundry). See Anthropic's [cost page](https://code.claude.com/docs/en/costs). Sustained science
is heavy use, so budget for it.

**Install and sign in.** Follow [code.claude.com/docs](https://code.claude.com/docs). Then:

```bash
git clone https://github.com/PyAutoLabs/<assistant>.git
cd <assistant>
claude
```

The assistant configures itself on your first prompt and installs its library if it is missing.

**Start from any directory.** Cloning first is optional. Open Claude Code in any folder, even an empty one,
and paste your assistant's starting prompt. The prompt names the repository, so the agent clones it, reads
`AGENTS.md` and installs the library. Approve the `git clone` and `pip install` requests. Hooks and project
settings only load when Claude Code is launched inside the folder, so in that session the agent checks its
code against the installed library by hand. Relaunch `claude` inside the cloned folder for the full setup.

**Tested coverage.** Claude Code is the most thoroughly exercised agent. The assistants are developed in it,
and it has run them end to end, from installing the library to fits and HPC workflows.

## Codex (recommended, paid)

Codex is OpenAI's coding agent (CLI, IDE extension and cloud). It reads the shared `AGENTS.md`
instructions. Each assistant exposes its `skills/` through generated `.codex/skills/` adapters, and the
tracked `.codex/hooks.json` registers the code gate.

**What you need.** Codex is included in ChatGPT plans, and the Free plan lists it for quick coding tasks
([pricing](https://learn.chatgpt.com/docs/pricing)). As of October 2026, CLI access on Free is not
confirmed and Free limits are unpublished. For sustained science, plan on Plus or above, or API billing.

**Install and sign in.** Follow [developers.openai.com/codex](https://developers.openai.com/codex). Then:

```bash
git clone https://github.com/PyAutoLabs/<assistant>.git
cd <assistant>
codex
```

After cloning, and after any change to the hooks, run `/hooks` and trust the current hash of
`.codex/hooks.json`. Codex skips project hooks until you do. For local development setup, use
`source activate.sh`.

**Start from any directory.** Open Codex in any folder and paste your assistant's starting prompt. The
default sandbox blocks network access, and the clone and install need it. Approve the network request when
Codex asks, or start it with network enabled:
`codex --sandbox workspace-write -c sandbox_workspace_write.network_access=true`.
Codex reads `AGENTS.md` and registers hooks only at launch, so relaunch `codex` inside the cloned folder
for the full setup.

**Tested coverage.** Codex discovery and the safety adapters are checked with an installed Codex CLI, and
guard tests cover the setup. Full science fits still need to be exercised in your own environment. The
[harness smoke record](https://github.com/PyAutoLabs/PyAutoBrain/blob/main/docs/agent_harness_smoke.md)
describes the measured scope.

## Free options

Every free route is for trying the assistant, not sustained science: quotas are small and free models
change without notice. Both routes below are supported and documented, but not benchmarked against the
assistants. Neither has a hook system the assistants use, so the code gate is self-enforced: the assistant
should run its `autoassistant/audit_skill_apis.py` check on generated code before executing it. If it
skips this, ask it to.

### GitHub Copilot CLI

**What is free.** Every Copilot plan includes Copilot CLI, including Copilot Free
([plans](https://docs.github.com/en/copilot/get-started/plans)). Copilot Free gives an allowance of GitHub
AI Credits (the amount is unpublished) and automatic model selection only. Verified students get the
Copilot Student plan at no cost, also with automatic model selection
([GitHub Education](https://github.com/education/students)). Many researchers already have Copilot access
through GitHub Education or their institution.

**Install.** See [Installing GitHub Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli).
For example `npm install -g @github/copilot`, `brew install --cask copilot-cli`, or
`curl -fsSL https://gh.io/copilot-install | bash`. Then:

```bash
git clone https://github.com/PyAutoLabs/<assistant>.git
cd <assistant>
copilot
```

On first launch, run `/login` if prompted.

**Caveats.** You cannot choose the model on Free or Student, so quality varies from session to session.
Copilot CLI is expected to read `AGENTS.md`; tell it to read `AGENTS.md` in full if it does not.

### OpenCode

**What is free.** [OpenCode](https://opencode.ai/docs/) is an open-source (MIT) coding agent. The client
is free and the model is a separate choice. Its hosted provider, [OpenCode Zen](https://opencode.ai/docs/zen/),
listed 13 free models in October 2026 (for example Big Pickle, GLM-5.3-Flash Free and DeepSeek V4.1 Flash
Free). All are described as free for a limited time. Zen's setup asks you to add billing details before
copying your API key, so a card may be requested even for free models. Any other provider key also works,
including a paid Claude or OpenAI key.

**Install.**

```bash
curl -fsSL https://opencode.ai/install | bash
git clone https://github.com/PyAutoLabs/<assistant>.git
cd <assistant>
opencode
```

Run it from the repository root so it reads `AGENTS.md`.

**Caveats.** Pick a model that supports tool use and image input; check the model card, not the name.
Many free models have no vision input, so the assistant cannot check its own figures, and every fit check
involves looking at a PNG. A quick test: ask it to plot the dataset and describe what it sees. A model
that cannot view the figure will describe the code instead.

If you try a free route, please open an issue on the assistant's repository with the agent, model, date
and what worked or failed.

## Troubleshooting

Known failure modes in any coding agent. If you hit something else, open an issue on the assistant's
repository.

**It wrote API that no longer exists** (for example `aplt.FitImagingPlotter(...)` or `aplt.MatPlot2D(...)`).
Older library versions dominate model training data. On Claude Code and Codex the code gate blocks this.
Elsewhere, ask it to re-read the relevant skill, rewrite the code, and run
`python autoassistant/audit_skill_apis.py --file <script>` before executing. If it keeps happening, start a
fresh session in the repository root so `AGENTS.md` loads again.

**It answered an API question without opening any file.** Ask it to name the `skills/` or `wiki/core/`
page it read. An answer from memory is the failure the assistants are designed to prevent.

**It started a fit on real data without plotting it.** The real-data gate is not optional. Tell it to stop,
plot the data, show you the path and settle the mask and any contaminants with you first.

**`audit_skill_apis.py --check-version` exits non-zero at session start.** Exit 1 is API drift between the
documented and installed library: follow the audit skill, usually by installing the pinned version. Exit 2
or 3 means the library is missing or broken in the interpreter the agent uses: let the assistant install it.

**Cache or permission errors from numba or matplotlib in a sandbox.** Prefix runs with
`NUMBA_CACHE_DIR=/tmp/numba_cache MPLCONFIGDIR=/tmp/matplotlib`.

**It ran out of context, or got slow and vague.** Something large was pulled in, such as
`wiki/literature/` or `llms-full.txt`. Start a fresh session and ask it to read single pages only.

**It stopped mid-task, or switched to a weaker model.** You hit your plan's usage window. A subscription
tells you when it resets; with usage billing, check your spend controls.

**The model cannot see figures, or skips the audit step.** That is a model limitation, common on free
models. Switch to a model with image input and reliable tool use.

## Colab notebooks and the assistant

Google Colab has no agentic mode, so it cannot run an assistant. Where an assistant ships a Colab notebook,
it is the "see the code" route: the same analysis written out with explanation, for learning the library
API. The assistant is the "do it in conversation" route.

## Chat instead of an agent

Claude.ai and ChatGPT can attach an assistant repository through their GitHub connector. They read the
repository well and see its current content, so they are good for questions, planning, learning and
discussing papers. They cannot run code or look at your data, so there are no fits, no figure checks and no
check of the API against the installed library. Use chat for discussion, not for fits.

- **Claude.ai.** The [GitHub integration](https://claude.com/docs/connectors/github) is available on every
  plan, including Free. It reads file names and contents of attached repositories.
- **ChatGPT.** The GitHub connector is on paid plans (Plus, Pro, Team, Enterprise).

Connect GitHub under **Settings, Connectors**, attach the assistant repository, then start with a prompt
like this (replace `<assistant>`):

```text
Use the <assistant> repository: https://github.com/PyAutoLabs/<assistant>

Start by reading its front door:
https://raw.githubusercontent.com/PyAutoLabs/<assistant>/main/llms.txt

Follow its read order and its API rules. First tell me whether you can actually read
llms.txt. If you can't, say so plainly and don't answer from memory.
```

Naming `llms.txt` explicitly matters: connectors do not reliably find it on their own. The last sentence is
an honesty check, so you know at once if the chat cannot read the repository.

## Not recommended

Gemini CLI's free and consumer access ended on 2026-06-18
([announcement](https://github.com/google-gemini/gemini-cli/discussions/27274)) and its successor,
Antigravity CLI, has a small unpublished free quota; if you already use it, it loads `AGENTS.md`, but it is
not a supported route.
