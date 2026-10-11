# Start a Scientist dashboard with your own identity

This is the first slice of the independent starter: an empty dashboard with a
name, its own repository identity and explicit organ connections. It needs
Python, PyYAML and a pinned PyAutoBrain checkout for shared presentation. It
requires no science libraries, assistant repository or organ service.

This local preview does not initialize a working Mind, install an agent harness,
provision repositories, activate organs or publish a site. Those remain later
starter steps. Existing projects keep their own source and records.

## Try the empty preview

From this repository, with Brain beside it (or `PYAUTO_BRAIN` set to its checkout):

```bash
python -m pip install pyyaml
python scripts/organism_board.py --instance examples/starter/instance.json \
  --repos examples/starter/repos.yaml --check-instance
python scripts/organism_board.py --instance examples/starter/instance.json \
  --repos examples/starter/repos.yaml --html > starter.html
```

Open `starter.html` locally. The fictitious **Mira Scientist** has no projects or
connected organs. Rendering and opening this empty page fetch no organ feeds.
The example GitHub identity and `example.invalid` address are placeholders,
not repositories or a deployed service. This example body map is a fixture,
not a complete Mind installation.

## Initialize a user-owned configuration directory

If you already have a canonical Mind `repos.yaml`, the offline initializer saves
copying the preview files by hand. Add your Scientist repository identity to that
map first. Use an intended HTTPS Pages address; it need not be deployed yet.
From the framework checkout:

```bash
python scripts/starter.py /path/to/new-instance --repos /path/to/Mind/repos.yaml \
  --name "My Scientist" --repo my-scientist \
  --pages-url https://example.invalid/my-scientist/
```

This prints the file plan without writing. Repeat with `--apply` to create
`instance.json`, empty `projects.json` and `SETUP.md`. The destination's parent
must exist; the destination itself must not exist, even as an empty directory or
symlink. An existing instance is resumed, never initialized again. No `--force`
is provided. If a filesystem error interrupts writing, inspect the partial
new directory; the command will refuse to overwrite it on retry.

`SETUP.md` records local validation commands and a fresh-chat handoff. Keep it
private: it contains paths to your framework and canonical map. It is an ordinary
local note, not an installed agent skill. Moving either checkout or configuration
requires updating these paths. No body map is copied, no remote access is checked,
and no task or knowledge records, project source, harness settings or repositories
are created. Mind/Memory template setup and harness integration remain separate.
Use the existing supported templates for those, rather than copying live records.

## Configure your instance

Copy the example configuration to a directory you own, outside the framework
checkout. Set `name`, `repo` and `pages_url`. `repo` is a stable ID in your
canonical Mind `repos.yaml`; its `github` field supplies the repository home.
`pages_url` is the explicit HTTPS directory where you intend to publish this
Scientist, including any custom path. Naming is independent of framework organ
keys and repository names.

The required `projects` field names a file relative to the profile directory.
Start with the empty project file. Supplying `--instance` never falls back to
this repository's live project configuration. Use `--projects` only when you
intentionally want to override the profile's file. Keep this configuration and
your records when updating the framework; this change neither migrates nor
rewrites them. A supported upgrade procedure remains future work.

Omitting `--instance` retains the existing PyAutoLabs-compatible dashboard path.
The current Actions publishing workflow still uses that path; this local preview
does not configure independent-instance deployment.

## Connect an existing project

Give your coding assistant this request in the local checkout:

> Read STARTER.md, PROJECTS.md and my instance profile. Help connect one existing
> project. First inspect its current source and any existing Scientist records.
> Ask me for its purpose, canonical repository identity and intended visibility
> if these are not available. Reuse my Mind body map and explicit project/resource
> relationships; do not copy source material or assume an assistant exists.
> Explain the proposed configuration changes before applying them. Validate the
> profile and relationships offline, then show me a local dashboard preview.
> Do not create repositories, publish, change access or run science as part of
> connecting the project. Suggest optional organs only when they serve a concrete
> need; setup and activation remain separate steps.

