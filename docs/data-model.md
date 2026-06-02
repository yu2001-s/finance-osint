# Data Model

The repo separates observed evidence from interpretation.

## Object Types

```text
entity
source
evidence
claim
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

## Local Derived State

`fo graph build` writes `.local/graph.json`. This file is derived from repo data and ignored by git.

