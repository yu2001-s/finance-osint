# Schema Migration V1

This document maps the current scaffold to the first public data contract.
It is an implementation checklist, not a new design source. If this document
conflicts with `docs/contracts.md`, the contract wins.

## Goal

Move the repository from the current prototype schema to public v1:

- local-first YAML records remain the canonical database
- every canonical record has `schema_version: 1`
- humans and agents use the same records and contributor accountability model
- canonical records do not store derived truth labels such as confidence/status
- metrics, events, datasets, predicates, and relationship ontology are supported
  before public launch
- agent-facing commands expose stable JSON output

## Preconditions

Before code changes:

- `docs/design-decisions.md` captures the settled philosophy
- `docs/contracts.md` captures the implementation contract
- this migration doc captures the order of schema, template, validator, CLI, and
  fixture changes

Public data has not launched yet, so v1 may update existing synthetic fixtures
directly. After public launch, future changes should use migration notes under
`schemas/migrations/`.

## Public V1 Kinds

Public v1 supports:

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
thesis
```

Deferred from public v1:

```text
debate
argument
resolution
first-class forecast
trade or portfolio expression
embeddings
```

Existing debate fixtures should move to `archive/debates/` or
`examples/deferred/debates/` before public v1. They should not be part of the
required v1 validator surface until debate is promoted back into the public
contract.

## Global Field Migration

Apply to every canonical record:

```text
add schema_version: 1
use submitted_by for contributor accountability
remove agent-specific provenance fields if any appear
keep IDs stable and path-independent
```

Do not use these canonical fields for claim, relationship, thesis, metric,
event, or evidence truth:

```text
status
confidence
```

If an object needs lifecycle state for ontology administration, use `state`
instead of `status` so it is not confused with derived truth. Examples:

```text
relationship_type.state: registered | proposed | retired
claim_predicate.state: registered | proposed | retired
metric_definition.state: registered | proposed | retired
```

Use typed lifecycle links rather than truth status:

```text
contradicts
supersedes
superseded_by
duplicate_of
corrects
restates
narrows
broadens
withdrawn_by
addressed_by
archive_reason
```

Avoid loose `related_to` links in v1 schemas.

## Kind-By-Kind Migration

### Entity

Current files:

```text
entities/
```

Target changes:

- add `schema_version: 1`
- support v1 entity types from `docs/contracts.md`
- keep canonical IDs stable and name-based, not ticker-based
- keep tickers, CIKs, LEIs, FIGIs, and exchange codes under `identifiers`
- use `state` only for operational lifecycle if needed

Supported v1 entity types:

```text
company
person
product
component
security
listing
market
geography
commodity
technology
regulation
fund
service
```

Example:

```yaml
id: entity:company:apple-inc
identifiers:
  ticker: AAPL
  cik: "0000320193"
```

### Source

Current files:

```text
sources/
```

Target changes:

- add `schema_version: 1`
- require `source_type`, `title`, `public_status`, `accessed_at`, and
  `content_mode`
- use `source_type: sec_filing` for SEC filings
- add SEC fields when applicable:
  `accession_number`, `form_type`, `filing_date`, `accepted_at`,
  `period_of_report`, `amends`, `url`, `archive_url`, `content_hash`
- store metadata, URLs, hashes, excerpts, and summaries rather than large raw
  files

### Evidence

Current files:

```text
evidence/
```

Target changes:

- add `schema_version: 1`
- rename evidence classes:

```text
E0_public_primary -> public_primary
E1_public_secondary -> public_secondary
E2_firsthand_public -> firsthand_public
E3_firsthand_private -> firsthand_private
E4_anonymous_internal -> anonymous_internal
E5_unverified_rumor -> rumor
```

- remove canonical `status`
- rename `attribution` to `source_attribution`
- remove `anonymous_to_maintainers`
- add `content_mode`
- keep `source_access`, `verification_status`, and `risk_flags` for private,
  anonymous, or low-trust evidence

Allowed `source_attribution` values:

```text
named_public
anonymous_to_public
unknown
```

### Claim Predicate

New public v1 registry:

```text
claim-predicates/
claim-predicates/proposals/
schemas/claim-predicate.schema.json
templates/claim-predicate.yaml.template
```

Target fields:

```text
schema_version
kind
id
name
state
ontology_version
required_fields
allowed_support_type
allowed_subject_kinds
allowed_object_kinds
may_reference
```

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

If a predicate is not registered yet, contributors may use:

```yaml
predicate: provisional:channel_inventory_signal
proposed_predicate_definition: claim-predicates/proposals/channel_inventory_signal.yml
```

### Claim

Current files:

```text
claims/
```

Target changes:

- add `schema_version: 1`
- remove required canonical `status`
- remove required canonical `confidence`
- require `support_type` when all linked evidence supports the claim the same
  way
- allow structured evidence links when support differs by evidence item
- require registered or provisional predicate
- allow references to metrics, events, datasets, and relationships when the
  predicate definition permits them

Target evidence link shape:

```yaml
support_type: inferred
evidence:
  - id: evidence:public:sec:example
  - id: evidence:public:transcript:example
