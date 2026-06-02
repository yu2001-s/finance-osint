---
name: validate-or-challenge
description: Use when reviewing an existing evidence, claim, metric, event, relationship, or thesis by adding an append-only validation or challenge record.
---

# Validate Or Challenge

Validation evaluates support. Challenge records unresolved pressure.

## Workflow

1. Inspect the target:

```bash
uv run fo context ID --json
uv run fo review ID --json
```

2. Add a validation when giving a targeted support verdict:

```bash
uv run fo new validation \
  --target ID \
  --verdict supports \
  --summary "Why the cited dependencies support the target." \
  --evidence evidence:... \
  --submitted-by github:USERNAME \
  --json
```

3. Add a challenge when there is unresolved pressure:

```bash
uv run fo new challenge \
  --target ID \
  --challenge-type missing_evidence \
  --summary "What is missing or wrong." \
  --claim claim:... \
  --submitted-by github:USERNAME \
  --json
```

4. Recheck review state:

```bash
uv run fo lint --json
uv run fo review ID --json
```

## Verdicts

```text
attests
supports
partially_supports
disputes
falsifies
marks_stale
withdraws
```

## Challenge Types

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

## Boundaries

- Do not delete contested records to settle disagreement.
- Do not treat validation count as truth.
- Do not close a challenge by removing it; use append-only links such as `addressed_by`.
