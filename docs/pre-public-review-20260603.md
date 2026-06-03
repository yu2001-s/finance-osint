# Pre-Public Review

Review date: 2026-06-03

Scope: current Finance OSINT repository after the GitHub pre-review guardrails
were added.

This review evaluates whether Finance OSINT is ready to become a public,
GitHub-native place where global investors exchange sourced research ideas.

## Verdict

Finance OSINT is ready for continued private or controlled-alpha review. It is
not ready for broad public investor exchange until GitHub enforcement, global
market identity, market-integrity workflow, and scale checks are tightened.

Current posture:

```text
private/dev use: ready
controlled public alpha: close, after GitHub settings are verified
broad global investor exchange: not ready
```

The project is strongest as a conservative evidence graph for rejecting,
discounting, and refining overclaimed public-equity narratives. It is less
mature as a global, model-ready underwriting system or GitHub-scale community
platform.

## Current Repo State

Observed state from local checks:

```text
records_checked: 376
graph nodes: 376
graph edges: 1338
lint warnings: 0
tests: 37 passing
changed current thesis/relationship chain reviews: 0
diff-review HEAD warnings: 0
```

Current canonical record mix:

```text
sources: 56
evidence: 59
claims: 55
metrics: 36
events: 8
relationships: 38
theses: 8
questions: 13
challenges: 11
validations: 1
entities: 52
```

The imbalance between `challenges` and `validations` is intentional for early
seeding but should not remain the long-term community state. The graph is good
at preserving skepticism; it needs more independent support review history over
time.

## Review Axes

### 1. Evidence Chain Robustness

Decision: pass for controlled alpha.

What works:

- The core chain is explicit:

  ```text
  Source -> Dataset -> Evidence -> Metric/Event/Claim -> Relationship -> Thesis
                                -> Validation/Challenge/Question
  ```

- Canonical records do not store truth `status` or `confidence`.
- Low-trust evidence controls are implemented in lint: direct claims cannot rely
  only on anonymous/internal/rumor evidence.
- Mutable web-like source preservation is checked through archive URL, content
  hash, bounded excerpt, or artifact path.
- `fo review --chain --json` exposes evidence class mix, source perspective,
  claims, metrics, events, relationships, questions, challenges, and promotion
  pressure.

Risks:

- `source_perspective` is important but not schema-required.
- Current canonical evidence is mostly public primary/secondary, so private,
  anonymous, and rumor workflows are tested but not exercised in real seed data.
- Staleness is explicit-signal only. Market data, valuation snapshots, news, and
  time-sensitive source pages will not become stale without an explicit
  validation, challenge, or risk flag.
- Compiled negative-search sidecars can be counted as independent source support
  even when their risk flags say `compiled_research` or `negative_search`.

Review gate:

- Every new source should declare `source_perspective`.
- Every strong relationship or thesis should run `fo review ID --chain --json`.
- Every revenue, valuation, customer-allocation, supplier, qualified-supplier,
  design-win, BOM, or AVL leap should have direct evidence or an explicit
  question/challenge.
- Dated market data and news evidence should receive a staleness review path.

### 2. Ontology And Overpromotion Control

Decision: pass with watch items.

What works:

- Relationship records are n-ary typed graph objects, not loose edges.
- Relationship type definitions constrain participant roles, entity types,
  cardinality, scope, qualifiers, materiality, and evidence requirements.
- Claim predicates constrain support types, subject/object kinds, and allowed
  references.
- Existing relationship types handled CPO, optical interconnect, InP substrate,
  SiC/GaN, 800 VDC, manufacturing partner, product support, capacity expansion,
  and regulatory exposure seed cases without forcing premature new types.

Risks:

- Metric ontology is under-enforced. Metric definitions declare allowed units,
  value basis, and dimensions, but metric records still allow flexible period
  and dimension shapes.
- Relationship validation is structurally strong but cannot fully judge semantic
  overpromotion. Human reviewers still need to verify that source text supports
  the exact role/scope/materiality.
- Broad terms such as `supports_architecture`, `product_signal`, and
  `market_signal` could become catch-alls.
- Provisional ontology requires a proposed definition path, but overlap
  analysis, concrete examples, and retirement/merge criteria remain governance
  expectations rather than hard checks.

Review gate:

- Verify every metric against metric-definition units, value basis, dimensions,
  and period shape.
- Require exact source support for strong relationship types.
- Require a challenge/question when broad architecture, product, or market
  signals do not prove revenue, allocation, qualification, or customer proof.
- Require ontology proposals to include definition, concrete example, overlap
  analysis, source requirements, and migration path.

### 3. Financial And Fundamental Usefulness

Decision: useful for thesis triage; not yet full underwriting.

What works:

- Revenue, backlog, pipeline, market cap, price-to-sales, gross margin, and
  valuation snapshots are represented separately.
