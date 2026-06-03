# Seeded Graph Full Chain Review

Review date: 2026-06-03

Scope: stock-research seed records through commit `2a12379` (`Seed FIT Hon Teng
CPO ELSFP conversion watch`).

Excluded from this review: synthetic fixture data such as
`thesis:synthetic-exdev-margin-risk-from-foundry-concentration`.

## Decision

Pass for continued controlled seeding.

The seeded graph preserves the core Finance OSINT rule: canonical evidence and
reported metrics stay intact, while investment interpretation lives in claims,
relationships, questions, challenges, and theses. None of the reviewed stock
research theses is encoded as settled truth. Every thesis with a material
revenue, customer, supplier, valuation, or timing leap is currently `contested`
by deterministic review.

This is not a signal to bulk-port all old research without review. The right
next workflow is still batch-by-batch migration with a mini source-to-claim
review, followed by another full chain review when the graph shape changes.

## Deterministic Review Summary

Target thesis review states:

```text
thesis:aaoi:order-backed-ramp-watch
  review: contested
  evidence: 3 public_primary
  source perspectives: 3 company_self
  open challenges: 1 materiality_dispute

thesis:axt-sumitomo:inp-substrate-bottleneck-watch
  review: contested
  evidence: 9 public_primary, 3 public_secondary
  source perspectives: 8 company_self, 1 independent_research, 1 aggregator
  open challenges: 1 missing_evidence, 1 materiality_dispute

thesis:chroma-ate:cpo-insertion-test-watch
  review: contested
  evidence: 1 public_primary, 3 public_secondary
  source perspectives: 2 company_self, 1 independent_research, 1 aggregator
  open challenges: 1 materiality_dispute

thesis:fit-hon-teng:cpo-elsfp-conversion-watch
  review: contested
  evidence: 7 public_primary, 2 public_secondary
  source perspectives: 4 company_self, 1 counterparty_self, 1 independent_research,
    1 aggregator
  open challenges: 1 materiality_dispute

thesis:foci-himax:relfacon-hidden-allocation-watch
  review: contested
  evidence: 7 public_primary, 2 public_secondary
  source perspectives: 6 company_self, 1 counterparty_self, 1 independent_research, 1 aggregator
  open challenges: 2 materiality_dispute

thesis:sivers:cpo-dfb-laser-frontier-watch
  review: contested
  evidence: 9 public_primary, 1 public_secondary
  source perspectives: 8 company_self, 1 counterparty_self, 1 aggregator
  open challenges: 1 materiality_dispute

thesis:xfab-navitas:800-vdc-foundry-watch
  review: contested
  evidence: 6 public_primary, 3 public_secondary
  source perspectives: 5 company_self, 1 government_or_regulator, 1 independent_media,
    1 independent_research, 1 aggregator
  open challenges: 2 materiality_dispute
```

Mini-review checkpoints were completed for:

- `docs/seed-review-axt-sumitomo-20260603.md`
- `docs/seed-review-chroma-ate-20260603.md`
- `docs/seed-review-fit-hon-teng-20260603.md`
- `docs/seed-review-foci-himax-20260603.md`
- `docs/seed-review-xfab-navitas-20260603.md`

## Source To Evidence

Pass.

The source layer is explicit and mostly public-primary. Evidence records point
to source records and carry local summaries, excerpts, locators, observed dates,
evidence class, attribution, verification status, and source-access metadata.

What held:

- Public filings, official product pages, company press releases, exchange/MOPS
  records, government records, market-data pages, transcript-hosted management
  statements, media reports, and frozen stock-research sidecars are represented
  as separate source records.
- Social/market-rerating material is treated as evidence that a report or market
  signal existed, not proof that the underlying business chain is true.
- Frozen stock-research sidecars are treated as secondary compiled research and
  negative-search evidence, not as primary company facts.

Pressure points to keep visible:

- The graph still depends heavily on company-originated evidence. This is
  acceptable for public-company factual disclosure, but not enough for stronger
  customer allocation, supplier, revenue, or valuation-conversion conclusions.
