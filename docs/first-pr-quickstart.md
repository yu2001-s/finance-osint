# First PR Quickstart

This guide walks through a small source-backed contribution. Use it for a first
source, evidence, metric, claim, question, challenge, or validation PR.

## 1. Set Up

```bash
uv sync
uv run fo lint --json
uv run fo index build --json
```

Search before adding records:

```bash
uv run fo search "company or topic" --json
uv run fo search "source title or ticker" --json
```

If the target entity already exists, reuse it. If not, add an entity first.

## 2. Choose A Small Contribution

Good first PRs are narrow:

- add one missing company, product, security, listing, market, or regulation
- add one public source and one bounded evidence record
- add one reported metric from an existing evidence record
- add one claim with `support_type: direct`
- add one question for a missing proof point
- add one challenge against an overstated relationship or thesis

Avoid starting with a broad thesis. A thesis is easier to review after its
source, evidence, claim, metric, event, and relationship dependencies exist.

## 3. Use Deterministic Constructors

The `fo new` commands write YAML from explicit inputs only. They do not fetch
sources, summarize documents, infer claims, or decide truth.

Preview an entity:

```bash
uv run fo new entity \
  --id entity:company:example-corp \
  --entity-type company \
  --name "Example Corp" \
  --submitted-by github:your-login \
  --dry-run \
  --json
```

Preview a source:

```bash
uv run fo new source \
  --id source:public:example:fy2025-annual-report \
  --source-type company_report \
  --title "Example Corp FY2025 Annual Report" \
  --public-status public \
  --source-perspective company_self \
  --accessed-at 2026-06-04 \
  --content-mode external_link \
  --url "https://example.com/report.pdf" \
  --submitted-by github:your-login \
  --dry-run \
  --json
```

After the source record exists, preview evidence:

```bash
uv run fo new evidence \
  --evidence-class public_primary \
  --source source:public:example:fy2025-annual-report \
  --summary "The report discloses Example Corp's FY2025 revenue." \
  --content-mode excerpt \
  --observed-at 2026-06-04 \
  --source-attribution named_public \
  --excerpt "Keep the excerpt short and bounded." \
  --submitted-by github:your-login \
  --dry-run \
  --json
```

Remove `--dry-run` when the preview is correct, or pass `--path` when you want a
specific file path.

## 4. Keep The Chain Honest

Use these boundaries:

- `source`: where the information came from
- `evidence`: a bounded excerpt, table, row, locator, or observation
- `metric`: a numeric observation
- `event`: something that occurred or is expected to occur
- `claim`: a narrow assertion backed by evidence
- `relationship`: a typed graph connection supported by claims or evidence
- `question`: an open proof gap
- `challenge`: unresolved pressure on support, scope, ontology, or freshness
- `validation`: append-only review of support
- `thesis`: interpretation or forecast built from dependencies

If you cannot prove customer allocation, revenue conversion, qualified-supplier
status, design-in, or materiality, say that with a question or challenge.

## 5. Validate Locally

Use your branch point or PR base for `BASE`:

```bash
uv run fo lint --json
uv run python -m unittest discover -s tests
uv run fo index build --json
uv run fo graph build --json
uv run fo diff-review BASE --json
uv run fo view build BASE --json
```

For changed or impacted thesis and relationship records:

```bash
uv run fo review RECORD_ID --chain --json
uv run python scripts/chain_review_changed.py BASE
```

## 6. Open The PR

Summarize:

- records added or changed by kind
- main source and evidence IDs
- evidence classes and source perspectives
- ontology terms used or proposed
- open questions, challenges, and limitations
- local command results and every `fo diff-review` warning

The PR submitter owns the result, including agent-assisted output.
