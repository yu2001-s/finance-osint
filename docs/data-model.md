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
relationship_type
relationship
thesis
```

Debate, argument, and resolution records are deferred from public v1. Prototype
examples live under `examples/deferred/`.

## Layers

```text
Source -> Dataset -> Evidence -> Metric/Event/Claim -> Relationship -> Thesis
                              -> Validation/Challenge
```

Source
  Provenance metadata for a filing, transcript, page, dataset, meeting,
  observation, or report.

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

Relationship
  A typed graph object connecting entities through participants, scope, time,
  materiality, and provenance.

Thesis
  A broader interpretation or forecast built from evidence, claims, metrics,
  events, datasets, and relationships.

## Relationship Ontology

Registered relationship types live in `relationship-types/`.

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

## Local Derived State

Canonical records do not store truth `status` or `confidence`. Tools derive
review state locally from evidence, validations, challenges, contradictions, and
supersession links.

`fo graph build` writes `.local/graph.json`. This file is derived from repo data
and ignored by git.
