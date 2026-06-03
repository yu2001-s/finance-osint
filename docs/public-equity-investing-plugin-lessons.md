# Public Equity Investing Plugin Lessons

Reviewed on 2026-06-03 before stock-research seed migration.

The OpenAI Public Equity Investing plugin is workflow-oriented, while Finance
OSINT is a repo-native evidence graph. We should borrow its provenance and
research-discipline ideas, not its workbook, connector, or portfolio-action
surface.

## Borrow

### Source Honesty

Do not imply access to data providers, transcripts, estimates, or filings unless
the source material is explicitly present in the repo or supplied by the
contributor.

For migrated data, prefer explicit source material in this order:

```text
explicit user/repo source package
public primary source
counterparty or regulator source
independent research or media
social post or forum post
```

This is not a truth hierarchy. It is a prompt for better provenance labels and
missing-source questions.

Old researcher interpretation and contributor/agent inference are not source
material. Migrate them only as thesis language, questions, or challenges unless
explicit source-backed dependencies exist.

Use existing fields first:

```text
source_type
source_perspective
public_status
content_mode
archive_url
content_hash
source_artifacts
risk_flags
```

### Fact, Estimate, And Assumption Separation

Numbers should enter canonical records with explicit basis:

```text
reported
observed
derived
estimated
restated
```

Management guidance and company statements are source-backed claims or events,
not contributor forecasts. Consensus estimates are `estimated` metrics only when
an explicit consensus source or export is present. Contributor assumptions and
scenario work belong in thesis records unless they are quoted from a source.

### Thesis Discipline

A useful thesis should expose:

```text
the mispriced or under-explained wedge
the evidence dependencies
the core pillars
the observable proof points
the observable kill criteria
the next missing evidence
the time horizon
```

These fields may live inside `thesis` records for now. They should not be turned
into canonical claim truth statuses.

### Catalyst Timing

Expected events are allowed, but exact dates require exact source support. If a
source gives only a window, record the window under `period` or `properties`;
do not collapse it into a fake exact `expected_at` date.

Suggested event properties:

```text
date_type: exact | window | inferred_window | unknown
timing_basis: source_disclosed | company_guided | historical_pattern | contributor_inferred
timing_confidence: confirmed | guided | expected | inferred | rumored | unknown
```

These are event metadata, not truth status.

### Conflicts And Comparability

When sources disagree, preserve both source-backed records. Use challenges,
questions, `restated_from`, `supersedes`, or explicit limitations rather than
silently choosing one value.

Watch for public-equity comparability problems:

```text
non-GAAP definition changes
segment recasts
period mismatches
preliminary or unaudited figures
OCR or extraction uncertainty
old source link rot
```

## Do Not Borrow

- Hidden support artifacts or private connector state.
- Provider assumptions without visible source material.
- Workbook-first output as canonical data.
- Portfolio sizing, rating, or trade-action records as canonical objects.
- Vote-like confidence scoring or committed review status.

Trading language may appear in theses if contributors choose to write it, but
canonical evidence, metrics, claims, and relationships must stay intact and
source-backed.

## Seed Migration Implications

- Treat social posts as sources for what the account said. Underlying company
  facts still need direct hard evidence.
- Convert old `status`, `confidence`, `evidence_strength`, and `verdict` into
  evidence metadata, questions, challenges, validations, or thesis caveats.
- Keep old watchlists and vetoes as questions, challenges, or thesis language.
- Do not seed broad theses unless their dependencies, proof points, and kill
  criteria are explicit.
- Use deterministic tools for formatting and validation. Use human judgment only
  to decide what a source actually supports.
