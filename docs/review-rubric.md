# Review Rubric

This rubric is for formal repository reviews before broad public use and for
periodic review after major seeding batches.

## 1. Evidence Chain Robustness

Check whether records preserve a traceable chain:

```text
Source -> Dataset -> Evidence -> Metric/Event/Claim -> Relationship -> Thesis
                              -> Validation/Challenge/Question
```

Review:

- Source preservation through archive URL, content hash, excerpt, or artifact.
- `source_perspective`, `source_attribution`, `content_mode`, and evidence
  class.
- Low-trust evidence handling for `anonymous_internal` and `rumor`.
- Whether compiled research and negative-search sidecars are visibly limited.
- Open challenges, questions, contradictions, supersession, and staleness.
- `fo review RECORD --chain --json` output for PR-sensitive records.

## 2. Ontology And Overpromotion Control

Review:

- Relationship roles, scope, materiality, qualifiers, and evidence support.
- Claim predicate constraints and support-type compatibility.
- Metric definitions, lint-enforced units, value basis, required dimensions,
  and period/as-of context.
- Whether broad types such as `supports_architecture`, `product_signal`, and
  `market_signal` are becoming catch-alls.
- Whether provisional ontology has a definition, concrete example, overlap
  analysis, and promotion/retirement path.

Reject supplier, customer, qualified-supplier, design-win, BOM, AVL, revenue,
margin, or valuation-conversion claims unless the evidence supports that exact
promotion.

## 3. Financial And Fundamental Usefulness

Review:

- Separation of revenue, backlog, pipeline, orders, market cap, valuation, and
  forecasts.
- Period, as-of, reported-at, observed-at, and fiscal context.
- Whether thesis records have linked metrics, proof points, kill criteria,
  open questions, and challenges.
- Whether valuation snapshots remain market observations, not proof of business
  conversion.
- Whether the graph helps reject, refine, or underwrite an idea.

## 4. Supply-Chain Usefulness

Review:

- Entity granularity for companies, products, components, architectures,
  services, markets, regulations, and geographies.
- Supplier, customer, manufacturing partner, design-win, qualified-supplier,
  component-use, and capacity-expansion semantics.
- Treatment of ecosystem adjacency, demos, validation language, unnamed
  customers, purchase orders, BOM, AVL, shipment, allocation, and revenue split.
- Whether broad segment revenue is incorrectly used as named-customer proof.
- Transferability to facilities, commodities, logistics lanes, tier-N suppliers,
  and manufacturing processes.

## 5. GitHub-Native Governance And Market Integrity

Review:

- Branch protection, required checks, CODEOWNERS, required reviews, and
  conversation resolution.
- PR template completeness and reviewer acknowledgement of warnings.
- Issue templates for disputes, ontology proposals, source/takedown concerns,
  and abuse/MNPI/defamation/spam reports.
- Contributor accountability through GitHub identity and `submitted_by`.
- Visible handling of moderation, takedown, archive, and dispute decisions.

## 6. Global Market Readiness

Review:

- Company, security, and listing separation.
- Exchange, MIC, quote currency, primary listing, share class, ADR/ADS ratio,
  and underlying security links.
- ISIN, LEI, FIGI, SEDOL, CUSIP, RIC, CIK, local issuer IDs, native names, and
  registry IDs.
- Non-US filing metadata: jurisdiction, regulator, filing regime, local form,
  report period, filing date, source language, archive/hash/artifact.
- Accounting standard, fiscal year-end, reporting currency, trading currency,
  consolidation scope, and FX methodology.
- Translation and OCR provenance.

## 7. Scalability And Data Operations

Review:

- Runtime for lint, tests, diff-review, index build, graph build, and changed
  chain review.
- PR record deltas, graph edge deltas, warning count, and artifact bytes.
- SQLite indexes and query plans for identifiers, metrics, participants,
  sources, evidence, claims, and dates.
- Clone size, `.git` growth, artifact policy, and generated `.local/` size.
- Path and slug conventions, sharding by market/company/theme, and merge
  conflict behavior.
- Synthetic scale tests at 10k records, then 100k records before broad public
  growth.

## 8. Contribution And Viewing UX

Review:

- Whether a new contributor can run setup, search, inspect, review, and prepare
  a small PR in about 10 minutes.
- Whether each public record type has a template or deterministic `fo new`
  helper.
- Whether reviewer-facing commands have consistent human and JSON output.
- Whether mistyped IDs produce actionable recovery hints.
- Whether GitHub-only readers can follow a thesis-to-source chain without local
  tooling.
- Whether PR summaries expose the important graph and review facts without
  forcing reviewers to parse large JSON by hand.
