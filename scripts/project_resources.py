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
    "profiling": "Profiling",
    "inference": "Inference",
    "visualization": "Visualization",
    "tests": "Workspace tests",
    "records": "Organ records",
}
KINDS = {"software_family": "Software family", "scientific_project": "Scientific investigation"}
CAPABILITIES = {
    "workspaces": "Examples and working scripts for this project.",
    "tutorials": "Step-by-step teaching material.",
    "documentation": "Reference and usage guides.",
    "assistants": "A project-specific research assistant.",
    "tests": "Regression and smoke-test workspaces.",
    "profiling": "Measure runtime and resource use.",
    "inference": "Compare inference methods and results.",
    "visualization": "Review figures and visualization outputs.",
}
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
    if set(config) - {"schema_version", "resources", "projects", "routes"}:
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
        if "repo" in item:
            resolved[key].update(repo=item["repo"], github=repos[item["repo"]]["github"])

    routes = config.get("routes", {})
    if not isinstance(routes, dict) or set(routes) - RELATIONS.keys():
        raise ValueError("routes must map known relationships to dashboard resource IDs")
    for relation, key in routes.items():
        if not isinstance(key, str) or key not in resources:
            raise ValueError(f"route {relation}: unknown dashboard resource")
        if "published_url" not in resources[key]:
            raise ValueError(f"route {relation}: dashboard requires published_url")

    public_projects = []
    for key, item in projects.items():
        if set(item) - {"name", "public", "kind", "description", "resources", "available"}:
            raise ValueError(f"project {key}: unknown field")
        if not isinstance(item.get("kind"), str) or item["kind"] not in KINDS:
            raise ValueError(f"project {key}: unknown project kind")
        relations = item.get("resources", {})
        if not isinstance(relations, dict) or set(relations) - RELATIONS.keys():
            raise ValueError(f"project {key}: unknown resource relationship")
        available = _entries(item.get("available", {}), "available capability")
        for capability, option in available.items():
            if capability not in CAPABILITIES or set(option) - {"name", "public"}:
                raise ValueError(f"project {key}: unknown available capability or field")
            if relations.get(capability):
                raise ValueError(f"project {key}: available capability is already connected")
        groups = []
        for relation, label in RELATIONS.items():
            ids = relations.get(relation, [])
            if (not isinstance(ids, list) or any(not isinstance(i, str) for i in ids)
                    or len(ids) != len(set(ids))):
                raise ValueError(f"project {key}: relationships must be unique ID lists")
            if any(i not in resources for i in ids):
                raise ValueError(f"project {key}: unknown resource reference")
            visible = [resolved[i] for i in ids if resources[i].get("public") is True]
            option = available.get(relation, {})
            if visible or option.get("public") is True:
                group = {"relation": relation, "label": label, "resources": visible}
                if option.get("public") is True:
                    group["available"] = [{"id": relation, "name": option["name"],
                                           "purpose": CAPABILITIES[relation]}]
                dashboard = routes.get(relation)
                if dashboard and resources[dashboard].get("public") is True:
                    group["dashboard"] = {"id": dashboard, "name": resources[dashboard]["name"],
                                          "url": resources[dashboard]["published_url"]}
                groups.append(group)
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


def display_groups(project: dict) -> list[dict]:
    """Combine rows sharing a dashboard; keep typed relationships in the snapshot."""
    groups = {}
    for group in project["groups"]:
        dashboard = group.get("dashboard")
        key = ("dashboard", dashboard["id"]) if dashboard else ("relation", group["relation"])
        if key not in groups:
            groups[key] = {"label": dashboard["name"] if dashboard else group["label"],
                           "url": dashboard["url"] if dashboard else None,
                           "resources": [], "available": []}
        row = groups[key]
        row["available"].extend(group.get("available", []))
        seen = {r["id"] for r in row["resources"]}
        for resource in group["resources"]:
            if resource["id"] in seen:
                continue
            resource = dict(resource, links=list(resource["links"]))
            if dashboard and group["relation"] in {"tests", "workspaces", "tutorials", "documentation", "assistants"}:
                base = dashboard["url"].split("#", 1)[0]
                resource["links"].append({"label": dashboard["name"] + " details",
                                          "url": base + "#resource-" + resource["id"]})
            row["resources"].append(resource)
    return list(groups.values())


def markdown_text(value: str) -> str:
    """Escape instance-owned labels for plain text in published Markdown."""
    return re.sub(r"([\\\[\]*_`#|])", r"\\\1", html.escape(value)).replace("\n", " ")


