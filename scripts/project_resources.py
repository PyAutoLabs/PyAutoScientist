"""Versioned, instance-owned project relationships; no collection or execution.

Repository identities come only from the supplied Mind body map. The output is
a publication projection: private/unapproved entries never enter the snapshot.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.parse import quote, urlsplit

import yaml


RELATIONS = {
    "software": "Software",
    "dependencies": "Shared dependencies",
    "workspaces": "Workspaces",
    "tutorials": "Tutorials",
    "documentation": "Documentation",
    "assistants": "Assistants",
    "records": "Organ records",
}
KINDS = {"software_family": "Software family", "scientific_project": "Scientific investigation"}
ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be nonempty text")
    return value


def _https(value):
    value = _text(value, "published_url")
    url = urlsplit(value)
    if (url.scheme != "https" or not url.hostname or url.username or url.password
            or "\\" in value or any(c.isspace() or ord(c) < 32 for c in value)):
        raise ValueError("published_url must be an absolute HTTPS URL without credentials")
    return value


def _entries(value, label):
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object keyed by stable IDs")
    for key, item in value.items():
        if not ID.fullmatch(key) or not isinstance(item, dict):
            raise ValueError(f"invalid {label} ID or entry")
        _text(item.get("name"), f"{label} name")
        if "public" in item and type(item["public"]) is not bool:
            raise ValueError(f"{label} public must be boolean")
    return value


def resolve(config: dict, body_map: dict) -> dict:
    """Resolve explicit relationships without inferring projects from repo names."""
    if not isinstance(config, dict) or type(config.get("schema_version")) is not int or config["schema_version"] != 1:
        raise ValueError("unsupported project configuration schema_version")
    if set(config) - {"schema_version", "resources", "projects"}:
        raise ValueError("unknown project configuration field")
    repos = body_map.get("repos") if isinstance(body_map, dict) else None
    if not isinstance(repos, dict):
        raise ValueError("canonical identity map must contain repos")
    resources = _entries(config.get("resources", {}), "resource")
    projects = _entries(config.get("projects", {}), "project")
    resolved = {}
    for key, item in resources.items():
        if set(item) - {"name", "public", "repo", "path", "ref", "published_url"}:
            raise ValueError(f"resource {key}: unknown field")
        links = []
        if "repo" in item:
            _text(item["repo"], "repo")
            identity = repos.get(item["repo"])
            if not isinstance(identity, dict):
                raise ValueError(f"resource {key}: unknown canonical repository")
            remote = identity.get("github")
            if not isinstance(remote, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", remote):
                raise ValueError(f"resource {key}: invalid canonical GitHub identity")
            url = f"https://github.com/{remote}"
            if "path" in item or "ref" in item:
                path = item.get("path", "")
                ref = item.get("ref", "main")
                if (not isinstance(path, str) or path.startswith("/") or "\\" in path
                        or any(p in (".", "..") for p in path.split("/"))
                        or any(ord(c) < 32 for c in path)):
                    raise ValueError(f"resource {key}: invalid repository-relative path")
                _text(ref, "ref")
                if ref in (".", "..") or "\\" in ref or any(c.isspace() or ord(c) < 32 for c in ref):
                    raise ValueError(f"resource {key}: invalid revision")
                url += "/tree/" + quote(ref, safe="")
                if path:
                    url += "/" + quote(path, safe="/")
            links.append({"label": "Source", "url": url})
        elif "path" in item or "ref" in item:
            raise ValueError(f"resource {key}: path/ref requires repo")
        if "published_url" in item:
            links.append({"label": "Published", "url": _https(item["published_url"])})
        if not links:
            raise ValueError(f"resource {key}: repo or published_url required")
        resolved[key] = {"id": key, "name": item["name"], "links": links}

    public_projects = []
    for key, item in projects.items():
        if set(item) - {"name", "public", "kind", "description", "resources"}:
            raise ValueError(f"project {key}: unknown field")
        if not isinstance(item.get("kind"), str) or item["kind"] not in KINDS:
            raise ValueError(f"project {key}: unknown project kind")
        relations = item.get("resources", {})
        if not isinstance(relations, dict) or set(relations) - RELATIONS.keys():
            raise ValueError(f"project {key}: unknown resource relationship")
        groups = []
        for relation, label in RELATIONS.items():
            ids = relations.get(relation, [])
            if (not isinstance(ids, list) or any(not isinstance(i, str) for i in ids)
                    or len(ids) != len(set(ids))):
                raise ValueError(f"project {key}: relationships must be unique ID lists")
            if any(i not in resources for i in ids):
                raise ValueError(f"project {key}: unknown resource reference")
            visible = [resolved[i] for i in ids if resources[i].get("public") is True]
            if visible:
                groups.append({"relation": relation, "label": label, "resources": visible})
        description = item.get("description", "")
        if not isinstance(description, str):
            raise ValueError(f"project {key}: description must be text")
        if item.get("public") is True:
            public_projects.append({"id": key, "name": item["name"], "kind": item["kind"],
                                    "description": description, "groups": groups})
    return {"schema_version": 1, "projects": public_projects}


def load(config_path: Path, repos_path: Path) -> dict:
    return resolve(json.loads(config_path.read_text(encoding="utf-8")),
                   yaml.safe_load(repos_path.read_text(encoding="utf-8")))


def render_markdown(snapshot: dict) -> str:
    def text(value):
        return re.sub(r"([\\\[\]*_`#|])", r"\\\1", html.escape(value)).replace("\n", " ")

    lines = ["## Projects", "", "Connected resources; inventory is not a quality or readiness verdict."]
    for project in snapshot.get("projects", []):
        lines.extend(["", "### " + text(project["name"]), "", text(project["description"])])
        for group in project["groups"]:
            for resource in group["resources"]:
                links = " · ".join(f"[{text(link['label'])}]({quote(link['url'], safe='/:?=&%+#@~;,-_')})"
                                   for link in resource["links"])
                lines.append(f"- {text(group['label'])}: {text(resource['name'])} — {links}")
    return "\n".join(lines)


def render_html(snapshot: dict) -> str:
    esc = html.escape
    cards = []
    for project in snapshot.get("projects", []):
        groups = []
        for group in project["groups"]:
            entries = []
            for resource in group["resources"]:
                links = " · ".join(f'<a href="{esc(link["url"], quote=True)}">{esc(link["label"])}</a>'
                                   for link in resource["links"])
                entries.append(f'<li data-resource="{esc(resource["id"])}"><span>{esc(resource["name"])}</span> — {links}</li>')
            groups.append(f'<div class="summary-row"><dt>{esc(group["label"])}</dt><dd><ul>{"".join(entries)}</ul></dd></div>')
        content = f'<dl>{"".join(groups)}</dl>' if groups else '<p>No public resources configured.</p>'
        cards.append(f'''<details class="organ-card project-card" id="project-{esc(project['id'])}">
<summary><span>{esc(project['name'])}</span><span class="organ-status">{esc(KINDS[project['kind']])}</span></summary>
<div class="organ-content"><p>{esc(project['description'])}</p>{content}</div></details>''')
    empty = '<p>No public projects configured.</p>' if not cards else ''
    return f'''<section id="projects" aria-labelledby="projects-heading"><h2 id="projects-heading">Projects</h2>
<p>Connected resources. Follow the source links for current records; listed resources do not establish quality or readiness.</p>
{empty}<div class="organ-grid" aria-label="Project resources">{''.join(cards)}</div></section>'''
