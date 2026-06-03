# Contributing

This project is designed for pull-request review.

## Setup

Use `uv` for local tooling:

```bash
uv sync
uv run fo lint
uv run fo diff-review main --json
uv run fo index build --json
uv run python scripts/chain_review_changed.py main
uv run fo graph build
```

## Add Data

For a full research-batch workflow, see
`docs/research-batch-contribution.md`.
For merge rules and ontology governance, see `docs/governance.md`.

1. Add or update entities under `records/entities/`.
2. Add source metadata under `records/sources/`.
3. Add exact evidence or observation reports under `records/evidence/`.
4. Add metrics, events, or datasets when the information has a structured shape.
5. Add claims only when they point to evidence.
6. Add validations or challenges as append-only review records when you support, dispute, or pressure an object.
7. Add relationships when a typed connection is supported by claims or evidence.
8. Add theses as the interpretive layer.
9. Run `uv run fo lint`, `uv run fo diff-review BASE --json`, and
   `uv run python scripts/chain_review_changed.py BASE` before opening a PR.

New database records must use your GitHub account for attribution:

```yaml
submitted_by: github:your-github-login
```

CI rejects new records whose `submitted_by` does not match the pull request
author. Existing records may keep their previous `submitted_by`; changing an
existing record to another person's identity is blocked. Maintainer-approved
automation can use `github:codex` or `github:scaffold` only through the explicit
`allow-automation-attribution` PR label.

You may use deterministic constructors instead of hand-writing YAML:

```bash
uv run fo new evidence --help
uv run fo new claim --help
uv run fo new relationship --help
uv run fo new thesis --help
```

These helpers create structure from explicit inputs. They do not infer,
summarize, ingest sources, or decide truth.

## Agent Workflows

Agents should use `AGENTS.md` as a router and load the smallest relevant
workflow under `agent-skills/`. Skills are instructions for operating the repo;
they are not canonical data and do not replace `fo lint --json`.

## PR Validation

GitHub Actions runs the deterministic local checks on every pull request:

```bash
uv sync --locked
uv run python scripts/check_pr_attribution.py "origin/${{ github.base_ref }}" --pr-author "${{ github.event.pull_request.user.login }}"
uv run python scripts/validate_with_timing.py "origin/${{ github.base_ref }}" --json
uv run python scripts/scale_smoke.py --records 10000 --json
uv run fo view build "origin/${{ github.base_ref }}" --output .local/ci/github-view --json
```

CI validates structure, references, ontology usage, tests, and derived local
read artifacts. It does not decide investment truth.

The timing wrapper runs lint, tests, index build, changed chain review, graph
build, and diff-review once and writes a generated JSON report under `.local/`.
The 10k scale smoke uses a temporary generated repository and does not commit
generated YAML. Timing budgets are advisory during public alpha; see
`docs/performance-budgets.md`.

`fo view build BASE` writes generated Markdown under `.local/github-view/` for
GitHub-only review. CI uploads `.local/ci/github-view/` as the `github-view`
artifact and appends `pr-review.md` to the workflow summary. These files are
derived review aids, not canonical data.

`fo diff-review` is useful before CI because it summarizes what a PR changes as
OSINT records: evidence edits, review-state movement, graph impact, reference
impact, ontology changes, and deterministic warnings.

`scripts/chain_review_changed.py BASE` runs `fo review --chain --json` for each
changed current thesis or relationship record. It is the PR-safe source-to-claim
review gate: source/evidence mix, dependency counts, relationship types, open
questions, open challenges, and relationship-promotion pressure.

## Evidence Classes

```text
public_primary       Public primary source: filing, transcript, court doc, official dataset.
public_secondary     Public secondary source: article, research report, trade publication.
firsthand_public     First-hand observation in a public setting.
firsthand_private    First-hand private conversation or closed-door meeting.
anonymous_internal   Anonymous or internal-source report.
rumor                Watchlist signal only; not strong factual support.
```

Low-trust classes `anonymous_internal` and `rumor` are allowed, but they cannot
be the only path to strong derived review state.

## Source Preservation

For mutable web-like sources, prefer `archive_url`. If no archive URL exists,
provide at least one preservation path: bounded evidence excerpt, source
`content_hash`, or small referenced `source_artifacts`.

Artifacts are last-resort preservation. Keep them under `artifacts/sources/`,
reference them from source/evidence YAML, use only `png`, `jpg`, `jpeg`, or
`pdf`, and keep each file under 2 MB.

## Archive

Move records into `archive/records/` only by PR. Move ontology records into
`archive/ontology/` only when retiring vocabulary. Keep the record ID unchanged
and add `superseded_by`, `duplicate_of`, or `archive_reason`. Update current
dependents to point at a current replacement instead of depending on archived
records.

## Claims

Claims use `support_type`:

```text
direct
observed
inferred
private_attestation
rumor
```

If a claim predicate does not exist yet, use a provisional predicate with a
proposed definition under `ontology/claim-predicates/proposals/`.

## Relationship Types

Use registered types from `ontology/relationship-types/` whenever possible.

If a type does not exist yet, use a provisional type:

```yaml
type: provisional:critical_tooling_dependency
proposed_type_definition: ontology/relationship-types/proposals/critical_tooling_dependency.yml
```

Provisional types are allowed, but reviewers may register, rename, merge, or reject them.