def setup_prompt(project: dict, option: dict) -> str:
    """A portable request, not an activation command or inferred repository ID."""
    return (
        f"Help me add {RELATIONS[option['id']].lower()} to project "
        f"{json.dumps(project['name'])} (stable project ID: {project['id']}). "
        f"Suggested name: {json.dumps(option['name'])}; this is only a naming hint.\n\n"
        "Read this Scientist's instructions, instance profile, project relationships and "
        "canonical Mind repository map. Inspect existing project-owned sources and any "
        "partial setup first; reuse them and preserve user records. Ask for missing purpose, "
        "location, ownership or visibility choices. Do not infer identity or access from names. "
        "Propose the smallest useful setup through the existing development workflow, "
        "including validation and how to resume it. Obtain approval before creating "
        "repositories, changing access, publishing or running science.\n\n"
        f"Keep capability {option['id']} available until setup is validated. Then replace "
        "its available entry with an explicit connected resource using the canonical "
        "repository identity, and validate the Scientist configuration offline. "
        "Configure an owning organ separately if needed; a resource link is not organ "
        "activation or evidence of quality."
    )


def render_markdown(snapshot: dict) -> str:
    text = markdown_text

    lines = ["## Projects"]
    for project in snapshot.get("projects", []):
        lines.extend(["", "### " + text(project["name"]), "", text(project["description"])])
        for group in display_groups(project):
            label = text(group["label"])
            if group["url"]:
                label = f"[{label}]({quote(group['url'], safe='/:?=&%+#@~;,-_')})"
            for resource in group["resources"]:
                links = " · ".join(f"[{text(resource['name'] if i == 0 else link['label'])}]({quote(link['url'], safe='/:?=&%+#@~;,-_')})"
                                   for i, link in enumerate(resource["links"]))
                lines.append(f"- {label}: {links}")
            for option in group["available"]:
                lines.extend([f"- {label}: {text(option['name'])} — Available to add",
                              "", text(setup_prompt(project, option)), ""])
    return "\n".join(lines)


def render_html(snapshot: dict) -> str:
    esc = html.escape
    cards = []
    for project in snapshot.get("projects", []):
        groups = []
        for group in display_groups(project):
            entries = []
            for resource in group["resources"]:
                links = " · ".join(f'<a href="{esc(link["url"], quote=True)}">{esc(resource["name"] if i == 0 else link["label"])}</a>'
                                   for i, link in enumerate(resource["links"]))
                entries.append(f'<li data-resource="{esc(resource["id"])}">{links}</li>')
            for option in group["available"]:
                ident = f"setup-{project['id']}-{option['id']}"
                entries.append(
                    f'<li><details class="available-resource" data-capability="{option["id"]}">'
                    f'<summary><span>{esc(option["name"])}</span> '
                    '<span class="availability-label">Available to add</span></summary>'
                    f'<div class="available-resource-body"><p>{esc(option["purpose"])}</p>'
                    f'<label for="{ident}">Setup prompt</label>'
                    f'<textarea id="{ident}" readonly rows="8">'
                    f'{esc(setup_prompt(project, option))}</textarea></div></details></li>')
            label = esc(group["label"])
            if group["url"]:
                label = f'<a href="{esc(group["url"], quote=True)}">{label}</a>'
            groups.append(f'<div class="summary-row"><dt>{label}</dt><dd><ul>{"".join(entries)}</ul></dd></div>')
        content = f'<dl>{"".join(groups)}</dl>' if groups else '<p>No public resources configured.</p>'
        cards.append(f'''<details class="organ-card project-card" id="project-{esc(project['id'])}">
<summary><span>{esc(project['name'])}</span><span class="organ-status">{esc(KINDS[project['kind']])}</span></summary>
<div class="organ-content"><p>{esc(project['description'])}</p>{content}</div></details>''')
    empty = '<p>No public projects configured.</p>' if not cards else ''
    return f'''<section id="projects" aria-labelledby="projects-heading"><h2 id="projects-heading">Projects</h2>
{empty}<div class="organ-grid" aria-label="Project resources">{''.join(cards)}</div></section>'''


def catalogue(snapshot: dict) -> dict:
    """Public, deduplicated inventory only; no evidence or source-content copy."""
    resources = {}
    for project in snapshot.get("projects", []):
        for group in project["groups"]:
            for resource in group["resources"]:
                row = resources.setdefault(resource["id"], dict(resource, projects=[], relations=[]))
                context = {"id": project["id"], "name": project["name"]}
                if context not in row["projects"]:
                    row["projects"].append(context)
                if group["relation"] not in row["relations"]:
                    row["relations"].append(group["relation"])
    return {"schema_version": 1, "resources": list(resources.values())}
