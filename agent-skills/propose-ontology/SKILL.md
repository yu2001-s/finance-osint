---
name: propose-ontology
description: Use when a needed claim predicate, relationship type, metric definition, entity type, event type, proof type, or risk flag vocabulary is missing.
---

# Propose Ontology

Use this skill when existing registries cannot represent the evidence precisely.
Prefer one narrow proposal over broad vocabulary expansion.

## Workflow

1. Search the existing registry:

```bash
uv run fo search claim_predicate --json
uv run fo search relationship_type --json
uv run fo search metric_definition --json
```

2. If a registered term works with scope, qualifiers, or dimensions, use it.

3. If a new term is needed, add a proposed registry record using the matching
   schema/template and keep `state: proposed`.

4. Link provisional records to the proposed definition:

```yaml
predicate: provisional:new_predicate
proposed_predicate_definition: ontology/claim-predicates/proposals/new_predicate.yml
```

```yaml
type: provisional:new_relationship_type
proposed_type_definition: ontology/relationship-types/proposals/new_relationship_type.yml
```

5. Validate:

```bash
uv run fo lint --json
```

## Boundaries

- Do not create ontology terms for one contributor's wording preference.
- Do not use provisional terms without a proposed registry record.
- For seed migration, prefer proposals for missing metric definitions before
  migrating dependent metrics.
