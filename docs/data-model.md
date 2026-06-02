# Data Model

The repo separates observed evidence from interpretation.

## Object Types

```text
entity
source
evidence
claim
validation
challenge
relationship_type
relationship
thesis
debate
argument
resolution
```

## Truth Layers

```text
Source
  A provenance record for where information came from.

Evidence
  A quote, excerpt, table, observation, meeting note, or source report.

Claim
  A narrow, checkable statement backed by evidence.

Validation
  An append-only review record that attests, corroborates, disputes, falsifies, or marks an object stale.

Challenge
  An append-only objection about missing evidence, source quality, scope, ontology, materiality, or legal risk.

Relationship
  A typed graph object connecting entities through roles, scope, time, materiality, and provenance.

Thesis
  A broader interpretation or forecast built from evidence, claims, and relationships.

Debate
  Structured adversarial review around a claim, relationship, thesis, or question.
```

## Relationship Ontology

Registered relationship types live in `relationship-types/`.

If the graph needs a new type, contributors may use a provisional type:

```yaml
type: provisional:critical_tooling_dependency
proposed_type_definition: relationship-types/proposals/critical_tooling_dependency.yml
```

The validator allows provisional types only when a proposed definition exists.

Relationship instances are checked against their type definition:

- participant roles must be allowed by the type
- participant entity types must match the role
- scope keys must be allowed by the type
- qualifiers must be allowed by the type
- materiality values must be allowed by the type
- evidence-required types need evidence or claims

## Evidence Policy

`E4_anonymous_internal` and `E5_unverified_rumor` may be recorded, but they are low-trust classes. They cannot be the only support path for a corroborated or falsified claim, relationship, or validation.

First-hand evidence classes must declare attribution, source access, and risk flags so readers can filter or discount them locally.

## Local Derived State

`fo graph build` writes `.local/graph.json`. This file is derived from repo data and ignored by git.
