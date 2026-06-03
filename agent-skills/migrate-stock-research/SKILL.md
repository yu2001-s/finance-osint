---
name: migrate-stock-research
description: Use when porting seed material from the frozen local stock research snapshot into Finance OSINT canonical records.
---

# Migrate Stock Research

Stock research is seed input, not canonical truth. Migrate only from the frozen
snapshot recorded in `docs/stock-research-seed-snapshot.yml`.

## Snapshot

```text
source repo: /Users/shaoyuhuang/Documents/codebase/stock research
branch: codex/finance-osint-seed-snapshot
tag: finance-osint-seed-20260603
commit: d2d72bfd7cb791d7bbef4566ab0fceb9358b5e2e
```

Do not migrate from a moving dirty tree. Read source files from the tag/commit
or from a worktree checked out at that commit.

## Workflow

1. Verify the snapshot:

```bash
git -C "/Users/shaoyuhuang/Documents/codebase/stock research" rev-parse finance-osint-seed-20260603
```

2. Build a batch crosswalk outside canonical records:

```text
old source id/path -> source/evidence records
old entity id      -> entity record
old claim id       -> metric/event/claim/question/challenge/thesis decision
old edge id        -> relationship/question/challenge/thesis decision
old veto id        -> challenge/question/thesis decision
```

3. Migrate in layers:

```text
entities
sources
evidence
records/metrics/records/events/datasets
claims
relationships
records/questions/challenges
theses
```

4. Before writing each object, classify the public-equity research role:

```text
source-backed fact
reported or observed metric
derived or estimated metric
expected or occurred event
attribution claim
relationship claim
open proof gap
challenge or veto pressure
thesis interpretation
```

5. Run checks after each layer:

```bash
uv run fo lint --json
uv run fo index build --json
uv run fo graph build --json
uv run fo diff-review HEAD --json
```

## Translation Rules

- Do not copy old `status`, `confidence`, `evidence_strength`, `reliability`,
  `verdict`, `proven`, `unproven`, `watch`, or `veto` as canonical truth fields.
- Convert old `evidence_strength` into support choice, risk flags, validations,
  challenges, or thesis wording only when dependencies justify it.
- Convert old `status: active` into no field. It only means the old record was live.
- Convert old `status: proven` into a normal sourced claim/relationship plus
  evidence. The derived review state decides how it surfaces locally.
- Convert old `unproven`, `watch`, `negative_search`, `valuation_veto`, and
  conversion gaps into questions, challenges, or thesis caveats.
- Social posts support attribution to the post author unless independently
  backed by hard evidence.
- Unnamed customers/suppliers stay descriptors until named evidence exists; do
  not create fake company entities for them.
- Pipeline, backlog, bookings, order value, revenue, guidance, and valuation
  are distinct structured records/metrics/events.
- Product existence and market relevance are separate. Add `scope.market` to a
  product or manufacture relationship only when explicit dependencies support
  that market context.
- Do not imply provider, transcript, filing, or estimate access unless the
  source material is explicit in the repo or supplied by the contributor.
- Use `source_perspective` whenever possible to expose whether support is
  company-originated, counterparty-originated, independent, social,
  first-hand, anonymous, internal, or old-researcher material.
- Use metric `value_basis` conservatively:
  `reported` for source-reported numbers, `observed` for field observations,
  `derived` for calculations from explicit inputs, `estimated` for explicit
  consensus/provider/model estimate sources, and `restated` for source-backed
  restatements.
- Contributor assumptions, scenarios, price targets, and future expectations
  belong in theses unless a source explicitly states them.
- Expected catalysts may be events. Use exact `expected_at` only when the source
  gives an exact date; otherwise record a window under `period` or `properties`.
- Preserve conflicting values or statements as separate records plus
  records/challenges/questions. Do not silently choose one value during migration.
- Mark stale links, preliminary or unaudited figures, OCR uncertainty,
  missing-source gaps, and contradicted-source situations with explicit
  limitations or `risk_flags`.

## Thesis Quality

Migrate a thesis only when it can name explicit dependencies and at least one
observable proof point or kill criterion. Otherwise migrate the material as
claims, relationships, questions, or challenges first.

Preferred thesis structure:

```yaml
depends_on:
  evidence: []
  claims: []
  relationships: []
  metrics: []
  events: []
pillars:
  - statement: "..."
    proof_points: []
    kill_criteria: []
next_missing_evidence: []
```

## Provenance

For migrated source records, include a concise `provenance` value with the
snapshot tag/commit and original stock-research id/path when available.

Do not add hidden agent fields such as `generated_by`, `agent_run`, `model`, or
prompt metadata. The PR submitter owns the migrated output.
