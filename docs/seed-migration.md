# Seed Migration Rules

Finance OSINT migrates old research as explicit source material, not as truth.
Every migrated batch must preserve the evidence layer and translate old research
labels through the current schema.

## Frozen Source Snapshot

The current seed source is recorded in
`docs/stock-research-seed-snapshot.yml`.

Use the snapshot tag or commit, not the live dirty working tree:

```bash
git -C "/Users/shaoyuhuang/Documents/codebase/stock research" rev-parse finance-osint-seed-20260603
```

## Batch Order

Migrate each ticker/theme in layers:

1. Entities
2. Sources
3. Evidence
4. Metrics, events, and datasets
5. Claims
6. Relationships
7. Questions and challenges
8. Theses

Do not write theses first. Do not create relationships until the supporting
records/claims/evidence exist.

## Old Field Translation

Old stock-research fields are not canonical Finance OSINT truth:

```text
status
confidence
evidence_strength
reliability
verdict
proven
unproven
watch
veto
```

Translate them into evidence class, support type, risk flags, validations,
challenges, questions, or thesis language. Never copy them as canonical truth
fields.

## Public-Equity Research Discipline

Use the reviewed Public Equity Investing plugin as research discipline, not as a
canonical workflow model. Finance OSINT keeps the repo as the database and does
not add hidden connector state, workbook artifacts, portfolio records, or
committed review status.

During migration:

- Do not imply access to filings, transcripts, estimates, or provider data unless
  the source material is explicit in the repo or supplied by the contributor.
- Use `source_perspective` to distinguish company-originated, counterparty,
  regulator, independent, social, first-hand, anonymous, internal, and old
  researcher-originated material.
- Treat social posts as direct support for what the account said. Underlying
  business facts need separate source-backed evidence.
- Use metric `value_basis` precisely:
  `reported`, `observed`, `derived`, `estimated`, or `restated`.
- Keep contributor assumptions and scenarios inside thesis records, not metrics.
- Record exact expected event dates only when a source gives an exact date. Put
  windows or inferred timing in `period` or `properties`.
- Preserve source conflicts as parallel records plus records/questions/challenges rather
  than silently choosing one value.
- Mark stale, preliminary, unaudited, OCR-derived, missing-source, or
  contradicted material with explicit limitations or `risk_flags`.

## Thesis Seed Quality

Seed theses should be sparse and falsifiable. Do not migrate a broad narrative
unless it can name:

```text
dependencies
core pillars
observable proof points
observable kill criteria
next missing evidence
time horizon
```

If those fields are not clear, migrate the material as claims, relationships,
questions, challenges, or a narrower thesis caveat first.

## Required Checks

Run after each batch:

```bash
uv run fo lint --json
uv run python -m unittest discover -s tests
uv run fo index build --json
uv run python scripts/chain_review_changed.py HEAD
uv run fo graph build --json
uv run fo diff-review HEAD --json
```

Treat lint and diff-review warnings as review items even when exit code is zero.