- Link rot and source archival remain unresolved product questions. They do not
  block local seeding, but public launch should require a clearer archive policy
  for primary filings, screenshots, PDFs, or source snapshots.

## Evidence To Claims

Pass.

Claims stayed narrow. The migration did not copy old research verdicts as
canonical truth fields.

Examples of correct claim shape:

- AXT and Sumitomo: InP substrate product exposure, export-control risk,
  backlog lower bound, and NVIDIA ecosystem adjacency are separate claims.
- Chroma: CPO insertion purchase-order language is a management-statement claim,
  not a named customer claim.
- FIT Hon Teng: 102.4T ELSFP validation, Broadcom TH5-Bailly interconnect
  evidence, AI/cloud growth, 2027/2028 revenue timing, customer-economics
  nondisclosure, and valuation snapshot are separate claims.
- FOCI/Himax: ReLFACon product fit, Himax collaboration, planned delivery
  windows, and Wiwynn demo naming are separate claims.
- X-FAB/Navitas: Navitas naming X-FAB as U.S. manufacturer is a claim backed by
  customer-side filing evidence; Reuters-reported social rerating is only a
  market-signal claim.

Repeated rule that held: negative searches and proof gaps are not used to prove
absence absolutely. They become scoped claims, questions, and challenges.

## Evidence To Metrics And Events

Pass.

Reported numeric facts are metrics, not thesis language. Timing expectations are
events, not completed outcomes.

Correct metric treatment:

- Revenue, market cap, price-to-sales, backlog, wafer shipments, and TTM revenue
  are separated by metric definition, period, currency/unit, and source.
- Backlog and pipeline are not mixed with recognized revenue.
- Valuation snapshots are recorded as market-data observations, not endorsement
  of valuation.

Correct event treatment:

- AXT/Tongmei capacity financing and export-control events are context events.
- Chroma's June 2026 Insertion 4E pilot is an expected timing window.
- FOCI/Himax H2 2026 limited shipments and 2026 planned deliveries are expected
  event windows, not completed shipments or revenue records.
- FIT Hon Teng's expected initial 102.4T ELSFP revenue contribution in 2027 is
  an expected event, not current revenue, backlog, or margin proof.
- X-FAB CHIPS-funded SiC/GaN expansion is capacity context, not customer revenue.

## Claims To Relationships

Pass with one important learning.

The graph supports rich relationships, but relationship promotion stayed
conservative.

Accepted relationship promotions:

- `manufactures_product` for product lines directly supported by company source
  material.
- `supports_architecture` for component/product/architecture fit where evidence
  supports technical relevance.
- `capacity_expansion_for` where financing, funding, or expansion evidence ties
  to a product or service surface.
- `development_partnership` where public collaboration evidence names the
  counterparties.
- `manufacturing_partner` where Navitas's Form 10-K names X-FAB as the U.S.
  manufacturer for Navitas SiC products.
- `supplier_relationship` where both company-side and counterparty-side evidence
  support the narrow supplied product or component relationship.

Rejected or avoided relationship promotions:

- No named NVIDIA, hyperscaler, TSMC, COUPE, NTT customer, or customer-design-in
  relationship was created from ecosystem adjacency, validation language, demo
  naming, customer-adjacent language, unnamed customer language, purchase-order
  language, social posts, or negative searches.
- No supplier/customer/qualified-supplier/design-win edge was created unless the
  evidence supported that exact relationship.

Learning: the graph can represent a real manufacturing relationship without
accepting the downstream investment thesis. X-FAB/Navitas is the clean example:
the Navitas-to-X-FAB manufacturing edge is canonical, while NVIDIA production,
order value, X-FAB revenue, margin, and customer split remain challenged.

FIT Hon Teng adds the stronger supplier-edge example. The Broadcom-side release
supports a scoped `supplier_relationship` for TH5-Bailly CPO interconnect
hardware, while product-line revenue, signed backlog, order value, margin, and
valuation conversion remain challenged.

## Relationships To Questions And Challenges

Pass.

Questions and challenges are doing the work we wanted from the debate layer.
They keep contested areas alive without deleting or rewriting source-backed
records.

