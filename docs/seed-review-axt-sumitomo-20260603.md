# AXT / Sumitomo Seed Review

Review date: 2026-06-03

Seed commit: `d993f34` (`Seed AXT Sumitomo InP substrate watch`)

Migration-guidance base: `ffbf138` (`Add stock research seed migration guidance`)

Target thesis: `thesis:axt-sumitomo:inp-substrate-bottleneck-watch`

## Decision

Pass for continued controlled seeding. The batch is a useful first real-data
test because it preserves the evidence layer, avoids turning old research labels
into truth fields, and keeps the interpretation contested where proof is missing.

No blocking schema change is required before the next seed batch.

## Deterministic Review

`fo diff-review ffbf138 --json` on the committed seed batch reports:

- 71 added records.
- 256 added graph edges.
- No errors.
- Expected warnings only: open challenges, ontology addition, and derived review
  state changes.

Record mix:

```text
challenge: 2
claim: 9
entity: 8
event: 2
evidence: 14
metric: 9
metric_definition: 1
question: 4
relationship: 8
source: 13
thesis: 1
```

`fo review thesis:axt-sumitomo:inp-substrate-bottleneck-watch --json` reports:

- Derived review state: `contested`.
- Open challenges: 2.
- Support evidence: 12 records.
- Evidence classes: 9 `public_primary`, 3 `public_secondary`.
- Source perspectives: 8 `company_self`, 1 `independent_research`, 1
  `aggregator`.

## Lens Review

### Data Integrity

Keep.

The batch keeps source, evidence, claim, metric, event, relationship, question,
challenge, and thesis boundaries separate. It does not add hidden agent state,
`generated_by`, `agent_run`, canonical `status`, or canonical `confidence`.

The old stock-research proof gaps were not copied as truth. They were translated
into evidence limitations, questions, thesis caveats, and challenges.

### Ontology

Keep.

The only new ontology record is `metric_definition:backlog_value`. That is the
right addition because backlog should not be mixed with revenue, pipeline, order
announcements, guidance, or thesis forecasts.

No new relationship type is required. Existing types cover this batch:

- `manufactures_product`
- `uses_component`
- `supports_architecture`
- `capacity_expansion_for`
- `regulatory_exposure`

No `supplier_relationship`, `qualified_supplier`, or `design_win` record was
added because the current evidence does not support those stronger relations.

### Finance Analyst

Keep with watch constraints.

Reported metrics are separated from interpretation:

- AXT FY2025 revenue and substrate revenue are reported metrics.
- AXT Q1 2026 total revenue, gross margin, InP revenue, and InP backlog lower
  bound are separate records.
- AXT May 29, 2026 market cap, price-to-sales, and TTM revenue are market-data
  snapshot metrics.
- Backlog is explicitly lower-bound and not recognized revenue or cash
  conversion.

The thesis correctly frames valuation, permits, backlog conversion, margin, and
cash conversion as open issues rather than settled conclusions.

### Supply-Chain Research

Keep.

The graph supports product-layer and architecture-layer exposure, not named
customer proof. It records:

- AXT and Sumitomo Electric as InP substrate product-exposure nodes.
- InP substrate linkage to the EML/CW laser layer.
- EML/CW laser support for 800G/1.6T optical links and CPO architecture.
- Sumitomo Electric adjacency to NVIDIA's silicon-photonics ecosystem.

The batch deliberately avoids claiming a Sumitomo-to-NVIDIA supply relationship
or AXT named AI customer/design-in. Those gaps are captured by questions and
challenges.

### Adversarial Review

Keep with visible pressure.

The strongest possible overclaim would be: "AXT or Sumitomo is proven to supply
NVIDIA or named AI optical programs." The batch does not encode that. The thesis
summary, risk flags, questions, and challenges all state that named customer,
design-in, market-share, permit, backlog-conversion, and cash-conversion proof is
missing.

No additional canonical challenge is needed from this review pass because the
two existing challenges already pressure the main overclaim surfaces:

- `challenge:axt-sumitomo:substrate-layer-not-customer-proof`
- `challenge:axt:valuation-permit-conversion-unproven`

## Follow-Ups

Fix before the next seed batch: none.

Tighten during the next seed batch:

- Keep using `backlog_value` for backlog/order-book lower bounds instead of
  revenue or pipeline.
- For product-manufacture relationships with `scope.market`, make sure the
  supporting evidence includes market relevance, not just generic product
  existence.
- Keep social posts as sources for what the account said only; underlying
  company facts still need separate hard evidence.
- Prefer one narrow thesis with explicit questions/challenges over a broad
  narrative seed.

Defer until repeated need appears:

- Formal event timing metadata such as `date_type`, `timing_basis`, and
  `timing_confidence`.
- New relationship subtypes for ecosystem adjacency. Current
  `disclosed_relationship` claim plus no supplier/design-win relationship is
  adequate for now.
- Richer source-archive policy. Source link rot matters, but it does not block
  controlled local seeding.

Reject:

- Bulk migrating old `status`, `confidence`, `evidence_strength`, `proven`, or
  `veto` fields as canonical truth.
- Creating named supplier, customer, design-win, or qualified-supplier
  relationships from ecosystem membership, negative searches, or inferred
  product adjacency.
