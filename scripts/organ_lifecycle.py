#!/usr/bin/env python3
"""Preview/apply setup or pause Scientist observation; never stop owner jobs."""
import argparse
import json
from pathlib import Path
import stat

import yaml

import connect_organ
import instance_profile
import organism_board
import project_resources


def plan(instance, repos, organ, action, repo=None, pages_url=None):
    instance, repos = Path(instance), Path(repos)
    if instance.is_symlink():
        raise ValueError("instance profile must not be a symlink")
    original, body = instance.read_bytes(), repos.read_bytes()
    config = json.loads(original)
    theme = organism_board.theme()
    _, projects = instance_profile.load(instance, repos, theme)
    project_bytes = projects.read_bytes()
    project_resources.load(projects, repos)
    if organ not in theme.board_links(config["pages_url"], current="organism"):
        raise ValueError("unknown organ key")
    existing = config["organs"].get(organ)
    if action == "resume":
        if existing is None:
            raise ValueError("resume requires a connected organ")
        prepared = connect_organ.plan(instance, repos, organ, existing["repo"], existing["pages_url"], resume=True)
        # Preserve the initial snapshot too; a concurrent identity edit must not
        # silently change which connection this resume was meant to validate.
        if prepared["inputs"] != {instance: original, repos: body, projects: project_bytes}:
            raise ValueError("input changed during resume; rerun preview")
        return prepared
    if action == "setup":
        if existing is not None:
            raise ValueError("organ is already connected")
        instance_profile._identity(repo, yaml.safe_load(body)["repos"])
        connection = {"repo": repo, "pages_url": instance_profile._pages(pages_url)}
        pending = config.setdefault("organ_setup", {})
        if organ in pending and pending[organ] != connection:
            raise ValueError("conflicting setup; review existing identity manually")
        changed = organ not in pending
        pending[organ] = connection
    elif action == "pause":
        if existing is None:
            raise ValueError("pause requires a connected organ")
        changed = not existing.get("paused", False)
        existing["paused"] = True
    else:
        raise ValueError("action must be setup, pause or resume")
    return {"instance": instance, "inputs": {instance: original, repos: body, projects: project_bytes},
            "mode": stat.S_IMODE(instance.stat().st_mode), "changed": changed,
            "replacement": (json.dumps(config, indent=2, ensure_ascii=False) + "\n").encode()}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["setup", "pause", "resume"])
    parser.add_argument("--instance", type=Path, required=True)
    parser.add_argument("--repos", type=Path, required=True)
    parser.add_argument("--organ", required=True)
    parser.add_argument("--repo")
    parser.add_argument("--pages-url")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    if args.action != "setup" and (args.repo is not None or args.pages_url is not None):
        parser.error("pause/resume use the existing connection identity")
    try:
        prepared = plan(args.instance, args.repos, args.organ, args.action, args.repo, args.pages_url)
        connect_organ._unchanged(prepared)
        if args.apply:
            print("Updated" if connect_organ.apply(prepared) else "Unchanged")
        else:
            print("Preview only; pass --apply to save" if prepared["changed"] else "Unchanged")
        print(prepared["replacement"].decode())
        print("Pause controls Scientist observation only; owner jobs and services are unaffected.")
    except (OSError, ValueError, RuntimeError, yaml.YAMLError) as exc:
        parser.exit(2, f"organ-lifecycle: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