- Seeded records repeatedly preserve gaps around revenue conversion, backlog,
  margin, cash conversion, customer split, and valuation support.
- `fo review --chain` is useful for investors because it summarizes evidence
  mix, source perspective, metric/event coverage, open questions, challenges,
  and relationship-promotion pressure.

Risks:

- Thesis structure is uneven. Some theses have explicit pillars, proof points,
  kill criteria, and next missing evidence; others are less structured.
- The database helps reject and refine ideas better than it helps produce
  positive underwriting decisions.
- It does not yet model estimates, consensus deltas, scenario valuation, action
  thresholds, portfolio expression, or current market-price refresh.
- Validation history is thin relative to challenges.

Review gate:

- Every non-fixture thesis should include pillars, proof points, kill criteria,
  and next missing evidence.
- Every thesis with revenue or valuation conversion should depend on relevant
  metrics and have explicit open questions/challenges.
- Pipeline, order, backlog, and revenue must remain distinct.
- Valuation records should remain point-in-time market observations, not proof
  of business conversion.

### 4. Supply-Chain Usefulness

Decision: pass for conservative supply-chain OSINT.

What works:

- Entity granularity covers companies, products, components, architectures,
  services, markets, regulations, and geography.
- Relationship types cover supplier/customer, qualified supplier, design win,
  manufacturing partner, component use, substitutes, capacity expansion,
  product dependency, and architecture support.
- Seed records correctly avoid turning ecosystem adjacency, demo mentions,
  validation language, or unnamed-customer language into supplier/customer or
  design-win proof.
- Proof gaps for BOM, AVL, procurement, allocation, orders, revenue split, and
  customer split are surfaced as questions/challenges.

Risks:

- Current canonical relationships do not yet exercise `design_win`,
  `qualified_supplier`, or `customer_relationship`.
- Customer allocation remains mostly a proof-gap workflow, not a structured
  data model.
- There are no first-class objects for BOM line, AVL approval, production
  allocation, awarded share, purchase order, shipment lane, or revenue bridge.
- Seed data is sector-skewed toward CPO/optical interconnect and power
  semiconductors.

Review gate:

- For every strong edge, inspect `fo review REL_ID --chain --json`.
- Search every supply-chain batch for terms such as `BOM`, `AVL`,
  `allocation`, `purchase order`, `backlog`, `revenue split`, `customer split`,
  and `unnamed customer`.
- Reject broad segment revenue as named-customer allocation unless dimensions or
  evidence tie it to the customer/product.
- Add future fixtures for facilities, manufacturing processes, commodities,
  logistics lanes, tier-N chains, and formal order/allocation evidence.

### 5. GitHub-Native Governance And Market Integrity

Decision: public-launch blocker until settings are verified.

What works:

- The repository explicitly treats GitHub as the canonical contribution and
  review surface.
- CI runs lint, diff-review, tests, index build, changed chain review, and graph
  build.
- The PR template now requires diff-review warning acknowledgement.
- CODEOWNERS and issue templates have been added for review ownership, disputes,
  ontology proposals, source/takedown concerns, and abuse/MNPI/defamation.
- Governance rejects hidden source knowledge, hidden agent state, unsupported
  strong claims, social proof promotion, and unsafe artifacts.

Risks:

- Actual branch protection and required review settings live in GitHub settings,
  not the repository.
- CODEOWNERS does not enforce itself without branch protection.
- CI warnings are review pressure, not merge blockers.
- Public market-integrity handling needs operational discipline around possible
  MNPI, rumor laundering, defamation, coordinated promotion, spam, takedown, and
  unsafe private material.
- `submitted_by` accountability is not yet equally strict across all foundational
  kinds such as source, entity, and dataset.

Review gate:

- Verify default-branch protection before public launch.
- Require the `Validate` workflow before merge.
- Require CODEOWNERS review for schemas, ontology, tooling, sources, evidence,
  relationships, and theses.
- Require conversation resolution.
- Block force pushes and direct default-branch pushes.
- Route disputes, ontology proposals, source/takedown, and abuse concerns
  through issue templates.

### 6. Global Market Readiness

Decision: not ready for broad global investor exchange.

What works:

- The entity schema supports `security`, `listing`, `regulation`, and
  `geography`.
- Seed data includes non-US markets and currencies such as HKEX, TWSE/TPEX,
  Nasdaq Stockholm, TWD, HKD, SEK, and EUR.
- Regulatory exposure is representable through regulation entities, events, and
  relationships.

Risks:

- Multi-listing identity is under-modeled in actual records.
- There are no exercised listing/security records for ADRs, dual listings,
  share classes, MICs, depositary ratios, primary listings, or underlying
  securities.
- Non-US filing metadata is not normalized. SEC-specific fields exist, but
  jurisdiction, regulator, exchange, filing regime, local report code, and
  source language are not standard.
