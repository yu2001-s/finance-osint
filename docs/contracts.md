# Contracts

This document defines implementation contracts for schemas, paths, derived state,
and CLI output. It turns the design decisions into stable migration targets.

## Scope

Canonical state is YAML records, JSON Schemas, and Git history.

Derived local state is rebuildable and lives under `.local/`:

```text
.local/graph.json
.local/index.sqlite
```

Derived state must not become the write source of truth.

## Schema Version

Every canonical record must include an integer schema version:

```yaml
schema_version: 1
```

Rules:

- `schema_version` is required on every canonical YAML record.
- It is an integer, not a string.
- Version `1` is the first public contract version.
- Schema changes after public launch require a migration note and, when needed, a migration script.

Migration layout:

```text
schemas/migrations/
  0001-initial-public-contract.md
  0002-example-change.md
```

Future command:

```bash
fo migrate
```

`fo migrate` should never guess semantic intent. It may perform mechanical
renames, field moves, and schema-version bumps when the migration is
deterministic.

## Field Naming

Use `submitted_by` consistently for contributor accountability.

Do not use `author` for canonical contribution ownership. If a record is about
a written artifact whose author is part of the source content, use
`attributed_to` or source metadata instead.

Use `attributed_to` for the person, firm, management team, speaker, source
category, or public entity whose statement, forecast, or attestation is being
recorded.

Do not use agent-specific fields such as:

```text
generated_by
agent_run
model
```

Agent use is a contribution implementation detail. The submitting GitHub user is
responsible for the PR.

## Object Boundaries

Canonical object boundaries:

```text
entity
  A real-world or conceptual actor/object such as company, person, product,
  security, listing, geography, market, technology, service, or regulation.

source
  Provenance metadata for a document, page, filing, transcript, dataset,
  meeting, observation, or report.

dataset
  Metadata about a collection of records.

evidence
  A concrete excerpt, observation, row, table, locator, or source-backed report.

metric
  A structured numeric value with provenance.

event
  A time-bound occurrence or expected occurrence.

claim
  A narrow assertion that may reference evidence, metrics, events, or relationships.

relationship
  A typed n-ary connection among entities.

thesis
  An interpretation, causal argument, or contributor forecast.
```

Do not encode metrics, events, or relationships as prose-only claims when a
structured object exists. Claims may reference those objects to assert or discuss
them.

## Source Attribution

Allowed `source_attribution` values:

```text
named_public
anonymous_to_public
unknown
```

Do not support `anonymous_to_maintainers`. Maintainer-only source identity would
create a hidden trust layer.

## Sources

Minimum source fields:

```text
schema_version
kind
id
source_type
title
public_status
accessed_at
content_mode
```

SEC filing source fields:

```text
accession_number
form_type
filing_date
accepted_at
period_of_report
amends
url
archive_url
content_hash
```

Use `source_type: sec_filing` rather than creating a separate filing object.

Use `source_type: social_media_post` for public posts. The post directly
supports attribution claims about what the account said; underlying company
facts need separate source-backed evidence.

Mutable web-like source types:

```text
web_page
news_article
research_report
```

These should not rely on `url` alone. Prefer `archive_url`. If no archive exists,
use at least one preservation path:

```text
source content_hash
source/evidence source_artifacts
linked evidence excerpt
```

`source_artifacts` must reference local files under `artifacts/sources/`.
Allowed file types are `png`, `jpg`, `jpeg`, and `pdf`. Each file must be 2 MB
or smaller. Unreferenced, missing, invalid-path, invalid-type, and oversized
artifact files are hard lint errors.

## Content Mode

Evidence and source-adjacent records should declare how much content is stored.

Allowed `content_mode` values:

```text
metadata_only
excerpt
summary
redacted_summary
small_fixture
external_link
```

Meanings:

```text
metadata_only
  The repo records metadata, provenance, hashes, or locators only.

excerpt
  The repo stores a short excerpt tied to a source locator.

summary
  The repo stores a contributor-written summary.

redacted_summary
  The repo stores a summary with sensitive details removed.

small_fixture
  The repo stores a small test or example fixture.

external_link
  The repo links to external content rather than storing it.
```

Default policy:

