# Design Decisions

This document records settled product and data-model decisions for Finance OSINT.
It is the reference for future schema, CLI, and plugin work.

## Core Philosophy

Finance OSINT is a local-first, git-native evidence graph.

- The git repo is the canonical database.
- There is no server, hosted database, private moderation layer, or hidden agent state.
- Contributors pull the repo, make structured changes locally, and submit pull requests.
- Agents and humans are treated the same at the data-model layer.
- The GitHub user submitting a PR is responsible for the contribution, including agent-assisted work.
- Canonical records should be judged by structure, provenance, and evidence, not by whether a human or agent authored them.

## Canonical Layers

The core model separates observation from interpretation:

```text
Source -> Dataset -> Evidence -> Metric/Event/Claim -> Relationship -> Thesis -> Debate
                              -> Validation/Challenge
```

Canonical object types:

```text
source
dataset
evidence
entity
metric
event
claim
validation
challenge
relationship_type
relationship
claim_predicate
thesis
debate
argument
resolution
```

## Agents

Agents are native operators, but not special canonical authors.

- Do not add `agent_run` records to the canonical database.
- Do not require `generated_by` or agent-specific provenance fields.
- Agent workflow guidance belongs in the external toolkit/plugin, not in canonical data.
- The data repo may keep a small `AGENTS.md` router, but not a large task manual.

## Evidence Semantics

Evidence is classified by how it was obtained and how independently verifiable it is.

Use plain evidence classes:

```text
public_primary
public_secondary
firsthand_public
firsthand_private
anonymous_internal
rumor
```

Evidence classes describe provenance, not truth.

Low-trust evidence classes:

```text
anonymous_internal
rumor
```

Low-trust evidence may exist in the repo, but it must not silently become strong factual support. Tools should prevent low-trust evidence from being the only support path for strong derived review states.

First-hand, private, anonymous, and rumor evidence should carry explicit metadata:

```text
public_status
source_attribution
source_access
verification_status
risk_flags
content_mode
```

Allowed source attribution values:

```text
named_public
anonymous_to_public
unknown
```

Do not support `anonymous_to_maintainers`. Everything that changes support power must be visible in the repo. Maintainer-only source knowledge would create a hidden trust layer.

The project enforces provenance and labeling, not broad legal or investment-suitability policing.

Minimal repository hygiene still applies:

```text
no secrets
no credentials
no doxxing or PII dumps
no malware
no giant copyrighted uploads
no accidental private files
```

## Claims

A claim is a narrow assertion backed by evidence.

Claims should not carry canonical truth status such as `corroborated`, `falsified`, or `disputed`.

Instead, claims should carry:

```text
statement
predicate
support_type
subject
object or structured fields
evidence
risk_flags
supersedes / superseded_by when applicable
```

Review state is derived locally from evidence, validations, challenges, contradictions, and archive/supersession metadata.

## Derived Review State

Derived review state is local tooling output, not canonical truth.

Tools may compute labels such as:

```text
unreviewed
supported
partially_supported
contested
low_trust_only
stale
superseded
withdrawn
```

These labels summarize the local evidence graph for users and agents. They should never be committed as canonical claim or relationship status.

Derived review state must not be vote-counting. Multiple validations do not create truth by volume. Tools should weigh:

```text
evidence class
source independence
support_type
validations
challenges
contradictions
supersession
archive location
time freshness
```

The first review algorithm can be simple, but it must be deterministic and documented before public launch.

### Support Type

Use plain support types:

```text
direct
  The evidence directly states the claim.

observed
  A contributor or source observed it first-hand.

inferred
  The claim is reasoned from multiple evidence points.

private_attestation
  A private, anonymous, or internal source attests to it.

rumor
  Weak signal or unverified report.
```

Support type describes the reasoning distance between evidence and claim.
Evidence class describes the provenance of the evidence itself.

### Support Compatibility

Support type must be compatible with the evidence path.

Initial rules:

