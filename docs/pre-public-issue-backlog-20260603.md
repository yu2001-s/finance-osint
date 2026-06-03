# Pre-Public Issue Backlog

Created: 2026-06-03

Purpose: local backlog for work that should become GitHub Issues after the
repository has a remote and public contribution workflow. Until then, this file
is the tracked issue queue.

## P0: Launch Blockers

### Verify GitHub Branch Protection And CODEOWNERS

Rationale: The repository is designed so all meaningful contribution and review
happens through GitHub PRs. Branch protection and CODEOWNERS are GitHub settings
and cannot be enforced from local files alone.

Acceptance criteria:

- Default branch is chosen.
- `Validate` workflow is required before merge.
- CODEOWNERS review is required for owned paths.
- Direct pushes and force pushes to the default branch are blocked.
- Conversation resolution is required before merge.
- Maintainer bypass policy is documented.

### Define Abuse, MNPI, Defamation, Spam, And Takedown Operations

Rationale: A public investor research repo can attract rumor laundering,
coordinated promotion, unsupported harmful claims, private-source leakage, and
unsafe artifacts.

Acceptance criteria:

- Maintainer triage steps are documented.
- Abuse/MNPI/defamation/source-takedown issue templates are tested in a real
  GitHub repo.
- Rules clarify when to lock, close, request changes, archive, redact, or add a
  challenge.
- Repo policy distinguishes public evidence from private or unsafe material.

### Decide Public Repository Visibility And Tagging

Rationale: Publication is intentionally deferred. A public alpha should not be
tagged until owner decisions and GitHub protections are complete.

Acceptance criteria:

- Default branch chosen.
- Visibility chosen.
- `v0.1.0-alpha` tag decision made.
- `docs/release-readiness.md` updated with the decision.

## P1: Global Investor Readiness

### Design Company, Security, And Listing Identity Records

Rationale: Global investor use needs issuer, security, and listing separation.
Ticker-only identity is not enough for ADRs, dual listings, share classes, and
local exchange symbols.

Acceptance criteria:

- Decide required fields for company, security, and listing records.
- Cover exchange/MIC, quote currency, primary listing, share class, ADR/ADS
  ratio, depositary, underlying security, and delisting/ticker-change history.
- Expand duplicate checks beyond ticker/CIK/LEI/ISIN/FIGI where appropriate.
- Add examples for at least one dual-listed or ADR case.

### Define Non-US Filing Metadata

Rationale: SEC fields exist, but non-US source records need normalized filing
metadata for global review.

Acceptance criteria:

- Define fields for jurisdiction, regulator/exchange, filing regime, local form
  or report type, issuer code, report period, filing date, source language, and
  preservation path.
- Add examples for HKEX, TWSE/TPEX MOPS, and a European issuer.
- Update source templates or docs.

### Define Translation And OCR Provenance

Rationale: Global research will use non-English sources. Reviewers need original
text, translation path, and OCR provenance to judge fidelity.

Acceptance criteria:

- Define source language and translation metadata fields.
- Decide how to store original excerpt and translated excerpt.
- Include translator, machine-translation flag, translation date/version, OCR,
  and encoding notes where relevant.
- Add one non-English evidence example.

### Define Accounting And Metric Comparability Rules

Rationale: Metric records need stronger comparability for global research.

Acceptance criteria:

- Decide required fields for reporting currency, trading currency, fiscal
  period, fiscal year-end, accounting standard, consolidation scope, value
  basis, and FX methodology.
- Enforce metric units and basis against metric definitions.
- Add examples for reported, observed, derived, estimated, and restated metrics.

## P2: Supply-Chain Depth

### Decide BOM, AVL, Purchase Order, Allocation, Shipment, And Revenue Bridge Modeling

Rationale: Current records treat these mostly as proof gaps. Public supply-chain
research may need first-class patterns or stricter claim/relationship rules.

Acceptance criteria:

- Decide whether each concept needs a new record kind, relationship type, claim
  predicate, metric dimension, or documented pattern.
- Add examples for a named purchase order, AVL approval, allocation share, and
  shipment/revenue bridge.
- Add review checks to prevent broad segment revenue from becoming named
  customer allocation.

### Exercise Strong Relationship Types

Rationale: `design_win`, `qualified_supplier`, and `customer_relationship` are
registered but not well exercised in current canonical records.

Acceptance criteria:

- Add fixture or real examples for each strong type.
- Add tests or review examples showing what evidence is sufficient and
  insufficient.
- Verify `fo review --chain` surfaces promotion pressure clearly.

## P2: Review And Data Quality

### Add Staleness Policy For Market Data, News, And Valuation Snapshots

Rationale: Staleness is currently explicit-signal only. Dated market data and
news can mislead when treated as current.

Acceptance criteria:

- Define record classes that require freshness review.
- Decide whether staleness is warning-only or derived review-state movement.
- Add examples for stale valuation snapshots and refreshed market data.

### Increase Validation Coverage

Rationale: Current seed data has many challenges and few validations. Mature
community review needs visible support, dispute, stale, and withdrawal history.

Acceptance criteria:

- Define validation norms for independent support paths.
- Add examples of `supports`, `partially_supports`, `disputes`, `falsifies`,
  `marks_stale`, and `withdraws`.
- Ensure repeated validation paths are de-duplicated in review output.

### Tighten Source Perspective Requirements

Rationale: Current sources mostly include `source_perspective`, but schemas do
not require it. Review output depends on it.

Status: source perspective requirement addressed locally. `submitted_by`
hard-requirement for legacy source/entity records remains deferred until a
reviewed attribution backfill is done.

Acceptance criteria:

- [x] Missing `source_perspective` is a schema error for source records.
- [x] Add guidance for `unknown`.
- [x] Add tests for missing and unknown source perspective.

## P3: Scale And UX

### Add CI Timing Budgets And Synthetic Scale Tests

Rationale: Tests and diff-review are already slower than lint at the current
small corpus size.

Acceptance criteria:

- Track timing for lint, tests, diff-review, index build, graph build, and
  changed chain review.
- Add a generated 10k-record scale smoke test.
- Define a path to 100k-record benchmarking.
- Add SQLite query-plan checks for major lookup paths.

### Improve GitHub-Only Viewing

Rationale: Local CLI review is strong, but casual GitHub readers cannot easily
follow record chains.

Acceptance criteria:

- Decide whether to generate committed markdown index pages, company pages, or
  PR review summaries.
- Make thesis-to-source chains easier to follow in GitHub.
- Keep generated artifacts deterministic and clearly separated from canonical
  records.

### Improve First-Time Contributor UX

Rationale: The first contribution path is still tool-heavy.

Acceptance criteria:

- Test `docs/first-pr-quickstart.md` from a clean clone.
- Add `fo new --dry-run` or equivalent preview mode.
- Improve not-found ID hints with search suggestions.
- Ensure every public record type has a template or helper.
