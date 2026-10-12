# Upgrade a local Scientist without replacing user records

This procedure selects an existing local Scientist/Brain checkout pair. User
configuration, the canonical Mind map, tasks, research and Broca records stay in
their existing directories. It does not upgrade packages, environments, owner-organ
code, schemas, harness settings or hosted dashboards.

Keep both framework pairs available until recovery is no longer needed. Select
trusted framework code: validation executes its Python scripts. Record fingerprints
are a drift check, not a sandbox or backup against malicious or faulty code.

## Register the current runtime

From a Scientist checkout that contains `scripts/instance_runtime.py`:

```sh
python scripts/instance_runtime.py initialize \
  --manifest /path/to/my-instance/runtime.json \
  --instance /path/to/my-instance/instance.json \
  --repos /path/to/MyMind/repos.yaml \
  --scientist /path/to/scientist-current --brain /path/to/brain-current \
  --protect /path/to/MyMind/active \
  --protect /path/to/research-records --protect /path/to/my-broca-data
```

The command previews the manifest and runs offline profile/project validation.
Review the protected paths and selected revisions, then repeat with `--apply`.
The manifest must be new, its parent must exist, and it must be outside framework
checkouts. Keep it private: it contains local paths. Existing starter instances can
register directly; no reinitialization or profile migration is required.

Framework paths must be clean Git checkout roots with tracked entry points. Exact
commit IDs are recorded for both Scientist and Brain. Tracked modifications and
untracked, nonignored files are refused. Ignored framework files and the Python
environment are not version pins; use trusted, controlled environments.

The profile directory and canonical map are always protected. Add each separate
record directory you need checked with repeated `--protect`. Only declared paths
are covered; research source and task records elsewhere are not implicitly scanned.
The scan streams file contents and records file/directory modes, so large data
trees cost time. `.git` entries are excluded; all other files, including hidden
files, are covered. Symlinks and special files are refused rather than silently
following external data. The runtime manifest itself is excluded from these record
hashes and checked separately. There is no stored copy of protected records.

## Use the selected runtime

```sh
python scripts/instance_runtime.py check --manifest /path/to/my-instance/runtime.json
python scripts/instance_runtime.py render --manifest /path/to/my-instance/runtime.json > preview.html
```

`check` is offline and uses the selected Scientist with the selected Brain.
`render` explicitly requests normal HTML rendering, including configured unpaused
organ feeds. Write its stdout outside protected directories. Both refuse changed
framework pins and detect record changes during execution. The Python interpreter
running this launcher supplies the environment; use the same compatible environment
for validation and normal use. Subprocess execution is capped at 120 seconds.

Direct calls to a different `organism_board.py` do not consult the manifest. Use
this launcher when you want the saved selection to control execution. The launcher
can live in a retained known-good checkout; selected checkouts only need the
existing profile validation and rendering entry point.

## Preview and apply an upgrade

Prepare the candidate Scientist and Brain checkouts separately using normal Git
procedures. This helper does not fetch, pull, checkout, reset or install anything.

```sh
python scripts/instance_runtime.py upgrade \
  --manifest /path/to/my-instance/runtime.json \
  --scientist /path/to/scientist-candidate --brain /path/to/brain-candidate
```

The candidate validates against **current** user configuration. Review the paths,
revisions, protected paths and validation output, then repeat with `--apply`.
Only the manifest changes: its current pair becomes the recovery pair and its
candidate becomes current. An identical selection is a no-op and does not discard
recovery information. Input drift or a write failure stops the switch; temporary
manifest files are removed on ordinary failures. Avoid concurrent edits during
preview/apply. Checks detect changes but are not a multi-user locking protocol.

## Recover without losing newer work

```sh
python scripts/instance_runtime.py rollback --manifest /path/to/my-instance/runtime.json
```

Review, then repeat with `--apply`. The previous pair must still exist at its
recorded revisions and must validate the current profile. Rollback switches the
framework selection; it does **not** restore yesterday's profile, task notes or
measurements. It can recover from a missing or dirty current pair. The two pairs
swap roles after success; only one previous selection is retained.

If newer configuration is incompatible with the previous pair, rollback refuses
and preserves selection/records. Inspect the incompatibility before making manual
changes. If validation changes protected data, the helper reports drift and does
not apply the selection; inspect the affected files and your normal backups. It
never automatically overwrites those files to hide the change.

If the launcher itself is unusable, run its copy from a retained known-good
Scientist checkout. Inspect the private manifest for the previous paths and commits,
verify those checkouts, then use their ordinary offline `--check-instance` command
with explicit `PYAUTO_BRAIN`, `--instance` and `--repos`. A missing/corrupt manifest
can be reconstructed into a **new** manifest with `initialize` after inspecting the
known-good selection; preserve the original file for diagnosis. Do not reset user
records or rerun the starter. This is recovery guidance, not a promise that arbitrary
schema downgrades or environment changes are compatible.

For a fresh chat, provide the private manifest and existing Mind task, and ask the
assistant to inspect the current/previous revisions, validate offline and preview
the intended transition before applying it. Deployment and owner-organ upgrades
remain separate tasks.
