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
an organ. Grey available-to-add capabilities, resumable AI-led activation and
independent deployment are subsequent epic phases.
