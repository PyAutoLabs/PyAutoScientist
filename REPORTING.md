# Reports across the organism

Scientist is the place to ask “What happened across all organs in the last
24 hours?” or “Summarize this week's work.” It joins evidence and coordinates
follow-through; the organs keep their authoritative records.

## Establish the period

Default an unspecified overview to the previous 24 hours, ending now. Honor a
requested duration or date range. State the exact start, end and timezone;
use the user's known timezone, or explicitly use UTC if unknown. Resolve
ambiguous boundaries with the user only when they materially affect the answer.

Distinguish events **during that period** from the **current position**. An
older blocker can still need attention, but it is not new work in the period.
A feed's generation time or dashboard refresh is not a completion timestamp.

## Cover the organs without loading every repository

Discover organ membership from Brain's board registry and Mind's body map.
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
