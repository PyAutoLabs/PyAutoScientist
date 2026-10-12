"""Opt-in Scientist instance configuration, resolved against the Mind body map.

Loading is read-only and offline. Only explicitly selected organs enter the
public snapshot; local configuration paths never enter it.
"""

import json
import re
from pathlib import Path
from urllib.parse import urlsplit

import yaml


def _text(value, label):
    if not isinstance(value, str) or not value.strip() or any(ord(c) < 32 for c in value):
        raise ValueError(f"{label} must be nonempty single-line text")
    return value


def _pages(value):
    value = _text(value, "pages_url")
    url = urlsplit(value)
    if (url.scheme != "https" or not url.hostname or url.username or url.password
            or url.query or url.fragment or "\\" in value or any(c.isspace() for c in value)):
        raise ValueError("pages_url must be an HTTPS directory URL without credentials, query or fragment")
    return value.rstrip("/") + "/"


def _identity(key, repos):
    _text(key, "repo identity")
    identity = repos.get(key)
    github = identity.get("github") if isinstance(identity, dict) else None
    if not isinstance(github, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", github):
        raise ValueError(f"repo {key}: missing or invalid canonical GitHub identity")
    return github


def load(path, repos_path, theme):
    """Return (public resolved profile, local project configuration path)."""
    path = Path(path)
    config = json.loads(path.read_text(encoding="utf-8"))
    required = {"schema_version", "name", "repo", "pages_url", "projects", "organs"}
    if not isinstance(config, dict) or not required <= set(config) or set(config) - required - {"organ_setup"}:
        raise ValueError("instance profile must declare schema_version, name, repo, pages_url, projects and organs")
    if type(config["schema_version"]) is not int or config["schema_version"] != 1:
        raise ValueError("unsupported instance schema_version")
    body = yaml.safe_load(Path(repos_path).read_text(encoding="utf-8"))
    repos = body.get("repos") if isinstance(body, dict) else None
    if not isinstance(repos, dict):
        raise ValueError("canonical identity map must contain repos")
    name = _text(config["name"], "instance name")
    github = _identity(config["repo"], repos)
    pages_url = _pages(config["pages_url"])
    relative = Path(_text(config["projects"], "projects"))
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("projects must be a relative path within the instance configuration directory")
    projects = path.parent / relative
    if not projects.resolve().is_relative_to(path.parent.resolve()):
        raise ValueError("projects must stay within the instance configuration directory")
    selected = config["organs"]
    family = theme.board_links(pages_url, current="organism")
    if not family:
        raise ValueError("Brain board registry unavailable")
    if not isinstance(selected, dict) or set(selected) - set(family):
        raise ValueError("organs must map canonical Brain organ keys to explicit connections")
    pending = config.get("organ_setup", {})
    if not isinstance(pending, dict) or set(pending) - set(family) or set(pending) & set(selected):
        raise ValueError("organ_setup must contain known, unconnected organ keys")
    setup = []
    for key, connection in pending.items():
        if not isinstance(connection, dict) or set(connection) != {"repo", "pages_url"}:
            raise ValueError(f"organ setup {key}: declare only repo and pages_url")
        github_setup = _identity(connection["repo"], repos)
        setup.append({"key": key, "name": theme.organ(key)["organ"],
                      "role": theme.organ(key)["function"], "repo": github_setup.split("/")[-1],
                      "url": _pages(connection["pages_url"])})
    available = [{"key": key, "name": theme.organ(key)["organ"],
                  "role": theme.organ(key)["function"]} for key in family
                 if key not in selected and key not in pending]
    boards = []
    for key in family:
        if key not in selected:
            continue
        connection = selected[key]
        if (not isinstance(connection, dict) or not {"repo", "pages_url"} <= set(connection)
                or set(connection) - {"repo", "pages_url", "paused"}
                or type(connection.get("paused", False)) is not bool):
            raise ValueError(f"organ {key}: declare repo, pages_url and optional boolean paused")
        organ_github = _identity(connection["repo"], repos)
        boards.append({"key": key, "name": theme.organ(key)["organ"],
                       "role": theme.organ(key)["function"],
                       "repo": organ_github.split("/")[1],
                       "url": _pages(connection["pages_url"]), "paused": connection.get("paused", False)})
    return {"schema_version": 1, "name": name, "repo": github.split("/")[1],
            "source_url": "https://github.com/" + github, "pages_url": pages_url,
            "boards": boards, "setup": setup, "available": available}, projects
