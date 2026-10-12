#!/usr/bin/env python3
"""Preview or connect an already prepared organ; validate before changing records."""

import argparse
import json
import os
from pathlib import Path
import stat
import tempfile

import yaml

import instance_profile
import organism_board
import project_resources


def plan(instance, repos, organ, repo, pages_url, *, resume=False):
    """Return validated replacement bytes and input snapshots, without writing.

    A connection is a location/contract check, never installation or a health
    verdict. Even an identical retry checks current evidence before reporting OK.
    """
    instance, repos = Path(instance), Path(repos)
    if instance.is_symlink():
        raise ValueError("instance profile must not be a symlink")
    original = instance.read_bytes()
    body_bytes = repos.read_bytes()
    config = json.loads(original)
    theme = organism_board.theme()
    _, projects = instance_profile.load(instance, repos, theme)
    project_bytes = projects.read_bytes()
    project_resources.load(projects, repos)
    family = theme.board_links(config["pages_url"], current="organism")
    if organ not in family:
        raise ValueError("organ must be a canonical Brain organ key")
    github = instance_profile._identity(repo, yaml.safe_load(body_bytes)["repos"])
    connection = {"repo": repo, "pages_url": instance_profile._pages(pages_url)}
    existing = config["organs"].get(organ)
    pending = config.get("organ_setup", {}).get(organ)
    if existing is not None and existing.get("paused", False) and not resume:
        raise ValueError("organ observation is paused; use explicit lifecycle resume")
    if existing is not None or pending is not None:
        prior = existing if existing is not None else pending
        normalized = {"repo": prior["repo"], "pages_url": instance_profile._pages(prior["pages_url"])}
        if normalized != connection:
            raise ValueError("organ already has a different connection; review it manually")

    from _state import validate_state  # theme() selects the matching Brain checkout.

    feed = json.loads(organism_board._get(connection["pages_url"] + "state.json"))
    errors = validate_state(feed)
    if errors:
        raise ValueError("invalid organ feed: " + "; ".join(errors))
    if feed["organ"] != organ or feed["repo"] != github.split("/")[1]:
        raise ValueError("organ feed identity does not match the selected organ/repository")
    if instance_profile._pages(feed["pages_url"]) != connection["pages_url"]:
        raise ValueError("organ feed pages_url does not match the selected location")

    config["organs"][organ] = connection
    if pending is not None:
        del config["organ_setup"][organ]
    return {
        "instance": instance,
        "inputs": {instance: original, repos: body_bytes, projects: project_bytes},
        "mode": stat.S_IMODE(instance.stat().st_mode),
        "replacement": (json.dumps(config, indent=2, ensure_ascii=False) + "\n").encode(),
        "changed": existing is None or bool(existing.get("paused", False)),
        "organ": organ,
        "connection": connection,
        "status": feed["status"],
        "updated": feed["updated"],
    }


def _unchanged(prepared):
    if prepared["instance"].is_symlink():
        raise ValueError("instance profile became a symlink; rerun the preview")
    for path, original in prepared["inputs"].items():
        if path.read_bytes() != original:
            raise ValueError(f"input changed during validation: {path}; rerun the preview")


def apply(prepared):
    """Preserve existing records on validation/write failure; replace one file."""
    _unchanged(prepared)
    if not prepared["changed"]:
        return False
    path = prepared["instance"]
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".connect-organ-", delete=False) as stream:
            temporary = Path(stream.name)
            os.fchmod(stream.fileno(), prepared["mode"])
            stream.write(prepared["replacement"])
            stream.flush()
            os.fsync(stream.fileno())
        _unchanged(prepared)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance", type=Path, required=True)
    parser.add_argument("--repos", type=Path, required=True)
    parser.add_argument("--organ", required=True, help="stable Brain organ key, e.g. broca")
    parser.add_argument("--repo", required=True, help="repository key in the canonical identity map")
    parser.add_argument("--pages-url", required=True, help="explicit public HTTPS board directory")
    parser.add_argument("--apply", action="store_true", help="connect after validation; default previews only")
    args = parser.parse_args(argv)
    try:
        prepared = plan(args.instance, args.repos, args.organ, args.repo, args.pages_url)
        _unchanged(prepared)
        if args.apply:
            changed = apply(prepared)
            print("Connected" if changed else "Already connected", args.organ)
        else:
            print("Preview only; pass --apply to connect" if prepared["changed"] else "Already connected; no change")
        print(json.dumps({args.organ: prepared["connection"]}, indent=2))
        print(f"Feed: {prepared['status']} · updated {prepared['updated']}")
        print("Connection validated; organ readiness and freshness remain with its owner.")
    except (OSError, ValueError, RuntimeError, yaml.YAMLError) as exc:
        parser.exit(2, f"connect-organ: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