```text
direct
  Requires evidence that directly states the assertion.
  Not compatible with rumor-only evidence.

observed
  Requires firsthand_public evidence or clearly attributed observation.

inferred
  Requires multiple evidence links or an explicit methodology.

private_attestation
  Requires firsthand_private or anonymous_internal evidence metadata.

rumor
  Allowed only as weak signal.
  Cannot produce strong derived support alone.
```

This matrix should be enforced by validators and explained by CLI error messages.

## Claim Predicates

Claim predicates should have a lightweight registry.

Initial predicates:

```text
reported_metric
disclosed_relationship
observed_event
management_statement
ownership_disclosure
transaction_disclosure
regulatory_action
legal_action
product_signal
market_signal
source_attestation
forecast_statement
```

Predicates describe the shape of the assertion, not investment interpretation.

Good predicates:

```text
reported_metric
disclosed_relationship
observed_event
source_attestation
```

Bad predicates:

```text
is_undervalued
is_fraud
will_moon
short_squeeze_coming
```

If a predicate does not exist yet, contributors may use a provisional predicate:

```yaml
predicate: provisional:channel_inventory_signal
proposed_predicate_definition: claim-predicates/proposals/channel_inventory_signal.yml
```

Predicate definitions should eventually declare:

```text
required fields
allowed support_type values
allowed subject kinds
allowed object kinds
whether the predicate may reference metric, event, or relationship records
```

## Metrics

A metric is a structured numeric observation with provenance.

Metrics may represent past, present, reported, observed, derived, or estimated values.
Future expectations should not be metrics; they belong in thesis forecasts.

Minimal metric fields:

```text
kind
id
entity
metric_type
value
unit
period
value_basis
evidence
```

Allowed value bases:

```text
reported
observed
derived
estimated
restated
```

Metrics are evidence-backed numeric records, not inherently undisputed truth.

Estimated or derived metrics should include methodology fields:

```text
methodology
sample_size
coverage
limitations
source_dataset
```

Metrics may stand alone as specialized numeric records with evidence. A separate claim is only needed when someone wants to make a textual assertion or argument from the metric.

## Events

An event is a structured time-bound occurrence.

Examples:

```text
earnings release
guidance change
product launch
factory shutdown
customer loss
supplier disruption
lawsuit filing
regulatory approval
M&A announcement
management change
insider transaction
```

Minimal event fields:

```text
kind
id
event_type
title
occurred_at
entities
evidence
properties
```

Events support timelines, causal reasoning, and relationship changes.

## Point-In-Time Semantics

Finance records must preserve time context.

Use these fields consistently:

```text
period
  Fiscal, calendar, or measurement window.

as_of
  Point-in-time value date.

observed_at
  When the observation occurred.

published_at
  When the source was published.

accessed_at
  When the contributor accessed the source.

effective_at
  When an event, relationship, contract, rule, or change became effective.

restated_from
  Prior metric, event, or record being corrected or restated.
```

Ambiguous time semantics are a data-quality problem. Validators and templates should push contributors to include the relevant time field rather than hiding time inside prose.

## Datasets

A dataset is metadata about a collection of records.

Examples:

```text
SEC company facts
customs records
app download estimates
vehicle registrations
store check surveys
job postings scrapes
pricing histories
```

Minimal dataset fields:

```text
kind
id
title
dataset_type
publisher
coverage
access
sources
```

Datasets should describe collections; evidence and metrics should reference the concrete rows, excerpts, observations, or values used.

## Source And Content Storage

The canonical repo should store structured records, not become a bulk file archive.

Default storage policy:

```text
public URL, archive URL, hash, metadata: yes
short excerpt or summary: yes
small fixture files: maybe
large PDFs, screenshots, reports, transcripts, and datasets: link or hash by default
raw leaked or private documents: not canonical raw content
```

This is repository hygiene. It keeps clone size, reviewability, and provenance manageable.

## Relationships

