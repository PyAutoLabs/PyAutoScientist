# Reports across the organism

Scientist is the place to ask “What happened across all organs in the last
24 hours?” or “Summarize this week's work.” It joins evidence and coordinates
follow-through; the organs keep their authoritative records. Use the existing
Scientist check-in with a direction such as “Review overnight work” or
“What changed since Friday?”; no separate reporting service is required.

## Establish the period

Default an unspecified overview to the previous 24 hours, ending now. Honor a
requested duration or date range. State the exact start, end and timezone;
use the user's known timezone, or explicitly use UTC if unknown. Resolve
ambiguous boundaries with the user only when they materially affect the answer.

Distinguish events **during that period** from the **current position**. An
older blocker can still need attention, but it is not new work in the period.
A feed's generation time or dashboard refresh is not a completion timestamp.

## Cover the organs without loading every repository

Use the instance profile's explicit connections when present; otherwise discover
organ membership from Brain's board registry and Mind's body map. Do not assume
that an independent instance has every framework organ installed.
Read their published summaries first, then inspect the relevant dated owner
records. For an all-organ report, account for every listed organ, including
ones whose evidence is missing. Ordinary focused requests still load only the
relevant organs; this guide does not authorize a repository-wide source scan.

| Owner | Evidence for a report |
|---|---|
| Brain | Coordination decisions and workflow outcomes |
| Mind | Task progress, issued/completed records, linked issues and PRs |
| Cortex | Project ledgers, run records and the scientist's recorded conclusions |
| Memory | Dated knowledge additions or revisions |
| Eyes | Published figure reviews, galleries and render evidence |
| Ears | Collection receipts and conversations needing a response |
| Heart | Dated checks, readiness changes and unresolved findings |
| Hands | Release records, published versions and failed release attempts |
| Pulse / Insight | Profiling/inference receipts, campaign progress and measured results |
| DNA / Nerves | Environment/compatibility observations and configuration work |
| Broca | Assistant evaluation and upkeep evidence |
| Gut | Cleanup receipts and pending disposal decisions |

Use each owner's entry guidance to locate its actual records; do not assume
all boards expose the same history endpoint. Current state feeds alone cannot
establish historical coverage. Git activity is supporting evidence, not proof
of completed work: distinguish proposed, committed, merged, published and
scientifically accepted outcomes. A release, a merged task and a successful
scientific run are different kinds of result.

## Query activity when asked

Brain's dashboard is an agent/workflow directory, not an overnight collector.
At request time, use dated owner records and the relevant repositories' workflow
runs to cover the requested interval. Enumerate enough runs/pages to establish
coverage; the single latest run per workflow cannot answer “what happened in the
last 24 hours.” Do not assume a fixed list of workflow names or repository owners.

Distinguish failure, a successful gate that blocked execution, work still in
progress, and a verified absence of runs. Follow run links for gate reasons and
use event timestamps, not the time you fetched a feed. Missing access, expired
history or incomplete pagination must appear as coverage gaps. State the cutoff
for work still changing while you review it. Brain's explicit workflow tools may
help investigate a specific run, but are not a separate history ledger.

## Write the summary

Lead with a few high-level outcomes, then active work/blockers and decisions
or useful next steps. Link each significant outcome to its owning evidence,
with an event date where available. Combine one task appearing in several
organs into one account; do not count its issue, PR and release as three tasks.
Keep domain judgments with their owner. Report scientific interpretations only
when requested, and distinguish them from the scientist's accepted conclusions.

End with a short coverage note: organs checked, sources that cover the period,
and missing/stale/unavailable history. Say “no recorded activity” only when
records for the period were checked; otherwise say “history unavailable.” Do
not turn an unavailable source into an all-clear. Do not imply exhaustive
coverage when access or retention prevents it. Avoid a long row for every quiet
organ unless the user requests that detail.

A requested summary is read-only. Follow-up work uses the owning workflow and
existing approval rules; the request does not authorize compute, replies,
merges or releases. Do not add recurring collection, a second task registry or
persistent monitoring to produce a one-off report.

## Live Feed: recorded development activity

The canonical Scientist dashboard has a grouped Live Feed between Projects and
Dashboards. It covers public development issues, issue/PR discussion updates,
explicit progress reports, closed tasks and merged PRs in Mind's registered
repositories. Library/workspace tasks route to Mind; organ development routes
to that organ. Scientific run progress, private work, local edits and chat-only
work are outside this first version. Independent instance previews do not yet
include the feed.

