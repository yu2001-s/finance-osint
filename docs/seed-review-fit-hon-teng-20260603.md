# FIT Hon Teng Seed Review

Review date: 2026-06-03

Base before batch: `794690a` (`Add chain review gate`)

Target thesis: `thesis:fit-hon-teng:cpo-elsfp-conversion-watch`

## Decision

Pass for continued controlled seeding.

This batch is useful because it tests a stronger relationship promotion than
most prior CPO seeds: FIT has both company-side and Broadcom-side evidence for
TH5-Bailly CPO interconnect hardware. The batch accepts the narrow supplier and
manufactures-product graph edges, but keeps the investment interpretation
contested because current product-line revenue, signed backlog, margin, BOM/AVL
allocation, and valuation conversion are still missing.

No schema or ontology change is required from this batch.

## Deterministic Review

`fo diff-review HEAD --json` before committing reported:

- 41 added records.
- 167 added graph edges.
- No errors.
- Expected warnings only: one open challenge and derived review states for new
  supported/contested records.

Record mix:

```text
challenge: 1
claim: 8
entity: 5
event: 1
evidence: 9
metric: 3
question: 1
relationship: 5
source: 7
thesis: 1
```

`fo review thesis:fit-hon-teng:cpo-elsfp-conversion-watch --chain --json`
reported:

- Derived review state: `contested`.
- Open challenges: 1 materiality dispute.
- Open questions: 1 high-priority revenue bridge question.
- Support evidence: 7 `public_primary`, 2 `public_secondary`.
- Source perspectives: 4 `company_self`, 1 `counterparty_self`, 1 `aggregator`,
  1 `independent_research`.
- Relationship chain: 2 `manufactures_product`, 2 `supports_architecture`, 1
  `supplier_relationship`.
- Relationship-promotion pressure: true, because revenue conversion remains
  unproven for the strong `supplier_relationship`.

`scripts/chain_review_changed.py HEAD` reviewed the five FIT relationship
records plus the FIT thesis and reported no blocking errors.

## Source To Evidence

Pass.

The batch keeps the sources separate:

- FIT company announcement for 102.4T ELSFP validation.
- FIT company announcement for Broadcom TH5-Bailly interconnect hardware.
- Broadcom counterparty announcement for FIT CPO LGA sockets and PLS
  cages/connectors.
- FIT Q1 2026 transcript-hosted management statements.
- FIT Q1 2026 HKEX financial update.
- StockAnalysis market-data snapshot.
- Frozen stock-research sidecar for the negative-search proof gap.

The frozen sidecar is public secondary evidence and is not used as primary
proof of the company facts.

## Claims And Metrics

Pass.

The claims stay narrow:

- Product proof and Broadcom relationship proof are source-backed.
- Q1 AI/cloud growth is recorded but not treated as CPO/ELSFP revenue.
- 2027/2028 ELSFP timing is a forecast statement and expected event, not current
  revenue.
- Q1 2026 revenue is a reported metric with a consolidated-financials-only risk
  flag.
- Market cap and TTM revenue are market-data metrics, not valuation approval.

The batch deliberately does not create a P/E metric because the repo has no
registered metric definition for it yet.

## Relationship Review

Pass with visible pressure.

The Broadcom edge is the important design test. The `supplier_relationship` is
acceptable because both FIT and Broadcom sources support that FIT hardware was
part of the TH5-Bailly CPO interconnect stack. The relationship is still scoped
to the product and carries risk flags for unquantified product revenue and
undisclosed customer program economics.

No stronger relationship was added for NTT. FIT says NTT technically validated
the ELSFP platform, but this batch does not promote that into a qualified
supplier, design win, or customer relationship.

## Challenge And Question

Pass.

The core pressure remains explicit:

- Future ELSFP/CPO revenue timing is not current underwriting.
- FIT's consolidated Q1 2026 financials do not disclose CPO/ELSFP/PLS/LGA or
  Broadcom program economics.
- The May 29, 2026 market-data snapshot suggests the AI interconnect story was
  already recognized before a narrow revenue bridge was disclosed.

## Tooling Decision

Keep `diff-review` as-is for now.

This batch confirms that `fo review --chain`, `scripts/chain_review_changed.py`,
and `fo diff-review` already expose the main PR review facts deterministically:
changed records, graph edges, derived review-state impact, source perspectives,
relationship-promotion pressure, open questions, and open challenges.

The next improvement should wait until a repeated PR pain appears. This batch
does not justify changing `diff-review` yet.
