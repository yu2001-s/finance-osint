# Pre-Public Issue Backlog

Created: 2026-06-03

Purpose: local backlog for work that should become or has become GitHub Issues
as the repository moves through private staging toward public launch.

## P0: Launch Blockers

Status: private GitHub staging is active at
`https://github.com/yu2001-s/finance-osint`. Branch protection and required
checks are tracked in GitHub issue #1; abuse/takedown operations in #2; public
visibility and tag decision in #3; GitHub Actions Node.js 20 deprecation in #4.
Branch protection enforcement is currently blocked by GitHub plan/visibility
for the private staging repo and remains required before public launch or tag.

### Verify GitHub Branch Protection And CODEOWNERS

Rationale: The repository is designed so all meaningful contribution and review
happens through GitHub PRs. Branch protection and CODEOWNERS are GitHub settings
and cannot be enforced from local files alone.

Acceptance criteria:

- [x] Default branch is chosen for private staging: `main`.
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

Status: first identity-model slice addressed locally. The contract now separates
company, security, and listing records; duplicate warnings cover expanded
security identifiers and listing ticker/local-symbol plus MIC; a synthetic
ADR/ADS fixture exercises issuer, underlying security, depositary ratio,
primary local listing, and secondary ADS listing.
Schema enforcement for identity-specific fields remains deferred until existing
company records are migrated.

Acceptance criteria:

- [x] Decide required fields for company, security, and listing records; hard
  schema enforcement remains deferred until migration.
- [x] Cover exchange/MIC, quote currency, primary listing, share class, ADR/ADS
  ratio, depositary, underlying security, and delisting/ticker-change history.
- [x] Expand duplicate checks beyond ticker/CIK/LEI/ISIN/FIGI where appropriate.
- [x] Add examples for at least one dual-listed or ADR case.

### Define Non-US Filing Metadata

Rationale: SEC fields exist, but non-US source records need normalized filing
metadata for global review.

Status: first global filing-metadata slice addressed locally. Source records now
support `exchange_filing` plus normalized jurisdiction, filing authority,
filing regime, issuer reference/code, local form/report type, report period,
filing date, source language, and preservation locator fields. HKEX, MOPS, and
European issuer examples are present in existing source chains. Duplicate-source
warnings now cover normalized filing identity; exchange filings participate in
preservation warnings.

Acceptance criteria:

- [x] Define fields for jurisdiction, regulator/exchange, filing regime, local form
  or report type, issuer code, report period, filing date, source language, and
  preservation path.
- [x] Add examples for HKEX, TWSE/TPEX MOPS, and a European issuer.
- [x] Update source templates or docs.

### Define Translation And OCR Provenance

Rationale: Global research will use non-English sources. Reviewers need original
text, translation path, and OCR provenance to judge fidelity.

Status: first translation/OCR provenance slice addressed locally. Source records
support explicit `source_language`; translated evidence now supports bounded
`original_excerpt`, `translated_excerpt`, `translation`, `ocr`, and
`encoding_notes` fields while preserving reviewer-facing `excerpt` output. Lint
warns on non-English excerpt evidence missing translation provenance, global
filing/report sources missing `source_language`, and OCR-derived translated
evidence without quality notes. The FOCI MOPS evidence record provides a
bounded Chinese-to-English example.

Acceptance criteria:

- [x] Define source language and translation metadata fields.
- [x] Decide how to store original excerpt and translated excerpt.
- [x] Include translator, machine-translation flag, translation date/version, OCR,
  and encoding notes where relevant.
- [x] Add one non-English evidence example.

### Define Accounting And Metric Comparability Rules

Rationale: Metric records need stronger comparability for global research.

Status: accounting comparability slice addressed locally. `fo lint` checks
metrics against registered metric definitions for allowed unit, allowed value
basis, required `period`/`as_of` context, and definition-required comparability
fields. Metrics now support a `comparability` block for reporting/trading
currency, accounting standard, consolidation scope, fiscal year-end, and FX
methodology. Derived, estimated, and restated metrics have stricter methodology
or restatement requirements, and fixture examples cover every value basis.

Acceptance criteria:

- [x] Decide required fields for reporting currency, trading currency, fiscal
  period, fiscal year-end, accounting standard, consolidation scope, value
  basis, and FX methodology.
- [x] Enforce metric units and basis against metric definitions.
- [x] Enforce metric-definition required context for current `period` and
  `as_of` patterns.
- [x] Add examples for reported, observed, derived, estimated, and restated metrics.

## P2: Supply-Chain Depth

### Decide BOM, AVL, Purchase Order, Allocation, Shipment, And Revenue Bridge Modeling

Rationale: Current records treat these mostly as proof gaps. Public supply-chain
research may need first-class patterns or stricter claim/relationship rules.

Status: supply-chain modeling slice addressed locally with documented patterns
for BOM, AVL, purchase order, allocation share, shipment, and revenue bridge.
Synthetic fixtures now cover an AVL `qualified_supplier`, a named purchase
order event, allocation share, shipment volume, a customer-scoped revenue
bridge, a `customer_relationship`, and a `design_win`. Lint now warns when a
strong named relationship cites broad revenue without customer, program, or
purchase-order dimensions.

Acceptance criteria:

- [x] Decide whether each concept needs a new record kind, relationship type, claim
  predicate, metric dimension, or documented pattern.
