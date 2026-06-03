# X-FAB / Navitas Seed Review

Review date: 2026-06-03

Batch target: `thesis:xfab-navitas:800-vdc-foundry-watch`

## Decision

Pass for continued seeding. The batch is a useful stress case because it contains
a real customer-side manufacturing disclosure, a real architecture/product-fit
surface, a real broad revenue numerator, and a social/retail rerating source,
while still keeping NVIDIA production and revenue conversion unproven.

The batch creates a `manufacturing_partner` relationship from Navitas to X-FAB.
It does not create a customer, supplier, qualified-supplier, or design-win
relationship between X-FAB and NVIDIA.

## Deterministic Review

`fo diff-review HEAD --json` before checkpointing the batch reported:

- 47 changed paths.
- 47 added records.
- 185 added graph edges.
- No errors.
- Expected warnings only: open challenges and derived review-state changes.

Added record mix:

```text
challenge: 2
claim: 7
entity: 6
event: 1
evidence: 9
metric: 6
question: 2
relationship: 4
source: 9
thesis: 1
```

`fo review thesis:xfab-navitas:800-vdc-foundry-watch --json` reported:

- Derived review state: `contested`.
- Open challenges: 2.
- Support evidence: 9 records.
- Evidence classes: 6 `public_primary`, 3 `public_secondary`.
- Source perspectives: 5 `company_self`, 1 `government_or_regulator`, 1
  `independent_media`, 1 `independent_research`, 1 `aggregator`.

## Source-To-Claim Chain

The chain is intact:

```text
source:public:xfab:sic-gan-technology
source:public:nist:xfab-texas-chips-funding
  -> evidence:public:xfab:sic-gan-foundry-services
  -> evidence:public:nist:xfab-texas-chips-funding
  -> claim:xfab:sic-gan-foundry-capability
  -> event:xfab:chips-funded-sic-gan-expansion
  -> relationship:xfab:capacity-expansion-for-sic-gan-foundry-services

source:public:navitas:fy2025-form-10-k
  -> evidence:public:navitas:fy2025-10k-xfab-sic-manufacturer
  -> claim:navitas:fy2025-10k-xfab-sic-manufacturer
  -> relationship:navitas:xfab-sic-manufacturing-partner

source:public:navitas:800-vdc-data-center-development
source:public:nvidia:800-vdc-architecture
  -> evidence:public:navitas:800-vdc-data-center-development
  -> evidence:public:nvidia:800-vdc-architecture
  -> claim:navitas:800-vdc-device-layer-support
  -> relationship:navitas-sic-products:supports-800-vdc
  -> relationship:wide-bandgap-power-semiconductors:supports-800-vdc

source:public:xfab:q1-2026-results
  -> evidence:public:xfab:q1-2026-wbg-revenue
  -> X-FAB revenue / backlog / SiC shipment metrics
  -> claim:xfab:q1-2026-wbg-revenue-watch

source:public:stockanalysis:xfab-valuation-20260529
  -> evidence:public:market-data:xfab-valuation-20260529
  -> market-cap / P/S metrics
  -> claim:xfab:valuation-snapshot-20260529

source:public:market-news:xfab-social-rally-20260527
  -> evidence:public:market-news:xfab-social-rerating-20260527
  -> claim:xfab:social-rerating-20260527
  -> challenge:xfab:social-rerating-not-revenue-proof

source:public:stock-research:xfab-navitas-800vdc-sidecar
  -> evidence:public:stock-research:xfab-navitas-800vdc-proof-gaps
  -> claim:xfab:navitas-800vdc-chain-revenue-unproven
  -> challenge:xfab:navitas-foundry-not-nvidia-revenue
```

## What Held

- Navitas's Form 10-K became a customer-side manufacturing-partner relationship,
  not a generic inferred supplier edge.
- Navitas 800 VDC support became device-layer/architecture relevance, not proof
  that NVIDIA qualified or purchased X-FAB-manufactured SiC.
- X-FAB Q1 2026 WBG revenue and SiC wafer shipments became metrics, while the
  missing customer split stayed visible.
- Reuters-reported social/retail rerating stayed as a market-signal claim and
  challenge, not as evidence of underlying business truth.
- CHIPS/NIST funding evidence was modeled as capacity context, not customer
  revenue.

## Ontology Note

No new ontology records were required. `manufacturing_partner`,
`supports_architecture`, and `capacity_expansion_for` covered this batch without
provisional relationship types.

## Follow-Ups

Fix before full chain review: none.

Carry forward:

- A named manufacturing relationship can be canonical without promoting the
  entire downstream thesis.
- Social/market-rerating sources should support attribution and market context,
  not underlying company-fact truth unless independently backed.
- Broad segment metrics need questions/challenges when the investment thesis
  depends on a narrower customer or product bridge.

Watch during full chain review:

- Whether supplier/customer terminology should distinguish customer-side
  manufacturing filings from inferred supply-chain exposure more explicitly.
- Whether repeated WBG/800 VDC layers need a richer architecture/component
  registry after more batches.
