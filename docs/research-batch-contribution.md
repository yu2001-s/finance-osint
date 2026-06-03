# Research Batch Contribution Workflow

Use this when adding a sourced public-equity research batch by hand or with an
agent. The PR submitter owns the output.

## Start From Explicit Material

Every batch starts from material already in the repo, supplied by the user, or
added as source records. Do not add hidden source knowledge, hidden agent state,
`agent_run`, `generated_by`, canonical `status`, or canonical `confidence`.

For stock-research migration, use the frozen snapshot recorded in
`docs/stock-research-seed-snapshot.yml`, not the moving source worktree.

## Add Records In Layers

Add only the layers the batch needs, in this order:

```text
entity
source
evidence
metric / event / dataset
claim
relationship
question / challenge / validation
thesis
```

Do not write a thesis first. Do not create a relationship until its supporting
claim or evidence exists.

## Keep Boundaries Clear

- `source`: where the information came from.
- `evidence`: bounded excerpt, summary, observation, or proof packet from a
  source.
- `metric`: reported, observed, derived, estimated, or restated numeric fact.
- `event`: occurred or expected timing record.
- `claim`: narrow statement backed by evidence.
- `relationship`: typed graph edge derived from evidence, claims, metrics, or
  events.
- `question`: open proof gap or next investigation target.
- `challenge`: open objection or pressure on an object.
- `thesis`: interpretation or forecast that depends on explicit records.

## Use Conservative Promotion

Promote a relationship only when the evidence supports that exact edge.

Good examples from seeded batches:

- Navitas naming X-FAB as U.S. manufacturer supports a scoped
  `manufacturing_partner` relationship.
- FIT plus Broadcom naming FIT TH5-Bailly CPO interconnect hardware supports a
  scoped `supplier_relationship`.
- Chroma purchase-order language supports a management-statement claim, not a
  named customer relationship.
- FOCI/Himax demo and planned-delivery evidence supports collaboration and
  product-fit records, not NVIDIA/TSMC/COUPE supplier allocation.

When revenue, order value, margin, customer allocation, BOM/AVL, or valuation
conversion is missing, add a question and challenge instead of stretching the
relationship.

## Write Theses As Contested Interpretations

A seed thesis should name:

```text
dependencies
core evidence
open proof gaps
observable next evidence
time horizon
challenge or kill criteria
```

It should not encode a truth status. The canonical truth surface is the evidence
and reported metrics; the thesis is the interpretation layer.

## Run Local Review

Set the base to the branch point or PR base:

```bash
BASE=HEAD
```

Before opening a PR, run:

```bash
uv run fo lint --json
uv run python -m unittest discover -s tests
uv run fo index build --json
uv run python scripts/chain_review_changed.py "$BASE"
uv run fo graph build --json
uv run fo diff-review "$BASE" --json
uv run fo view build "$BASE" --json
```

For the main thesis or any strong relationship, also run:

```bash
uv run fo review RECORD_ID --chain --json
```

Review every warning. Warnings are not automatic failures, but they are review
items.

## PR Summary Checklist

In the PR, summarize:

- Records added or changed by kind.
- Main sources and evidence classes.
- Any company-only, counterparty, independent, market-data, social, or compiled
  research support.
- Strong relationships promoted and why they are scoped correctly.
- Open questions and challenges.
- `fo diff-review`, `chain_review_changed.py`, and generated
  `.local/github-view/pr-review.md` results.