One task occupies one row. A PR is grouped with an issue only when its body has
one unambiguous standalone `Closes #N`, `Fixes #N` or `Resolves #N` directive for
that same repository and the target issue is in the collected evidence. Other
PRs remain separate. An issue being opened is not evidence of work starting;
a closed PR is not a merge, and a merge is not publication or science acceptance.

Comment bodies are never exported. Recognized headings (`Progress`, `Progress
update`, `In progress`, `Blocked`, `Shipped`, `Workspace PR Created`, `Library PR
Created`) produce short factual stage labels and source links. Other human
comments appear as “Discussion update recorded”; bot comments are excluded.
Editing a comment replaces that event without giving it a new posted time.
The source link is the place to read detail, not an automatic transcript mirror.

Collection runs in the existing Scientist Pages workflow approximately every
five minutes; scheduling and upstream visibility can delay it. The browser
checks the published same-origin `activity.json` every minute while visible.
There is no GitHub credential or per-visitor GitHub request in the page. A new
snapshot is buffered while a reader has expanded details, focused a control,
scrolled into the feed, or loaded older rows. “Show updates” applies it explicitly.

The `scientist-activity-cache` branch holds a derived, normalized cache and
per-repository cursors. It is not a task registry and contains no API response
bodies, prompts, tokens or raw comments. Only public repositories independently
verified in the current owner catalog are exported. Failed/inaccessible catalogs
suppress their cached rows. Other source failures retain last-known evidence,
mark it stale and leave the cursor unchanged. Losing the cache starts a disclosed
seven-day backfill; successful collection retains up to 30 days, 1500 events per
repository, 200 published task rows and 20 displayed events per task.

The collector reads with a read-only token minted from the organisation's GitHub
App and spends at most 180 requests per cycle; if the token cannot be minted the
run fails rather than collecting with less. It rotates repositories when the request budget is
exhausted; a busy source or pagination cap is reported in coverage rather than
claimed complete. The issue and comment endpoints paginate up to three pages
of 100 each. Partial batches retain verified events and reuse already normalized PR
revisions on the next attempt. A source cursor advances only after both
endpoints and the needed PR details have succeeded. Each cycle also has a
two-minute collection time budget. Therefore “every five minutes” is the collection
attempt interval, not a guarantee that every repository is current. Event time,
source check time and page check time remain distinct. Routine feed rebuilds
never create activity events.

### Pulse coverage and fair collection

`config/activity_sources.json` routes the registered `autolens_profiling` and
`autofit_profiling` development repositories to Pulse. Their identity still comes
from Mind's body map. A repository gets at most 12 API requests in a cycle;
partial normalized evidence survives to the next cycle and other repositories
get a turn. The whole-cycle request and two-minute limits still apply. GitHub
schedule delivery remains best effort; an enabled schedule is not evidence that
a collection occurred. The published source check times are the evidence.

The Pulse adapter reads `campaigns.yaml`, `registry.yaml` and the registered
`snapshots/<instance>.json` at one verified public Pulse commit. Campaign and task
changes share one campaign row. The recorded `last_checkin` dates a check-in,
not a measurement. Repeated check-ins with unchanged facts and next steps do not
create new events. `active` is not displayed as `running`.

A measurement event requires a producer `provenance.measured_at`, a stable
`run_id` and an explicit campaign association. Pulse may provide the association
as `campaigns[].runs: [{repo: <Mind identity>, run_id: <producer run ID>}]` in its
own ledger; alternatively a producer may declare `campaign_id` where its schema
allows it. The adapter never guesses from setup names or filenames. Multiple
measurements from a run produce one campaign-history entry; qualification,
speedups, comparisons and scientific acceptance are not inferred. No run-start
event is invented from a later measurement. Current legacy records lacking times
are counted in coverage and excluded from the timeline.

No Pulse or project records are changed by collection. Pulse input errors keep
last-known campaign history marked stale; an unverified public Pulse repository
suppresses it. The new adapter does not run profiling or add project collection
approval. The original development-only scope above describes PR84; this section
extends it with recorded Pulse campaign and admissible run activity.