Current open pressure surfaces:

- AAOI: order-backed ramp does not prove full revenue, margin, cash conversion,
  or volume-production timing.
- AXT/Sumitomo: substrate-layer and ecosystem adjacency do not prove named
  customer, design-in, supplier, permit conversion, or valuation conversion.
- Chroma: purchase-order language does not prove named customer, exact order
  value, CPO revenue, margin, or valuation conversion.
- FOCI/Himax: product/demo/collaboration/planned-delivery evidence does not
  prove supplier allocation, production orders, revenue split, margin, or
  current financial inflection.
- FIT Hon Teng: ELSFP validation and Broadcom CPO interconnect evidence do not
  prove current product-line revenue, signed backlog, order value, margin,
  BOM/AVL allocation, or valuation conversion.
- Sivers: CPO/DFB laser partnerships and pipeline do not prove volume revenue.
- X-FAB/Navitas: named manufacturing relationship does not prove NVIDIA
  qualification, purchase orders, customer-specific revenue, margin, or social
  rerating conversion.

This is the right shape for community debate: contributors can add validations,
counter-evidence, contradictions, or newer evidence without overwriting the
canonical record that started the debate.

## Thesis Layer

Pass.

The thesis layer is acting as interpretation, not data. Thesis records depend on
evidence, claims, metrics, events, relationships, and questions. They carry
watch language, missing evidence, risk flags, proof points, and kill criteria.

No thesis should be read as investment advice or a truth status. The canonical
truth surface is the evidence and reported metrics. The thesis surface is the
crowdsourced interpretation and forecast layer.

## Structural Findings

1. The ontology is strong enough for more controlled seeding.

   The current relationship set handled CPO optical components, InP substrates,
   ELSFP external-laser platforms, PLS cage/socket interconnect hardware,
   FAU/fiber-to-PIC coupling, test equipment, SiC/GaN foundry services, WBG
   power devices, and 800 VDC architecture without forcing premature new
   relationship types.

2. `source_attestation` for compiled negative-search sidecars is the only soft
   design smell.

   It is not blocking. The current records use proof-gap evidence plus questions
   and challenges correctly. If this pattern repeats, consider keeping negative
   search entirely as evidence plus question/challenge instead of promoting it
   into claim predicates.

3. Social/source attribution works.

   A social-media-originated market move can enter the database as media-reported
   market evidence or as a source claim about what someone said. It should not
   support underlying company truth unless backed by hard evidence.

4. Strong supplier edges can exist without blessing the thesis.

   FIT/Broadcom shows that a narrow `supplier_relationship` can be accepted from
   company-side plus counterparty-side support while the equity thesis remains
   contested. Relationship records need scoped risk flags and related questions
   when revenue or customer-program economics are not disclosed.

5. Richer interface-layer ontology can wait.

   FOCI ReLFACon/FAU, FIT PLS cage/socket hardware, and X-FAB WBG/800 VDC
   suggest possible future relationship types such as `implements_interface_layer`,
   but current `supports_architecture` is adequate until repeated cases demand
   sharper semantics.

6. Full-chain review should remain part of seeding.

   The batch mini-reviews caught the main overclaim risks early. The full review
   confirmed the repeated rules and gave a clearer migration standard for future
   contributors and agents.

## Required Carry-Forward Rules

- Do not bulk migrate old `status`, `confidence`, `evidence_strength`, `proven`,
  `veto`, or similar verdict fields into canonical records.
- Do not create supplier, customer, qualified-supplier, design-win, BOM, AVL, or
  revenue relationships from inference alone.
- Keep public-company statements, customer-side statements, independent research,
  media reports, social attribution, market data, and official filings as
  distinct source perspectives.
- Keep revenue, backlog, pipeline, order announcements, valuation, and forecasts
  as separate objects.
- Every thesis with a valuation or revenue conversion leap should have explicit
  questions and, when the gap is material, at least one open challenge.
- Continue staged seeding: add a batch, run mini source-to-claim review, run
  deterministic checks, commit, then do full-chain review after several batches.