```

When evidence support differs:

```yaml
evidence:
  - id: evidence:public:sec:example
    support_type: direct
  - id: evidence:public:survey:example
    support_type: observed
    methodology: "Store check sample across three locations."
```

### Metric Definition

New public v1 registry:

```text
metric-definitions/
metric-definitions/proposals/
schemas/metric-definition.schema.json
templates/metric-definition.yaml.template
```

Target fields:

```text
schema_version
kind
id
name
state
ontology_version
value_type
default_unit
allowed_units
allowed_value_basis
required_dimensions
optional_dimensions
source_requirements
```

The first registry should include a small set only, such as revenue,
gross_margin, unit_shipments, shares_outstanding, ownership_percent, and
customer_concentration_percent.

### Metric

New public v1 records:

```text
metrics/
schemas/metric.schema.json
templates/metric.yaml.template
```

Target fields:

```text
schema_version
kind
id
entity
metric_definition
value
unit
period
value_basis
evidence
source_locator
as_of
reported_at
published_at
restated_from
dimensions
methodology
limitations
```

Metrics are evidence-backed numeric records. They may be reported, observed,
derived, estimated, or restated. Future expectations from contributors stay in
thesis forecasts, not metric records.

### Event

New public v1 records:

```text
events/
schemas/event.schema.json
templates/event.yaml.template
```

Target fields:

```text
schema_version
kind
id
event_type
event_state
title
entities
occurred_at
expected_at
effective_at
period
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

Catalysts are expected events. Company guidance should be recorded as a
source-backed event, metric, claim, or management statement, not as a
contributor forecast.

### Dataset

New public v1 records:

```text
datasets/
schemas/dataset.schema.json
templates/dataset.yaml.template
```

Target fields:

```text
schema_version
kind
id
title
dataset_type
publisher
coverage
access
sources
content_mode
content_hash
license
limitations
```

Datasets describe collections. Evidence and metrics should reference the
specific row, excerpt, observation, or value used.

### Relationship Type

Current files:

```text
relationship-types/
```

Target changes:

- add `schema_version: 1`
- rename administrative `status` to `state`
- add `ontology_version`
- define required and optional roles
- include min/max cardinality per role
- define allowed entity kinds per role
- define allowed scope, qualifiers, and materiality values
- define inverse behavior as derived-local unless a duplicate canonical record
  is explicitly justified

Role definition example:

```yaml
roles:
  - name: buyer
    required: true
    min: 1
    max: 1
    allowed_entity_types: [company]
  - name: supplier
    required: true
    min: 1
    max: null
    allowed_entity_types: [company]
```

### Relationship

Current files:

```text
relationships/
```

Target changes:

- add `schema_version: 1`
- change ID prefix from `rel:` to `relationship:`
- remove canonical `status`
- remove canonical `confidence`
- change `participants` from map/object to list
- keep scope separate from participants
- validate participant roles against the relationship type definition
- use typed contradiction/supersession links

Target participant shape:

```yaml
participants:
  - role: buyer
    entity: entity:company:exdev
  - role: supplier
    entity: entity:company:fndwy
```

Scope example:

```yaml
scope:
  products:
    - entity:product:example-phone
  components:
    - entity:component:x1-processor
  geographies:
    - entity:geography:global
```

### Validation

Current files:

```text
validations/
```

Target changes:

- add `schema_version: 1`
- use `submitted_by`, not `author`
- remove canonical `confidence`
- remove truth `status` if present
- update verdict vocabulary
- keep validation as append-only review of support

Target verdicts:

```text
attests
supports
partially_supports
disputes
falsifies
marks_stale
withdraws
```