- Accounting and fiscal comparability is thin: fiscal year-end, accounting
  standard, consolidation scope, reporting currency, trading currency, and FX
  methodology are not first-class.
- Translation provenance is absent: no standard original excerpt, translated
  excerpt, source language, translator, machine-translation flag, OCR, or
  encoding fields.
- Ownership/control relationships exist in ontology but are not yet consistently
  exercised for subsidiaries and affiliates.
- Duplicate checks do not yet cover SEDOL, CUSIP, RIC, MIC, local issuer IDs,
  native names, or company registry IDs.

Review gate:

- Require explicit company/listing/security modeling for global public-company
  coverage.
- Add source-language and translation provenance before relying on non-English
  excerpts at scale.
- Add non-US filing metadata conventions.
- Add accounting/fiscal comparability conventions.
- Add ownership/control edges when records mention controlled entities.

### 7. Scalability And Data Operations

Decision: acceptable at current scale; needs benchmark gates.

What works:

- YAML remains canonical; SQLite index and graph JSON are derived local state.
- Record-per-file layout reduces ordinary merge conflicts.
- Duplicate detection uses deterministic signatures rather than expensive fuzzy
  pairwise comparison.
- `.local/` is ignored and source artifacts have per-file caps.

Risks:

- Unit tests and diff-review are already slower than lint at current corpus
  size.
- `diff-review` uses full before/after snapshots and may become expensive at
  large scale.
- Index and graph build are whole-repo operations.
- SQLite read layer needs more indexes for identifiers, relationship
  participants, metrics, claim predicates, source/evidence dates, and
  entity-centric lookups.
- Path conventions are documented but not strongly linted.
- Many small acceptable artifacts can still bloat Git history.

Review gate:

- Add CI timing budgets for lint, tests, diff-review, index build, graph build,
  and changed chain review.
- Add synthetic scale tests at 10k records, then 100k records.
- Track PR record deltas, edge deltas, warning count, artifact bytes, `.git`
  size, and `.local` size.
- Add query-plan checks for major SQLite lookup paths.
- Enforce path and slug conventions before broad public growth.

### 8. Contribution And Viewing UX

Decision: good for agents and maintainers; weak for casual GitHub readers.

What works:

- README explains the local-first model and core commands.
- Contribution order is documented.
- PR template asks for evidence, provenance, graph/review impact, and
  source-to-claim chain review.
- Deterministic `fo new` helpers exist for public record kinds.
- `fo search`, `fo context`, `fo review`, and `fo graph neighbors` expose useful
  local views.

Risks:

- First-time contribution is still tool-heavy.
- GitHub-only viewing is limited. YAML is readable, but dependency IDs are not
  links and there is no committed human index, company page, or static graph
  summary.
- `fo new` has no dry-run or preview-only mode.
- Mistyped IDs return limited recovery hints.
- Some reviewer-facing commands lack JSON parity.
- Templates are incomplete for some public types and ontology proposal flows.

Review gate:

- Run a clean-clone contributor test: setup, search, context, review, small PR
  understanding in about 10 minutes.
- Run a GitHub-only viewer test: follow a thesis to relationship, claim,
  evidence, and source without local tooling.
- Add `fo new --dry-run` or equivalent preview mode.
- Improve not-found hints and close-match search suggestions.
- Add or update templates for missing public record and ontology proposal
  workflows.

## Highest Priority Follow-Up Issues

Create GitHub issues from this review rather than solving all items in one PR:

1. Verify branch protection, required checks, CODEOWNERS enforcement, and
   required review settings.
2. Define public abuse, MNPI, defamation, spam, rumor-laundering, and source
   takedown operations.
3. Design global company/security/listing identity records.
4. Define non-US filing metadata and source-language conventions.
5. Define translation and OCR provenance fields.
6. Tighten metric comparability against metric definitions.
7. Decide whether BOM, AVL, purchase order, allocation, shipment lane, and
   revenue bridge need first-class records or stricter claim/relationship
   patterns.
8. Add CI timing budgets and synthetic scale benchmarks.
9. Improve GitHub-only viewing and first-time contributor workflow.
10. Add staleness policy for market data, news, and dated valuation snapshots.

Until the repository has a GitHub remote, track these as local backlog items in
`docs/pre-public-issue-backlog-20260603.md`.

## Launch Recommendation

Before public alpha:

- Verify GitHub branch protection and required review settings.
- Confirm issue templates and CODEOWNERS behavior in a real PR.
- Open issues for global identity, filing metadata, translation provenance,
  metric comparability, scale benchmarks, and GitHub-only viewing.
- Keep schema/model changes out of the guardrails PR unless the review owner
  explicitly promotes one issue to launch-blocking implementation.

Do not broaden public contribution until GitHub enforcement is confirmed. The
data model is promising, but the public-risk surface is now GitHub governance,
global identity, and market-integrity operations.
