---
name: add-relationship
description: Use when creating typed graph relationships among entities from explicit evidence or claims, including participants, scope, materiality, and ontology checks.
---

# Add Relationship

Relationships are typed graph objects. Relationship type defines participants;
scope defines context.

## Workflow

1. Inspect the candidate claim/evidence:

```bash
uv run fo context claim:... --json
uv run fo context evidence:... --json
```

2. Inspect relationship types:

```bash
uv run fo search supplier_relationship --json
```

3. Create the relationship with explicit participants:

```bash
uv run fo new relationship \
  --type supplier_relationship \
  --participant buyer=entity:company:buyer \
  --participant supplier=entity:company:supplier \
  --derived-claim claim:... \
  --derived-evidence evidence:... \
  --scope product=entity:product:... \
  --submitted-by github:USERNAME \
  --json
```

4. Validate and inspect graph context:

```bash
uv run fo lint --json
uv run fo graph neighbors relationship:... --json
```

## Boundaries

- Do not duplicate inverse relationships unless explicitly justified.
- Do not put context entities in participants unless the relationship type defines that role.
- Do not invent relationship types when a broad registered type plus rich scope works.
- Use `provisional:` only with a proposed relationship type definition.