```text
large PDFs, screenshots, reports, transcripts, datasets: external_link or metadata_only
short source excerpts: excerpt
private or sensitive material: redacted_summary or metadata_only
synthetic examples: small_fixture
```

## Evidence Classes

Use plain evidence class labels:

```text
public_primary
public_secondary
firsthand_public
firsthand_private
anonymous_internal
rumor
```

Low-trust classes:

```text
anonymous_internal
rumor
```

Low-trust evidence can exist, but cannot be the only support for strong derived
review states.

Evidence links in claims should be structured when the support differs by
evidence item:

```yaml
evidence:
  - id: evidence:public:sec:apple-inc-2025-10k-revenue-note
    support_type: direct
    locator:
      section: Management's Discussion and Analysis
    methodology: null
```

A claim-level `support_type` is acceptable only when all linked evidence supports
the claim in the same way.

## Support Type

Allowed `support_type` values for claims:

```text
direct
observed
inferred
private_attestation
rumor
```

Compatibility rules:

```text
direct
  Requires evidence that directly states the assertion.
  Invalid when all evidence is rumor.

observed
  Requires firsthand_public evidence or a clearly attributed public observation.

inferred
  Requires either multiple evidence records or a methodology field.

private_attestation
  Requires firsthand_private or anonymous_internal evidence metadata.

rumor
  Requires rumor evidence and must remain low-trust in derived review state.
```

## Derived Review State

Derived review state is computed locally. It is not canonical truth and must not
be committed into claim, relationship, thesis, metric, event, or evidence files.

Derived review should be represented as one primary label plus zero or more flags.

Allowed primary labels:

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

Allowed flags:

```text
has_open_challenge
has_low_trust_support
has_private_support
has_contradiction
has_scope_limitation
has_staleness_risk
has_superseding_record
```

Minimal deterministic algorithm:

```text
withdrawn
  Record has withdrawn_by or a withdrawal validation.

superseded
  Record has superseded_by, duplicate_of, or lives under archive with a replacement.

stale
  Record has a stale validation/challenge or time-sensitive evidence past a configured freshness window.

contested
  Record has at least one open challenge, contradiction, or dispute/falsify validation.

low_trust_only
  All direct support paths depend only on anonymous_internal or rumor evidence.

supported
  Has at least one non-low-trust support path and no open challenge.

partially_supported
  Has support but also scope limitations, partial validations, or unresolved caveats.

unreviewed
  No validations, no challenges, and no derived support beyond its own cited evidence.
```

Primary-label tie-breaking order:

```text
withdrawn
superseded
stale
contested
low_trust_only
partially_supported
supported
unreviewed
```

Validations are not votes. Derived review state should de-duplicate repeated
reviews that rely on the same evidence path and should prefer source
independence over volume.

Example:

```json
{
  "primary_label": "supported",
  "flags": ["has_open_challenge", "has_scope_limitation"]
}
```

## Validations And Challenges

Use `submitted_by`, not `author`.

Validation verdicts:

```text
attests
supports
partially_supports
disputes
falsifies
marks_stale
withdraws
```

Challenge types:

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

Challenge anti-suppression rules:

- Open challenges must show in `fo review` and `fo context`.
- Closing or addressing a challenge should be append-only through a follow-up record or explicit `addressed_by`.
- A challenge should not be removed from current views merely because maintainers disagree with it.
- Archive PRs must not bury open challenges without `superseded_by`, `duplicate_of`, or `archive_reason`.

## IDs

IDs are stable and path-independent.

General ID shape:

```text
kind:domain:slug
```

Examples:

```text
entity:company:apple-inc
source:public:sec:apple-inc-2025-10k
evidence:public:sec:apple-inc-2025-10k-revenue-note
claim:apple-inc-tsmc-a-series-supply
relationship:apple-inc-tsmc-a-series-supply
validation:apple-inc-tsmc-a-series-supply-alice-20260602
challenge:apple-inc-tsmc-a-series-scope-bob-20260603
question:apple-inc-tsmc-customer-proof
```

Slug rules:

- lowercase ASCII
- words separated by hyphen
- remove punctuation unless meaningful for a registered identifier
- collapse repeated hyphens
- trim leading and trailing hyphens
- max recommended slug length: 96 characters

Collision rules:

- Prefer adding a disambiguating stable identifier such as CIK, LEI, exchange, period, or date.
- For validations/challenges, use target slug + contributor slug + date.
- For questions, use the proof gap or source surface being investigated.
- If collision remains, append a short deterministic suffix from the source ID or evidence ID.

Entity IDs should prefer stable names over tickers:

```yaml
id: entity:company:apple-inc
identifiers:
  ticker: AAPL
  cik: "0000320193"
```

Tickers are identifiers, not canonical entity IDs.

Supported v1 entity types include:

```text
company
person
product
component
security
listing
market
geography
architecture
commodity
technology
regulation
fund
service
```

## Paths

Paths are kind-first and domain-scoped.

Preferred current paths:

```text
entities/company/apple-inc.yml
sources/public/sec/apple-inc/2025-10k.yml
evidence/public/sec/apple-inc/2025-10k/revenue-note.yml
claims/company/apple-inc/tsmc-a-series-supply.yml
relationships/company/apple-inc/tsmc-a-series-supply.yml
theses/company/apple-inc/tsmc-margin-risk.yml
validations/company/apple-inc/tsmc-a-series-supply/alice-20260602.yml
challenges/company/apple-inc/tsmc-a-series-scope/bob-20260603.yml
questions/company/apple-inc/tsmc-customer-proof.yml
```

Cross-entity records should be anchored by the primary subject or buyer/customer
side when one exists. If no clear anchor exists, use the broader domain:

```text
relationships/market/ai-infrastructure/
claims/regulation/us-export-controls/
```

Archive paths mirror current paths:

```text
archive/claims/company/apple-inc/
archive/relationships/company/apple-inc/
archive/theses/company/apple-inc/
archive/debates/company/apple-inc/
```

## Archive Flags

Archive records remain valid data.

`fo lint` behavior:

```text
fo lint
  validates current records and archive records

fo lint --current-only
  validates current records only
```

Current-view commands exclude archive by default:

```text
fo search
fo context
fo review
fo graph neighbors
```

Include archive explicitly with:

```text
--include-archive
```

Archive records should include at least one of:

```text
superseded_by
duplicate_of
archive_reason
```

This is enforced by `fo lint`. Current records must not depend on archived
records by default. If a current record points to an archived record, the field
must be a lifecycle link such as `supersedes`, `corrects`, `restates`,
`narrows`, `broadens`, or `contradicts`.

`fo diff-review` should warn when a PR adds, updates, or moves records under
`archive/`.

## JSON CLI Output

All agent-facing commands should support `--json`.

Minimum commands:

```text
fo lint --json
fo graph build --json
fo graph neighbors ID --json
fo index build --json
fo search QUERY --json
fo context ID --json
fo review ID --json
fo diff-review BASE --json
```

JSON result envelope:

```json
{
  "ok": true,
  "command": "lint",
  "repo_root": "/path/to/repo",
  "records_checked": 0,
  "warnings": [],
  "errors": []
}
```

Warnings are advisory review pressure and do not set `ok` to false. Duplicate
warnings use `possible_duplicate_*` codes and include the first canonical
`record_id` plus sorted `related_ids`; archive records are excluded from this
duplicate pass.

Error shape:

```json
{
  "code": "missing_reference",
  "path": "claims/company/apple-inc/example.yml",
  "json_pointer": "/evidence/0",
  "message": "references missing id evidence:example",
  "hint": "Add the evidence record or fix the reference.",
  "record_id": "claim:example",
  "related_ids": ["evidence:example"]
}
```

Human output can remain concise, but JSON output is the contract agents should use.

## SQLite V1 Schema

SQLite database:

```text
.local/index.sqlite
```

Required tables:

```sql
create table records (
  id text primary key,
  kind text not null,
  schema_version integer,
  path text not null,
  archived integer not null default 0,
  label text,
  json text not null
);

create table refs (
  source_id text not null,
  target_id text not null,
  field_path text not null
);

create table edges (
  source_id text not null,
  target_id text not null,
  edge_type text not null,
  field_path text
);

create table entities (
  id text primary key,
  entity_type text not null,
  name text not null,
  ticker text,
  cik text
);

create table identifiers (
  record_id text not null,
  id_type text not null,
  id_value text not null
);

create table evidence (
  id text primary key,
  evidence_class text not null,
  source_id text,
  content_mode text,
  observed_at text
);

create table claims (
  id text primary key,
  predicate text not null,
  support_type text not null,
  subject text,
  object text,
  period_start text,
  period_end text,
  as_of text
);

create table relationships (
  id text primary key,
  relationship_type text not null,
  primary_subject text,
  effective_at text,
  period_start text,
  period_end text
);

create table relationship_participants (
  relationship_id text not null,
  role text not null,
  entity_id text not null
);

create table relationship_scope (
  relationship_id text not null,
  scope_type text not null,
  scope_id text not null
);

create table metrics (
  id text primary key,
  entity_id text not null,
  metric_definition text not null,
  value real,
  unit text,
  value_basis text,
  period_start text,
  period_end text,
  as_of text
);

create table events (
  id text primary key,
  event_type text not null,
  event_state text,
  occurred_at text,
  effective_at text
);

create table validations (
  id text primary key,
  target_id text not null,
  verdict text not null,
  submitted_by text
);

create table challenges (
  id text primary key,
  target_id text not null,
  challenge_type text not null,
  submitted_by text
);

create table predicate_definitions (
  id text primary key,
  ontology_version integer,
  json text not null
);

create table metric_definitions (
  id text primary key,
  ontology_version integer,
  json text not null
);

create table relationship_type_definitions (
  id text primary key,
  ontology_version integer,
  json text not null
);

create virtual table records_fts using fts5(
  id unindexed,
  kind unindexed,
  label,
  body
);
```

The index must be deterministic:

- rebuild from YAML only
- stable ordering
- no timestamps in generated rows unless sourced from records
- no embeddings in v1

## Public V1 Contract

Public v1 should support these canonical kinds:

```text
entity
source
evidence
claim
claim_predicate
metric_definition
metric
event
dataset
relationship_type
relationship
validation
challenge
question
thesis
```

Deferred from public v1:

```text
debate
argument
resolution
first-class forecast
trade/portfolio objects
```

Embeddings are also deferred from v1 derived tooling.

## Metric Definitions And Observations

Metrics require a lightweight definition registry plus observations.

Metric definition fields:

```text
schema_version
kind: metric_definition
id
label
description
value_type
allowed_units
allowed_basis
```

Metric observation fields:

```text
schema_version
kind: metric
id
metric_definition
entity
value
unit
scale
currency
basis
period
fiscal_year
fiscal_period
as_of
reported_at
published_at
segment
geography
product
customer
source_locator
xbrl_concept
restated_from
evidence
```

Company guidance is source-backed public information, not a thesis forecast. It
should be represented as an event, metric, claim, or management statement derived
from a source.

Contributor forecasts remain inside theses unless forecasting needs an
independent lifecycle.

## Events And Catalysts

Event fields:

```text
schema_version
kind: event
id
event_type
event_state
title
occurred_at
expected_at
effective_at
entities
evidence
properties
```

Allowed `event_state` values:

```text
expected
occurred
cancelled
missed
```

Catalysts are event records with `event_state: expected` until they occur,
miss, or are cancelled.

## Relationship Participant Contract

Relationship participants are a list, not a map, so repeated roles are possible:

```yaml
participants:
  - role: supplier
    entity: entity:company:tsmc
  - role: buyer
    entity: entity:company:apple-inc
```

Relationship type definitions must declare:

```text
ontology_version
required roles
optional roles
min/max cardinality per role
allowed entity kinds per role
allowed scope dimensions
allowed qualifiers
inverse behavior
```

Scope is not the same as participants:

```text
participants
  Entities playing roles in the relationship.

scope
  Product, segment, geography, channel, market, contract, technology, or period context.
```

Use scope for contextual dimensions unless the relationship type explicitly
defines a participant role.

## Typed Links

Use typed links instead of loose `related_to` wherever possible.

Allowed v1 link types:

```text
contradicts
supersedes
duplicate_of
corrects
restates
narrows
broadens
withdraws
```

`related_to` should be avoided in canonical records unless no typed link fits.

## Ontology Versioning

Ontology registry records should include:

```text
ontology_version
```

Applies to:

```text
claim_predicate
relationship_type
metric_definition
```

Ontology migrations should be explicit and should not silently reinterpret old
records.
