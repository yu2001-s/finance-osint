---
name: add-entity
description: Use when adding companies, people, products, components, securities, listings, markets, geographies, architectures, facilities, manufacturing processes, commodities, technologies, regulations, funds, or services.
---

# Add Entity

Entities are graph nodes. Add them only when records need a stable canonical ID.

## Workflow

1. Search first:

```bash
uv run fo index build --json
uv run fo search "company product component aliases" --json
```

2. Create the entity with deterministic fields:

```bash
uv run fo new entity \
  --entity-type company \
  --name "Example Company" \
  --identifier ticker=EXM \
  --submitted-by github:USERNAME \
  --json
```

3. Validate:

```bash
uv run fo lint --json
```

## Boundaries

- Do not create fake company entities for unnamed customers, suppliers, or sources.
- If the counterparty is unnamed, keep it as a typed descriptor in metric dimensions,
  claim qualifiers, relationship scope, question text, or risk flags until named evidence exists.
- Do not use entities as weak claims. A company/product node only means the repo
  needs an ID, not that any relationship is true.
