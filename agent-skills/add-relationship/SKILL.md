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

Prefer the narrowest registered type the evidence actually supports:

- `supplier_relationship` / `customer_relationship` for broad buyer-seller edges.
- `qualified_supplier` for approval or qualification.
- `design_win` for designed-in products, components, technologies, or services.
- `capacity_expansion_for` for capacity ramps tied to output, market, customer, or time window.
- `uses_component` for product/architecture composition.
- `substitutes_for` for functional or economic substitution.
- `manufacturing_partner` for foundry, contract manufacturing, assembly, packaging, or test.

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
- Do not upgrade a broad supplier/customer mention into qualification, design-in, or capacity linkage without evidence.
- Do not add `scope.market` to generic product/manufacture relationships unless
  the supporting claim or evidence also supports that market relevance.
- Do not invent relationship types when a registered type plus rich scope works.
- Use `provisional:` only with a proposed relationship type definition.
