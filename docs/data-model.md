# Data Model

The repo separates observed evidence, structured facts, review pressure, and
interpretation.

## Public V1 Object Types

```text
entity
source
evidence
claim_predicate
metric_definition
metric
event
dataset
claim
validation
challenge
question
relationship_type
relationship
thesis
```

Debate, argument, and resolution records are deferred from public v1. Prototype
examples live under `examples/deferred/`.

## Layers

```text
Source -> Dataset -> Evidence -> Metric/Event/Claim -> Relationship -> Thesis
                              -> Validation/Challenge/Question
```

Source
  Provenance metadata for a filing, transcript, page, dataset, meeting,
  observation, or report.

  `social_media_post` is a source type. It can directly support an attribution
  claim such as "account X said Y"; underlying company facts still need their
  own evidence chain.

Evidence
  A locator, excerpt, observation, row, table, or source-backed report.

Metric
  A structured numeric value with provenance.

Event
  A time-bound occurrence or expected occurrence.

Claim
  A narrow, checkable assertion backed by evidence.

Validation
  An append-only review record that evaluates support.

Challenge
  An append-only unresolved objection or counter-pressure.

Question
  An open proof gap or next investigation target. Questions do not assert truth
  and do not carry truth status; they are resolved by linking follow-up records.

Relationship
  A typed graph object connecting entities through participants, scope, time,
  materiality, and provenance.

Thesis
  A broader interpretation or forecast built from evidence, claims, metrics,
  events, datasets, and relationships.

## Relationship Ontology

Registered relationship types live in `relationship-types/`.

For supply-chain research, prefer precise relationship types when evidence
supports them:

- `supplier_relationship` / `customer_relationship`: broad buyer-seller edges.
- `qualified_supplier`: supplier approval or qualification.
- `design_win`: designed-in product, component, technology, or service.
- `capacity_expansion_for`: capacity tied to output, market, customer, or time window.
- `uses_component`: composition or product/architecture dependency.
- `substitutes_for`: functional or economic substitution.
- `manufacturing_partner`: foundry, contract manufacturing, assembly, packaging, or test.

Use broad relationship types when the source only supports a broad edge. Do not
turn a broad supplier mention into qualification, design-in, or capacity linkage
without evidence for that narrower relationship.

If the graph needs a new type, contributors may use a provisional type:

```yaml
type: provisional:critical_tooling_dependency
proposed_type_definition: relationship-types/proposals/critical_tooling_dependency.yml
```

Relationship instances are checked against their type definition:

- participant roles must be allowed by the type
- participant role cardinality must fit the type
- participant entity types must match the role
- scope keys must be allowed by the type
- qualifiers must be allowed by the type
- materiality values must be allowed by the type
- evidence-required types need evidence or claims

## Evidence Policy

Use plain evidence classes:

```text
public_primary
public_secondary
firsthand_public
firsthand_private
anonymous_internal
rumor
```

`anonymous_internal` and `rumor` are low-trust classes. They may be recorded, but
they cannot silently become strong factual support. Claims use `support_type` to
describe reasoning distance from the evidence.

First-hand, private, anonymous, and rumor evidence should declare
`source_attribution`, `source_access`, and `risk_flags` so readers and agents can
filter or discount it locally.

Sources may also declare `source_perspective`. This is provenance metadata, not
truth status. Review output uses it to expose whether support is company-originated,
independent, first-hand/social, anonymous/internal, synthetic, or unknown.

## Source Preservation

For mutable source types such as `web_page`, `news_article`, and
`research_report`, `url` alone is not enough. Prefer `archive_url`. If no archive
exists, preserve the source through source `content_hash`, a bounded
`evidence.excerpt`, or local `source_artifacts`.

`source_artifacts` may appear on source and evidence records:

```yaml
source_artifacts:
  - artifacts/sources/source-slug/screenshot-2026-06-03.png
```

Artifact rules:

- files must live under `artifacts/sources/`
- files must be referenced by a source or evidence record
- allowed file types are `png`, `jpg`, `jpeg`, and `pdf`
- each file must be 2 MB or smaller

`fo lint` warns when a mutable web-like source has no archive, hash, artifact,
or linked evidence excerpt. Invalid, missing, unreferenced, or oversized
artifacts are hard validation errors.

## Archive Policy

Archive is a path-level lifecycle state, not a truth status field. Current
records live in top-level data directories. Archived records live under
`archive/` and keep their canonical ID.

Archived records must include at least one of:

```text
superseded_by
duplicate_of
archive_reason
```

Current records must not depend on archived records by default. When a record is
archived, current dependents should either point to a current replacement or be
archived/updated in the same PR. Lifecycle links such as `supersedes`,
`corrects`, `restates`, `narrows`, `broadens`, and `contradicts` may point to
archived records.

`fo diff-review` warns when a PR adds, updates, or moves records under
`archive/`.

## Local Derived State

Canonical records do not store truth `status` or `confidence`. Tools derive
review state locally from evidence, validations, challenges, contradictions, and
supersession links.

`fo graph build` writes `.local/graph.json`. This file is derived from repo data
and ignored by git.

`fo index build` writes `.local/index.sqlite`. This file is also derived from
repo data and ignored by git. Agent-facing read commands use the index:

```bash
fo search QUERY --json
fo context ID --json
fo review ID --json
fo diff-review BASE --json
fo graph neighbors ID --json
```

`fo review` reports deterministic review state without writing truth back into
canonical records. The JSON includes `review_state` plus summaries for support
evidence, source independence, validation dependency paths, challenges,
contradictions, supersession, staleness, and scope limitations. Staleness is v1
explicit-signal only: a `marks_stale` validation, `outdated` challenge, or
matching risk flag.

`fo review RECORD --chain --json` keeps the same review surface and adds
`chain_summary`. This is the deterministic source-to-claim review layer for
agents and PR authors. It reports dependency IDs/counts, source/evidence chain
items, claim predicates, metric/event coverage, relationship types, open
questions, open challenges, relationship-promotion pressure, and risk-flag
categories. The command still does not write truth status or confidence back
into canonical records.

`fo diff-review BASE` is the deterministic PR review layer. It compares records
by canonical ID, validates the current tree, flags canonical evidence edits,
shows reference and graph impact, reports before/after derived review-state
movement, and highlights ontology changes. It uses Git only as the versioned
transport; the interpretation is based on OSINT records and graph structure.

`fo lint` emits advisory duplicate warnings for current records. It checks stable
deterministic signatures: entity names and key identifiers, source URLs and
hashes, evidence source plus locator/excerpt, claim subject/predicate/object
plus scope/evidence, and relationship type/participants/scope/time. Archived
records are ignored for duplicate warnings. Duplicate warnings do not fail lint;
contributors should clarify distinct records or archive/merge duplicates with
`duplicate_of` or `superseded_by`.

`fo new` helpers are deterministic record constructors. They create schema-valid
YAML from explicit arguments and then rely on the same validators used by CI.
They should not perform ingestion, summarization, or semantic inference.

The common v1 contribution path is covered by helpers for entity, source,
evidence, claim, metric, event, dataset, validation, challenge, question,
relationship, and thesis records. Ontology-definition helpers remain deferred.
