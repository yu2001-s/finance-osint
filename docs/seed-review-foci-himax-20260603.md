# FOCI / Himax Seed Review

Review date: 2026-06-03

Batch target: `thesis:foci-himax:relfacon-hidden-allocation-watch`

## Decision

Pass for continued seeding. The batch is a useful stress case for hidden-allocation
and customer-adjacent evidence because it keeps product fit, collaboration,
planned deliveries, demo adjacency, valuation, and proof gaps separate.

The batch does not create a `supplier_relationship`, `qualified_supplier`,
`customer_relationship`, or `design_win` for FOCI. Current evidence does not
support those stronger graph relationships.

## Deterministic Review

`fo diff-review HEAD --json` before checkpointing the batch reported:

- 49 changed paths.
- 49 added records.
- 208 added graph edges.
- No errors.
- Expected warnings only: open challenges and derived review-state changes.

Added record mix:

```text
challenge: 2
claim: 8
entity: 6
event: 2
evidence: 9
metric: 5
question: 3
relationship: 4
source: 9
thesis: 1
```

`fo review thesis:foci-himax:relfacon-hidden-allocation-watch --json` reported:

- Derived review state: `contested`.
- Open challenges: 2.
- Support evidence: 9 records.
- Evidence classes: 7 `public_primary`, 2 `public_secondary`.
- Source perspectives: 6 `company_self`, 1 `counterparty_self`, 1
  `independent_research`, 1 `aggregator`.

## Source-To-Claim Chain

The chain is intact:

```text
source:public:foci:relfacon-20230118
  -> evidence:public:foci:relfacon-cpo-product-fit
  -> claim:foci:relfacon-cpo-product-fit
  -> relationship:foci:manufactures-relfacon
  -> relationship:foci-relfacon:supports-cpo

source:public:foci:q1-2026-investor-deck
  -> evidence:public:foci:q1-2026-unnamed-customer-delivery-plan
  -> claim:foci:q1-2026-unnamed-customer-delivery-plan
  -> event:foci:planned-cpo-fau-deliveries-2026

source:public:himax:foci-cpo-collaboration-20260105
  -> evidence:public:himax:foci-cpo-collaboration
  -> claim:himax:foci-cpo-collaboration
  -> relationship:foci-himax:cpo-development-partnership

source:public:himax:q1-2026-call-script
  -> evidence:public:himax:q1-2026-foci-limited-shipments
  -> claim:himax:q1-2026-foci-limited-shipments
  -> event:foci-himax:limited-cpo-shipments-h2-2026

source:public:wiwynn:computex-cpo-20260528
  -> evidence:public:wiwynn:computex-cpo-demo-foci
  -> claim:wiwynn:computex-cpo-demo-names-foci

source:public:stockanalysis:foci-valuation-20260529
  -> evidence:public:market-data:foci-valuation-20260529
  -> market-cap / P/S / TTM revenue metrics
  -> claim:foci:valuation-rerated-20260529

source:public:foci:monthly-revenue-202604
source:public:foci:q1-2026-financial-report
source:public:stock-research:foci-hidden-allocation-sidecar
  -> financial metrics and proof-gap evidence
  -> claim:foci:financial-monitor-no-cpo-inflection-20260601
  -> challenge:foci:financial-monitor-not-revenue-inflection

source:public:stock-research:foci-hidden-allocation-sidecar
  -> evidence:public:stock-research:foci-hidden-allocation-proof-gaps
  -> claim:foci:no-named-nvidia-tsmc-coupe-supplier-or-revenue-bridge
  -> challenge:foci:product-demo-validation-not-supplier-allocation
```

## What Held

- ReLFACon product proof stayed as product fit and architecture support, not
  customer allocation.
- FOCI's 2026 delivery language became an expected event window, not a completed
  shipment or revenue record.
- Himax collaboration and H2 2026 limited-shipment language became a
  development-partnership relationship and expected event, not a revenue bridge.
- Wiwynn's Computex CPO announcement stayed as a disclosed demo/ecosystem claim,
  not a supplier or customer relationship.
- Market data and reported revenue stayed as metrics; valuation pressure lives
  in the thesis and challenges.

## Ontology Note

No new ontology records were required.

The batch exposes a likely future ontology question: whether the graph needs a
registered relationship type for a product implementing an interface/component
layer, such as ReLFACon implementing a FAU / fiber-to-PIC coupling interface.
For now, `supports_architecture` is enough and avoids inventing a relationship
from one batch.

## Follow-Ups

Fix before next batch: none.

Carry forward:

- Demo, ecosystem, and customer-adjacent evidence should remain below
  supplier/customer/design-win relationships unless the source explicitly names
  allocation, order, BOM, AVL, or revenue.
- Keep expected delivery and shipment timing as `event_state: expected` with a
  window under `period`.
- Add challenges when valuation has rerated but revenue, margin, or customer
  conversion is not bridged.

Watch during full chain review:

- Whether repeated use of compiled negative-search sidecars should remain
  `source_attestation` claims or be demoted to evidence plus questions/challenges
  only.
- Whether a formal `implements_interface_layer` or similar relationship type is
  needed after more FAU/fiber-to-PIC cases.
