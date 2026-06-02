---
name: add-question
description: Use when recording an open proof gap or next investigation target for humans or agents.
---

# Add Question

Use a question when the repo needs to remember what would prove, weaken, or
kill a claim, relationship, or thesis. A question is not a truth status and
should not assert the answer.

## Workflow

1. Identify the target proof gap and the related entities.
2. Link any existing evidence, claims, relationships, or theses that motivated
   the question.
3. Create the record with deterministic inputs:

```bash
uv run fo new question \
  --question "Can any customer-side source name FOCI as FAU supplier?" \
  --entity entity:company:foci \
  --entity entity:company:nvidia \
  --proof-type customer_side_bom_or_avl \
  --priority high \
  --related-claim claim:foci:relfacon-product-fit \
  --related-relationship relationship:foci-nvidia-fau-unproven \
  --next-action "Search NVIDIA service, procurement, BOM, and replacement-part sources." \
  --submitted-by github:username \
  --json
```

4. Run validation:

```bash
uv run fo lint --json
```

## Rules

- Do not use a question as a weak claim.
- Do not store truth `status` or `confidence`.
- Resolve by adding follow-up evidence, claims, relationships, validations,
  challenges, or theses, then link them through `resolved_by`.
