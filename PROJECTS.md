# Connected projects

The Scientist home shows **software families** and, when explicitly configured,
**scientific investigations** as separate kinds of project. A software family
is not a Cortex investigation. Cards are a navigational inventory; source
repositories and organs retain their authoritative records. An empty card means
no public resources were configured, not that work or evidence does not exist.

## Connect or change a project

Edit the instance-owned `config/projects.json`. Keep stable IDs when renaming a
project or resource. Add repository identities to your canonical Mind
`repos.yaml`, then refer to those keys here; never copy GitHub owners/remotes
into a second repository inventory. Resource IDs can appear in multiple project
cards, including as shared dependencies. Associations are curated, not a complete
package dependency lockfile and not inferred from naming prefixes.

Each project has `name`, `kind` (`software_family` or `scientific_project`),
optional `description`, `public`, and a `resources` object. Its optional lists
are `software`, `dependencies`, `workspaces`, `tutorials`, `documentation`,
`assistants`, `profiling`, `inference`, `visualization`, `tests` and `records`. Each list contains resource IDs, in display order.
An assistant is never required. An empty project catalogue is supported.

Each resource has `name`, `public`, and one or both of:

- `repo`: a key from the canonical identity map. Optional repository-relative
  `path` and `ref` point at a folder or file. With a path and no ref, `main` is
  used; set ref explicitly for other default branches or a pinned revision.
- `published_url`: an explicit HTTPS destination, such as external documentation
  or an owning organ's board. This is a published location, not a second repo ID.

The version-1 format is a JSON object with `schema_version: 1`, `resources`
and `projects` objects keyed by stable lowercase, hyphen-separated IDs.
For example, given `analysis-code` in your own identity map:

```json
{
  "schema_version": 1,
  "resources": {
    "analysis-guide": {
      "name": "Analysis guide", "repo": "analysis-code",
      "path": "docs", "ref": "main", "public": true
    }
  },
  "projects": {
    "spectra": {
      "name": "Spectra", "kind": "scientific_project", "public": true,
      "resources": {"documentation": ["analysis-guide"]}
    }
  }
}
```

Validate without collecting feeds:

```bash
python scripts/organism_board.py --projects config/projects.json \
  --repos /path/to/YourMind/repos.yaml --check-projects
```

Use the same arguments with `--html`, `--md` or `--json` to render. A configured
workspace can supply `PYAUTO_MIND`; otherwise Brain's manifest-backed resolver
locates Mind. An unavailable map or invalid relationship fails rendering instead
of publishing a misleading empty catalogue. Rendering never fetches linked
content or executes project code. Ordinary organ feed refresh remains unchanged.

## Publication and ownership

Only projects **and** resources explicitly marked `public: true` enter the
rendered snapshot. Omitted/false values exclude them from HTML, Markdown and
embedded JSON. This flag records an owner's publication decision; it does not
check remote repository permissions. Review links and metadata before enabling
it. The configuration in this repository is itself public: never put private
project details here, even under `public: false`. Use a private instance/local
configuration for private material. Connecting resources changes no permissions.

Project repositories own software, docs, notebooks, scripts, assistant definitions
and runners. Scientist owns these explicit project associations and links. The
agreed Broca expansion covers communication/documentation relationships and
upkeep evidence, with documentation, tutorials, user-facing workspaces and
assistants as first-class surfaces. Its dashboard now presents communication
resource inventories alongside assistant evidence; broader upkeep evidence
remains separate Mind work. These IDs/categories provide a coordination point,
not a new Broca evidence schema or copied ledger. Links to Broca route
communication resources to its dashboard; they do not imply a project-specific
assessment or implemented evidence coverage.

Ears retains listening and feedback collection; Brain interprets and routes;
Mind tracks implementation; Memory holds knowledge and citations; Cortex owns
scientific records and human conclusions; Eyes owns gallery evidence; Heart
owns readiness; Hands owns builds/releases. A project may link any relevant
owner record without transferring ownership. Inventory presence, technical
validation, freshness and explanatory quality remain distinct. No external
messages, publication actions, evaluation runs or setup actions happen on a
card click or dashboard refresh.

## Adoption and upgrades

`config/projects.json` is user-owned configuration. `scripts/project_resources.py`
is framework logic; it contains no project names, GitHub owners or repository
suffix assumptions. The canonical identity map remains independently owned in
Mind. Rename displays or change canonical locations without changing stable IDs.
Unsupported schema versions fail explicitly; an upgrade must preserve the
configuration and user records or supply a reviewable migration.

Independent names and explicit optional organ connections are supported by the
local [starter preview](STARTER.md). Resumable activation, independently hosted
deployment and record-preserving upgrades remain separate phases. Shared
multi-contributor operation is a later milestone.

## Dashboard routing

An optional top-level `routes` object maps relationship names to resource IDs
for the relevant dashboards. Each target must have a `published_url`. For example,
`"profiling": "pulse-dashboard"` routes profiling resources to a dashboard resource
named Pulse. Identity and URLs stay in instance configuration, not framework logic.

Cards combine relationships routed to the same public dashboard into one row: the
organ name links to its dashboard and each resource name links to its source (with
a separate Published link when configured). The snapshot retains each typed
relationship for reuse. Broca groups docs, tutorials, workspaces and assistants;
Pulse profiling; Insight inference; Eyes visualization; Heart test workspaces.
These links convey responsibility, never a health or quality verdict.

Without a route, or when its dashboard is not explicitly public, resources retain
their ordinary category row. No private dashboard name or URL enters the snapshot.
Old schema-version-1 configurations continue to work without `routes`; generic
`records` remains supported for existing instances, but this instance no longer
uses the generic Organ records row or the shared assistant evidence inventory.

## Public owner-board catalogue

`organism_board.py --catalogue --repos <Mind>/repos.yaml` exports only public
resources referenced by public projects, deduplicated by stable resource ID.
It collects no organ feeds. Heart and Broca keep reviewed copies as resources.json
for offline rendering. Regenerate these projections when relationships change;
never hand-maintain a second identity or relationship map. The catalogue carries
no evidence timestamp: inventory refresh is not evidence collection.

Tests and communication resources link to their owning board's
`#resource-<resource ID>` disclosure while retaining source/published links.
Publish the owner-board changes before publishing the new Scientist links.

## Available to add

Each project may opt into `available` opportunities keyed by the stable capability
IDs `workspaces`, `tutorials`, `documentation`, `assistants`, `tests`, `profiling`,
`inference` and `visualization`. Add only what would be useful to that project:

```json
"available": {
  "workspaces": {"name": "myproject_workspace", "public": true},
  "inference": {"name": "myproject_inference", "public": true}
}
```

`name` is an instance-owned naming hint. No GitHub URL is inferred, no remote
existence is checked, and suffixes do not establish identity. The grey disclosure
contains a short purpose and selectable setup prompt. It stays usable by keyboard
and without JavaScript. Existing dashboard routes also group these opportunities;
an absent or private route falls back to the category heading.

As with connected resources, both the project and opportunity need explicit
`public: true` to appear. Opportunities are excluded from the connected resource
catalogue consumed by Heart and Broca. You cannot mark a capability available
while the same project's relationship contains a connected resource, including a
private one. To connect a validated resource, remove that opportunity and add the
normal resource/relationship using its canonical identity in one configuration
change. Projects can always omit assistants, and resources can be shared.

This is an explicit discovery contract, not a setup-state ledger. Keep incomplete
setup in your existing task records; do not claim it is connected until validated.
Missing or stale evidence on a connected organ never greys its resource into an
available opportunity. Paused/needs-attention states, resumable activation and
organ-specific validation remain separate work.
