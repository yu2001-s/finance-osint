# Chroma ATE Seed Review

Review date: 2026-06-03

Batch target: `thesis:chroma-ate:cpo-insertion-test-watch`

## Decision

Pass for continued seeding. The batch adds a useful stress case for
transcript-hosted purchase-order language without overpromoting it into a named
customer, supplier, qualified-supplier, or design-win relationship.

## Deterministic Review

`fo diff-review HEAD --json` before checkpointing the batch reported:

- 27 changed paths.
- 25 added records.
- 2 modified metric definitions.
- 100 added graph edges.
- No errors.
- Expected warnings only: open challenge, ontology changes, and derived review
  state changes.

Added record mix:

```text
challenge: 1
claim: 5
entity: 3
event: 1
evidence: 4
metric: 3
question: 1
relationship: 2
source: 4
thesis: 1
```

`fo review thesis:chroma-ate:cpo-insertion-test-watch --json` reported:

- Derived review state: `contested`.
- Open challenges: 1.
- Support evidence: 4 records.
- Evidence classes: 1 `public_primary`, 3 `public_secondary`.
- Source perspectives: 2 `company_self`, 1 `independent_research`, 1
  `aggregator`.

## Source-To-Claim Chain

The chain is intact:

```text
source:public:chroma-ate:siph-pic-reliability-test-solutions
  -> evidence:public:chroma-ate:siph-pic-reliability-test-solutions
  -> claim:chroma-ate:siph-pic-reliability-test-product-fit
  -> relationship:chroma-ate:manufactures-siph-pic-reliability-test-systems

source:public:chroma-ate:q1-2026-earnings-call-transcript
  -> evidence:public:chroma-ate:q1-2026-cpo-insertion-purchase-orders
  -> claim:chroma-ate:q1-2026-cpo-insertion-purchase-orders
  -> relationship:cpo-insertion-test-workflow:supports-cpo
  -> event:chroma-ate:insertion-4e-pilot-202606

source:public:stockanalysis:chroma-valuation-20260529
  -> evidence:public:market-data:chroma-valuation-20260529
  -> metrics and market-signal claim

source:public:stock-research:chroma-cpo-insertion-sidecar
  -> evidence:public:stock-research:chroma-proof-gaps
  -> claim/question/challenge for missing customer, order value, revenue, and margin proof
```

## What Held

- Purchase-order language stayed as a management-statement claim, not a
  customer relationship.
- The June 2026 Insertion 4E pilot was modeled as an expected month window, not
  an invented exact date.
- Market data was separated into observed market-cap and price-to-sales metrics,
  plus a reported TTM revenue metric from the market-data page.
- The thesis is explicitly watch-only and contested by a materiality challenge.

## Ontology Note

The batch required a small currency-unit registry update:

- `metric_definition:revenue` now allows `TWD`, `JPY`, `EUR`, and `HKD`.
- `metric_definition:market_cap` now allows `TWD`, `JPY`, `EUR`, and `HKD`.

This is justified by non-U.S. public-equity seeding. It keeps records explicit
instead of hiding currency under `local_currency`.

## Follow-Ups

Fix before next batch: none.

Carry forward:

- Do not turn unnamed purchase orders into customer relationships.
- Keep expected timing windows under `period` and timing metadata.
- Add a challenge when valuation is already rerated and revenue/order value is
  not bridged.

Watch during full chain review:

- Whether `source_attestation` is the right predicate for compiled negative
  search records, or whether negative search should stay evidence plus
  question/challenge only.