Prototype migration:

```text
corroborates -> supports
partially_corroborates -> partially_supports
```

### Challenge

Current files:

```text
challenges/
```

Target changes:

- add `schema_version: 1`
- use `submitted_by`, not `author`
- remove canonical truth `status`
- keep challenge as unresolved pressure
- model closure append-only with `addressed_by`, `withdrawn_by`, or
  `superseded_by`

Target challenge types:

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

Open challenges must stay visible in review and context commands. Archive should
not suppress them.

### Thesis

Current files:

```text
theses/
```

Target changes:

- add `schema_version: 1`
- remove canonical truth `status`
- remove canonical `confidence`
- keep stance, dependency graph, assumptions, and forecast expression
- allow dependencies on evidence, claims, metrics, events, datasets, and
  relationships
- use typed contradiction/supersession links

Forecasts remain inside thesis records:

```yaml
forecast:
  metric_definition: metric_definition:revenue
  entity: entity:company:exdev
  period:
    start: "2026-01-01"
    end: "2026-12-31"
  expected_value:
    operator: "<"
    value: 1500000000
    unit: USD
```

## Validator Migration

Update `fosint/cli.py` and tests after schemas/templates are migrated.

Required validator changes:

- load public v1 directories:
  `claim-predicates`, `metric-definitions`, `metrics`, `events`, `datasets`
- remove public v1 required loading for `debates`, `arguments`, and
  `resolutions`
- validate archive by default; add `--current-only`
- require `schema_version: 1`
- reject `anonymous_to_maintainers`
- reject old evidence classes
- reject canonical truth `status` and `confidence` on v1 claim, relationship,
  thesis, metric, event, and evidence records
- validate claim predicate registry references
- validate provisional predicate definition paths
- validate support type compatibility with evidence class and methodology
- validate relationship type registry references
- validate relationship participants against role cardinality and entity types
- validate `relationship:` ID prefix and keep `rel:` as invalid in v1
- validate typed links resolve to known records
- report open challenges in review/context commands even when target records are
  archived

JSON CLI output should use the envelope and error shape defined in
`docs/contracts.md`.

## CLI Migration Order

Implement in this order:

1. Update schemas for existing v1 kinds.
2. Add schemas for new v1 kinds.
3. Update templates.
4. Migrate synthetic fixtures.
5. Update validator loading and cross-reference checks.
6. Add `fo lint --json`.
7. Add archive behavior: `fo lint` and `fo lint --current-only`.
8. Add `.local/graph.json` compatibility with v1 references.
9. Add `.local/index.sqlite` with `fo index build --json`.
10. Add read commands: `fo search`, `fo context`, `fo review`, and
    `fo graph neighbors`, all with `--json`.
11. Add write helpers only after read/index behavior is stable.

Do not add embeddings in v1.

## Current Synthetic Fixture Migration

The existing EXDEV/FNDWY fixture should migrate as the first concrete example.

Expected changes:

- add `schema_version: 1` to every fixture
- convert evidence class `E0_public_primary` to `public_primary`
- remove evidence `status`
- rename evidence `attribution` to `source_attribution`
- set synthetic fixture `content_mode: small_fixture`
- remove claim `status` and `confidence`
- add claim `support_type`
- register or provision the claim predicate used by the fixture
- change relationship ID from `rel:...` to `relationship:...`
- convert relationship participants from object map to list
- remove relationship `status` and `confidence`
- update relationship type definitions with roles, cardinality, and
  `ontology_version`
- update validation verdicts to v1 vocabulary
- remove validation `confidence`
- update challenge closure fields if needed
- move debate fixture out of required v1 validation

## Test Plan

After implementation:

```bash
uv run fo lint
uv run fo lint --json
uv run fo lint --current-only
uv run python -m unittest discover -s tests
uv run fo graph build
uv run fo graph build --json
uv run fo index build --json
uv run fo search exdev --json
uv run fo context relationship:synthetic-exdev-fndwy-x1-supply --json
uv run fo review relationship:synthetic-exdev-fndwy-x1-supply --json
```

`fo lint --json` should be the main agent contract for PR automation.

## Non-Goals

This migration does not implement:

- hidden moderation
- maintainer-only source trust
- agent provenance in canonical records
- investment recommendation policing
- legal review workflows
- embeddings
- hosted database or server synchronization
