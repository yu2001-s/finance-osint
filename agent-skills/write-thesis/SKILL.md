---
name: write-thesis
description: Use when writing a thesis, interpretation, causal argument, or contributor forecast from explicit evidence, claim, metric, event, dataset, and relationship dependencies.
---

# Write Thesis

A thesis is interpretation. It may be opinionated, but dependencies must stay
explicit and canonical evidence must remain intact.

## Workflow

1. Gather context:

```bash
uv run fo context claim:... --json
uv run fo context relationship:... --json
uv run fo review ID --json
```

2. Draft a thesis only from explicit dependencies.

3. Create the thesis with explicit dependencies:

```bash
uv run fo new thesis \
  --title "Thesis title" \
  --summary "Interpretation built from explicit dependencies." \
  --claim claim:... \
  --relationship relationship:... \
  --evidence evidence:... \
  --submitted-by github:USERNAME \
  --json
```

4. Validate:

```bash
uv run fo lint --json
uv run fo review thesis:... --json
```

## Quality Bar

A thesis should make its reasoning inspectable:

```yaml
pillars:
  - statement: "Narrow pillar built from explicit dependencies."
    proof_points:
      - "Observable evidence that would strengthen this pillar."
    kill_criteria:
      - "Observable evidence that would weaken or break this pillar."
next_missing_evidence:
  - "Specific source, metric, event, or relationship still needed."
```

Use `pillars` and `next_missing_evidence` only when they are grounded in the
listed dependencies. If a thesis cannot name proof points or kill criteria, add
a question or challenge first.

## Forecasts

Contributor forecasts belong inside thesis records:

```yaml
forecast:
  metric_definition: metric_definition:revenue
  entity: entity:company:example
  period:
    start: "YYYY-MM-DD"
    end: "YYYY-MM-DD"
  expected_value:
    operator: "<"
    value: 0
    unit: USD
```

## Boundaries

- Do not alter evidence to fit a thesis.
- Do not represent a thesis as a claim.
- Do not add first-class trade or portfolio objects.
- Do not add truth `status` or `confidence`.