Relationships are first-class graph objects, not simple edges.

Relationship type defines roles.
Scope defines context.
Qualifiers define modifiers.
Materiality defines importance.
Evidence defines support.

Relationship instances should support n-ary participants by default:

```yaml
participants:
  buyer: entity:company:A
  supplier: entity:company:B
  end_market: entity:market:C
```

Use broad registered types plus rich scope instead of many one-off specific types.

Inverse relationships should usually be derived locally, not duplicated in canonical records.

If a relationship type does not exist yet, contributors may use a provisional type with a proposed definition.

Relationship type definitions should include role cardinality:

```text
required roles
optional roles
allowed scope
allowed qualifiers
allowed materiality values
```

Use scope for contextual entities unless the relationship type explicitly defines them as participant roles.

## Contradictions

Contradictions should be represented as structured disagreement, not overwrites.

Preferred workflow:

```text
1. Add the counterclaim or counter-relationship with evidence.
2. Add a challenge targeting the older object.
3. Link contradictory or superseding objects.
4. Let local tools show both and derive the review view.
```

Contradiction is an epistemic relationship between knowledge objects, not a business relationship between companies.

Objects that can be superseded or contradicted should support consistent linkage fields:

```text
contradicts
supersedes
superseded_by
related_to
```

These links make contradiction and compaction discoverable without relying only on prose in challenges.

## Validations And Challenges

Validations and challenges are append-only review records.

Use validations for targeted review outcomes:

```text
attests
supports
partially_supports
disputes
falsifies
marks_stale
withdraws
```

Use challenges for open objections:

```text
contradiction
missing_evidence
source_quality
scope_error
outdated
ontology_issue
materiality_dispute
other
```

Disagreement should generally add validation/challenge records rather than destructively editing evidence or claims.

One-sentence distinction:

```text
Validation evaluates support; challenge records unresolved pressure.
```

A cluster of validations and challenges around one object may later be promoted into a debate when the disagreement becomes broader than one target object.

## Theses And Forecasts

A thesis is an interpretation, causal argument, or forecast built from evidence, claims, metrics, events, and relationships.

Theses may be opinionated and directional, but dependencies must remain explicit.

Forecasts should live inside theses as optional structured expressions:

```yaml
forecast:
  metric_type: revenue
  entity: entity:company:COMPX
  period:
    start: "2026-01-01"
    end: "2026-12-31"
  expected_value:
    operator: "<"
    value: 1500000000
    unit: USD
```

Do not add first-class forecast objects until forecasting needs independent scoring, querying, or lifecycle.

Do not add strategy or trade-expression objects to the canonical core for now.

## Debates

Debates are advisory containers for structured disagreement.

- Debate does not directly decide truth.
- Debate organizes a question, positions, arguments, evidence, and resolution snapshots.
- Resolutions are snapshots, not binding status changes.
- Challenges and validations are the targeted review layer.

Debate lifecycle should be operational:

```text
open
archived
```

not truth labels.

Canonical debate files are optional. Early-stage discussion can happen in GitHub issues or PR comments. Promote a debate into canonical files when the question spans multiple claims, relationships, theses, or positions and is worth preserving as durable structured reasoning.

## Archive And Bloat

Bloat is expected and should be managed publicly.

Use:

```text
supersedes
superseded_by
time_scope
archive/
local current views
public compaction PRs
```

Archive layout:

```text
archive/
  claims/
  relationships/
  theses/
  debates/
```

Evidence should rarely be archived. It is the foundation of the repo.

Tools should ignore archive by default and include it only when explicitly requested.

Archive PRs must explain why a record is being archived and should link replacements when applicable:

```text
superseded_by
duplicate_of
archive_reason
```

Archiving should not be used to bury inconvenient counter-evidence. `fo lint` should validate archive records by default; current-view commands such as `fo search` and `fo context` should exclude archive unless `--include-archive` is passed.