Add canonical repository identities in your Mind body map, then configure
resources and projects as described in [PROJECTS.md](PROJECTS.md). Projects and
resources are private by default; only explicit `public: true` entries appear in
the publication snapshot. Do not enter private URLs into public connections.
A project may have no assistant and may share dependencies with other projects.

## Connect an already available organ

`organs` maps Brain's stable organ keys to explicit canonical identities and
published board directories. For example, after your own Mind board exists:

```json
"organs": {
  "mind": {
    "repo": "research-plans",
    "pages_url": "https://research.example/boards/plans/"
  }
}
```

`research-plans` must be an entry in your body map with its actual GitHub home.
The board's `state.json` must use `organ: "mind"` and the repository name from
that GitHub identity. Connection order follows Brain's shared registry; only
selected organs are collected, displayed and linked in the footer. A connected
organ with a missing or invalid feed remains visible as unavailable. An omitted
organ is unconfigured, not failed. Empty `organs: {}` is supported.

Connections are an explicit choice of public feed locations. Adding a connection
reads that feed during rendering and browser refresh; it never installs or runs
an organ. Grey available-to-add project resources are described below. Resumable organ
activation and independent deployment remain subsequent epic phases.

### Validate a connection before saving it

For an organ that already has a public dashboard, use the connection helper.
First register its actual repository identity in your Mind map. For example,
`my-guides` may identify your independently named Broca repository; `broca`
remains the framework organ key. Supply the actual board URL, not a guessed
repository-name suffix:

```sh
PYAUTO_BRAIN=/path/to/PyAutoBrain python scripts/connect_organ.py \
  --instance /path/to/instance/instance.json --repos /path/to/Mind/repos.yaml \
  --organ broca --repo my-guides --pages-url https://research.example/guides/
```

This previews the connection after checking the existing instance/projects and
reading only the selected board's `state.json`. The feed must match Brain's state
contract, organ key, canonical repository name and board URL. The command checks
declared identity, not repository access or ownership. Repeat with `--apply` to
validate again and save the connection. A valid red or old feed can be connected:
the command reports its status and timestamp, not a healthy/ready verdict.

Failed validation leaves the profile unchanged. Fix the missing prerequisite
and rerun the same command; no reinitialization is needed. An identical connection
is a no-op after validation. A different existing connection is refused for
manual review. The helper atomically replaces only `instance.json`, preserves its
permissions and other configuration, and refuses input changes detected during
validation. Avoid concurrent manual edits while applying. Projects, canonical
identities, research records and organ source remain untouched.

Once connected, missing or stale evidence stays visible as evidence trouble;
it does not turn the organ back into an unconfigured capability. This step does
not create an organ, publish it, configure upkeep, or validate its scientific or
communication quality. Broca's project-owned guides/workspaces and separate
assistants retain their own source; connecting Broca copies none of them.

To resume with an AI assistant:

> Read my profile, canonical map and existing Mind task first. Resume the selected
> organ connection using connect_organ.py. Ask only for missing repository identity
> or the public board URL. Preview and explain the change before applying it.
> If the organ or its feed is not ready, keep setup incomplete in this Mind task;
> do not invent a feed or mark it connected. Preserve all existing records and
> report connection validation separately from readiness. Do not create or publish
> anything without its own approved setup task.

Organ provisioning, resumable owner-specific setup, pause controls and deployment
are later activation phases. This helper covers the validated connection boundary.

## Discover what a project can add

The separate `examples/connected-project/` fixture shows **Mira Scientist** with
one fictional software resource, no connected assistant or organs, and optional
resources such as `spectra_workspace` and `spectra_inference`:

```bash
python scripts/organism_board.py --instance examples/connected-project/instance.json \
  --repos examples/connected-project/repos.yaml --html > connected-project.html
```

Expand Spectra, then a grey **Available to add** row to select its setup prompt.
Names are suggestions in instance configuration, not detected repositories.
Choose opportunities explicitly when connecting your project; see
[PROJECTS.md](PROJECTS.md#available-to-add). The empty starter stays empty.
These prompts begin a setup conversation; they do not run setup or activate organs.
