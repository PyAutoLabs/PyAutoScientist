#!/usr/bin/env python3
"""Initialize user-owned Scientist configuration; offline and non-overwriting."""

import argparse
import json
import shlex
from pathlib import Path

import yaml

from instance_profile import _identity, _pages, _text


def plan(destination, repos_path, name, repo, pages_url):
    """Validate inputs without writing, and return the complete file plan."""
    destination = Path(destination).absolute()
    if destination.exists() or destination.is_symlink():
        raise ValueError("destination already exists; keep its records and resume from SETUP.md")
    if not destination.parent.is_dir():
        raise ValueError("destination parent must already be a directory")
    repos_path = Path(repos_path).resolve(strict=True)
    body = yaml.safe_load(repos_path.read_text(encoding="utf-8"))
    repos = body.get("repos") if isinstance(body, dict) else None
    if not isinstance(repos, dict):
        raise ValueError("canonical identity map must contain repos")
    _identity(repo, repos)
    profile = {"schema_version": 1, "name": _text(name, "instance name"),
               "repo": repo, "pages_url": _pages(pages_url),
               "projects": "projects.json", "organs": {}}
    framework = Path(__file__).resolve().parents[1]
    command = shlex.join(["python3", str(framework / "scripts/organism_board.py"),
                          "--instance", str(destination / "instance.json"),
                          "--repos", str(repos_path)])
    setup = f"""# Resume this Scientist setup

This directory is user-owned configuration, not a full Scientist installation.
Keep it when upgrading the framework. Do not rerun initialization here or replace
these records with the examples. No organ is connected and no project is assumed.
The intended Pages address is configuration only; nothing has been published.

## Fresh-chat handoff

Open a coding-assistant session in this directory and ask:

> Read SETUP.md and instance.json, then inspect projects.json and the canonical
> repository map named below. Validate offline before suggesting changes. Help
> connect one existing project using the framework's PROJECTS.md and STARTER.md.
> Ask for missing project identity, purpose and visibility. Preserve project-owned
> source; do not assume an assistant exists. Propose changes before applying them.
> Do not provision repositories, install a harness, publish or run science.

The commands below retain local paths, so keep this file private. If you move the
configuration, framework or Mind checkout, update the command paths before use.
The canonical map is referenced, never copied or rewritten by initialization.

## Validate and preview

Ensure Python and PyYAML are available and set PYAUTO_BRAIN to your compatible
Brain checkout (shared presentation). The initializer itself does not need Brain.
Run validation, then render to a new scratch file of your choice:

```sh
{command} --check-instance
{command} --html
```

The second command prints HTML to stdout; save it outside this directory and open
it locally. An empty instance reads no organ feeds. Configuring an organ later
explicitly opts into reading its public feed.

## Still to set up

- A working Mind from the supported fresh-slate template, with your own body map
  and empty task records. This command assumes an existing canonical map only.
- Optional Memory from its supported template when knowledge needs a home.
- One supported local agent harness and its workflow integration; no global agent
  settings or skills were installed here.
- Existing-project connection, optional organ activation and independent hosting.

Consult the framework STARTER.md for current boundaries. Local instructions are
not evidence that a harness or organ has been installed or tested.
"""
    return {"instance.json": json.dumps(profile, indent=2, ensure_ascii=False) + "\n",
            "projects.json": json.dumps({"schema_version": 1, "resources": {}, "projects": {}}, indent=2) + "\n",
            "SETUP.md": setup}


def initialize(destination, files):
    """Exclusively create a new directory; never merge into existing state."""
    destination = Path(destination)
    destination.mkdir()  # Atomic refusal if another invocation got there first.
    for name, content in files.items():
        with (destination / name).open("x", encoding="utf-8") as stream:
            stream.write(content)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--repos", type=Path, required=True, help="existing canonical Mind repos.yaml")
    parser.add_argument("--name", required=True)
    parser.add_argument("--repo", required=True, help="stable ID in the canonical map")
    parser.add_argument("--pages-url", required=True, help="intended HTTPS board directory")
    parser.add_argument("--apply", action="store_true", help="create the new directory (default: preview only)")
    args = parser.parse_args(argv)
    try:
        files = plan(args.destination, args.repos, args.name, args.repo, args.pages_url)
        if args.apply:
            initialize(args.destination, files)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        parser.exit(2, f"starter: {exc}\n")
    print("Created" if args.apply else "Preview only; pass --apply to create", args.destination)
    for name in files:
        print(f"  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