Deletion should be rare and reserved for repository hygiene issues such as secrets, PII dumps, malware, large copyrighted uploads, or accidental private files.

## Duplicate And Merge Policy

Duplicate records are expected once agents and many contributors operate on the repo.

Entity duplicate hints:

```text
same CIK
same LEI
same ISIN
same official registry id
```

Ticker alone is not enough because tickers can change, collide across exchanges, or be reused.

Claim duplicate hints:

```text
same subject
same predicate
same object or structured payload
same period/as_of
same evidence
```

Duplicate detection should begin as warnings in local tooling, using SQLite and full-text search. Merges should be explicit PRs that preserve old IDs through `superseded_by`, `duplicate_of`, or equivalent links.

## Derived Local State

Canonical state is YAML plus schemas.
Derived local state lives in `.local/` and is not committed.

Pre-public derived state requirements:

```text
.local/graph.json
.local/index.sqlite
```

Required local commands before public launch:

```text
fo graph build
fo index build
fo search
fo context
fo review
fo graph neighbors
```

No embeddings in v1.

SQLite plus full-text search is enough for launch.

The SQLite index should be deterministic and fully rebuildable from YAML. It must never become the write source of truth.

Initial SQLite tables should include:

```text
records
edges
refs
entities
claims
evidence
metrics
events
relationships
fts
```

## Contribution UX

Contributions should be typed.

PR template categories:

```text
evidence
claim
metric-event-dataset
relationship
thesis
validation-challenge
debate
ontology
maintenance-archive
```

Agents and power users need non-interactive commands and JSON outputs.
Interactive wizards can come later.

## Identity And Attribution

Contributor identity and source attribution are different.

```text
submitted_by
  GitHub identity accountable for the record.

attributed_to
  Speaker, guru, management team, firm, source category, or public entity whose statement or forecast is being recorded.
```

For public-statement and guru accountability workflows, use `attributed_to` rather than implying the subject authorized the record.

`submitted_by` is useful but not sufficient by itself. Before public launch, CI should verify that `submitted_by` matches the PR author unless an explicit and reviewable `submitted_on_behalf_of` workflow exists.

## Schema Versioning And Migrations

Before public launch, every canonical record should include:

```yaml
schema_version: 1
```

The repo should add:

```text
schemas/migrations/
fo migrate
```

Schema changes after public launch must be explicit migrations, not silent schema drift.

## ID And Path Conventions

IDs should be stable. Paths may change.

Prefer stable entity slugs over volatile tickers:

```yaml
id: entity:company:apple-inc
identifiers:
  ticker: AAPL
  cik: "0000320193"
```

Example path:

```text
claims/company/apple-inc/aapl-tsmc-a-series-supply.yml
```

Agents need deterministic ID and path rules before large-scale writes. Rules should cover:

```text
slug generation
company renames
ticker changes
duplicate tickers
CIKs and other stable identifiers
cross-entity relationships
date suffixes
author suffixes for validations/challenges
```

## Public V1 Scope

The canonical design can include metrics, events, datasets, debates, arguments, and resolutions.

Public launch scope should be narrower:

```text
entity
source
evidence
claim
claim_predicate
relationship_type
relationship
validation
challenge
thesis
```

Metrics, events, datasets, and durable debates should be added once the public-source path is solid or when the first real corpus proves the need.

The first public workflows should focus on:

```text
filings
public statements
claim extraction
relationship mapping
thesis writing
validations/challenges
guru forecast attribution
```

## Minimal Agent Router

The data repo may include a small `AGENTS.md`:

```text
Use the Finance OSINT toolkit/plugin if available.
Operate through `fo` commands where possible.
The submitting GitHub user owns all contributions, agent-assisted or not.
Do not add agent-specific provenance to canonical records.
Do not edit evidence to resolve disagreement; add validations/challenges.
Run `fo lint`, `fo graph build`, and `fo index build` before finishing.
```

Detailed agent workflows belong in the external toolkit/plugin.