- [x] Add examples for a named purchase order, allocation share, and
  shipment/revenue bridge.
- [x] Add an AVL approval example using `qualified_supplier`.
- [x] Add review checks to prevent broad segment revenue from becoming named
  customer allocation.

### Exercise Strong Relationship Types

Rationale: `design_win`, `qualified_supplier`, and `customer_relationship` are
registered but not well exercised in current canonical records.

Status: synthetic strong relationship fixtures now exercise `qualified_supplier`,
`design_win`, and `customer_relationship`. Review-chain tests cover the
sufficient scoped examples, and lint tests cover an insufficient broad-revenue
promotion.

Acceptance criteria:

- [x] Add fixture or real examples for each strong type.
- [x] Add a `qualified_supplier` fixture with direct evidence.
- [x] Add tests or review examples showing the `qualified_supplier` chain.
- [x] Add tests or review examples showing what evidence is sufficient and
  insufficient.
- [x] Verify `fo review --chain` surfaces `qualified_supplier` promotion
  pressure clearly.

## P2: Review And Data Quality

### Add Staleness Policy For Market Data, News, And Valuation Snapshots

Rationale: Staleness is currently explicit-signal only. Dated market data and
news can mislead when treated as current.

Status: staleness policy slice addressed locally. Freshness-sensitive
market-data/news evidence and market-data valuation metrics now carry
`freshness` windows, and automatic freshness windows are warning-only in v1.
Open `outdated` challenges and `marks_stale` validations move targets toward
stale review state; addressed/withdrawn/superseded `outdated` challenges remain
visible as history without keeping targets stale. Synthetic stale and refreshed
market-data fixtures exercise the path.

Acceptance criteria:

- [x] Define record classes that require freshness review.
- [x] Decide that open explicit stale signals move derived review state, while
  closed outdated challenges do not.
- [x] Decide whether automatic freshness windows are warning-only or derived
  review-state movement.
- [x] Add examples for stale valuation snapshots and refreshed market data.

### Increase Validation Coverage

Rationale: Current seed data has many challenges and few validations. Mature
community review needs visible support, dispute, stale, and withdrawal history.

Status: validation coverage slice addressed locally. Canonical synthetic
fixtures now exercise `supports`, `partially_supports`, `disputes`, `falsifies`,
`marks_stale`, and `withdraws`; review-policy docs define validation verdict
norms and independent support paths. Review output de-duplicates repeated
validations by resolved evidence/source path, and lint rejects empty validations
or canonical validation `status`.

Acceptance criteria:

- [x] Define validation norms for independent support paths.
- [x] Add examples of `supports`, `partially_supports`, `disputes`, `falsifies`,
  `marks_stale`, and `withdraws`.
- [x] Ensure repeated validation paths are de-duplicated in review output.

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

Status: CI timing and scale-smoke slice addressed locally. The validation
workflow now runs the existing checklist through a timing wrapper, uploads
generated JSON reports from `.local/ci`, and runs a deterministic generated 10k
scale smoke. SQLite index coverage now includes major lookup paths and the scale
smoke fails on query-plan regressions. 100k remains documented as a manual
pre-tag benchmark, not a normal PR gate.

Acceptance criteria:

- [x] Track timing for lint, tests, diff-review, index build, graph build, and
  changed chain review.
- [x] Add a generated 10k-record scale smoke test.
- [x] Define a path to 100k-record benchmarking.
- [x] Add SQLite query-plan checks for major lookup paths.

### Improve GitHub-Only Viewing

Rationale: Local CLI review is strong, but casual GitHub readers cannot easily
follow record chains.

Status: first GitHub-only viewing slice addressed locally. CI now builds a
derived `.local/ci/github-view/` Markdown artifact with `pr-review.md`, an
artifact index, and changed thesis/relationship chain pages. The workflow
appends the PR summary to `$GITHUB_STEP_SUMMARY` and uploads the markdown as a
`github-view` artifact. Committed company pages remain deferred until the
artifact proves useful and a freshness contract exists.

Acceptance criteria:

- [x] Decide whether to generate committed markdown index pages, company pages, or
  PR review summaries.
- [x] Make thesis-to-source chains easier to follow in GitHub.
- [x] Keep generated artifacts deterministic and clearly separated from canonical
  records.

### Improve First-Time Contributor UX

Rationale: The first contribution path is still tool-heavy.

Status: first contributor UX slice addressed locally. `fo new` helpers now
support `--dry-run` to validate and preview records without writing files. ID
recovery hints for `context`, `review`, and `graph neighbors` are addressed
locally. Every public v1 kind now has a YAML template. The quickstart now uses
locked setup, explicit `BASE` handling, real fixture IDs, dry-run source,
evidence, and claim examples, chain review, diff review, and GitHub-view
artifact review. A fresh-clone plus current-doc-patch smoke passed the fixture
setup, search, context, review, dry-run constructor, chain-review, graph,
diff-review, and view-build commands; real PR review still uses the
contributor's changed record ID.

Acceptance criteria:

- [x] Test `docs/first-pr-quickstart.md` from a clean clone.
- [x] Add `fo new --dry-run` or equivalent preview mode.
- [x] Improve not-found ID hints with search suggestions.
- [x] Ensure every public record type has a template or helper.
