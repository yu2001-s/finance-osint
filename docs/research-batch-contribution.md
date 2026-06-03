# Research Batch Contribution

Use this workflow when adding a source-backed public-equity research batch by
hand or with an agent. The PR submitter owns the output.

## Start From Explicit Material

Every batch starts from material that is:

- already in the repo
- supplied by the contributor
- added as source records in the PR

Do not add hidden source knowledge, hidden agent state, private reviewer notes,
canonical truth `status`, or canonical `confidence`.

## Scope The Batch

Before writing records, define:

- the company, product, market, technology, event, or relationship being studied
- the primary sources being added or reused
- the question the batch helps answer
- what the batch will not prove

Prefer small batches. A focused source-to-claim chain is easier to review than
a broad thesis with weak dependencies.

## Add Layers In Order

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

Stop at the strongest layer the evidence supports. If the source only says a
company introduced a product, do not create a customer relationship or revenue
bridge.

## Use Conservative Promotion

Promote a relationship only when evidence supports the exact edge:

- A named foundry relationship can support `manufacturing_partner`.
- A named supplier statement can support `supplier_relationship` if buyer,
  seller, item, scope, and timing are clear enough.
- A qualification or AVL statement can support `qualified_supplier` only when
  approval or qualification is actually disclosed.
- A product composition statement can support `uses_component`.
- A customer or revenue allocation claim needs customer-specific support, not
  only segment revenue or broad market exposure.

When order value, volume, margin, customer allocation, BOM/AVL status, timing,
or valuation conversion is missing, add a question or challenge.

## Use Metrics And Events

Do not bury structured observations inside prose:

- revenue, backlog, market cap, ownership, price-to-sales, gross margin,
  shipments, opportunity pipeline, and allocation share belong in `metric`
  records when numeric support exists.
- orders, filings, permits, approvals, expected ramps, shipments, product
  launches, financing, and missed/cancelled milestones belong in `event`
  records when timing support exists.

Use `value_basis` conservatively:

```text
reported
observed
derived
estimated
restated
```

Derived or estimated metrics should name their input metrics, evidence, method,
and limitations.

## Write Claims Narrowly

Claims should be checkable. Use `support_type`:

```text
direct
observed
inferred
private_attestation
rumor
```

If the claim predicate does not exist, add a proposed claim predicate under
`ontology/claim-predicates/proposals/` and link it from the claim.

## Write Theses As Interpretations

A thesis should name:

- dependencies
- core evidence
- open proof gaps
- observable next evidence
- time horizon
- challenge or kill criteria

A thesis is not a truth label. It is an argument that readers can inspect,
challenge, validate, narrow, or supersede.

## Run Local Review

Use the branch point or pull-request base:

```bash
BASE=origin/main
```

Run:

```bash
uv run fo lint --json
uv run python -m unittest discover -s tests
uv run fo index build --json
uv run python scripts/chain_review_changed.py "$BASE"
uv run fo graph build --json
uv run fo diff-review "$BASE" --json
uv run fo view build "$BASE" --json
```

For key relationships and theses:

```bash
uv run fo review RECORD_ID --chain --json
```

Review every warning. Warnings are review items even when CI passes.

## PR Summary

Include:

- records added or changed by kind
- main source and evidence IDs
- evidence classes and source perspectives
- strong relationships promoted and why the scope fits
- metrics/events added and their value basis
- open questions and challenges
- every `fo diff-review` warning and how it was handled
- generated `.local/github-view/pr-review.md` or CI `github-view` artifact notes
