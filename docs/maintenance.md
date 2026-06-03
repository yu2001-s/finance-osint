# Maintenance

This page is for maintainers and contributors working on tooling, schemas,
large data changes, or generated review artifacts.

## Full Local Gate

Use the pull-request base or branch point:

```bash
BASE=origin/main
```

Run:

```bash
uv run fo lint --json
uv run python -m unittest discover -s tests
uv run fo index build --json
uv run python scripts/chain_review_changed.py "$BASE"
uv run fo graph build --json
uv run fo diff-review "$BASE" --json
uv run fo view build "$BASE" --json
```

For schema, CLI, indexing, graph, or large-data work:

```bash
uv run python scripts/validate_with_timing.py "$BASE" --json
uv run python scripts/scale_smoke.py --records 10000 --json
```

Generated reports are written under `.local/`.

## Generated GitHub View

`fo view build BASE` writes Markdown review aids under `.local/github-view/`.
CI writes the same kind of artifact under `.local/ci/github-view/`.

The generated view includes:

- diff-review summary
- changed and impacted thesis or relationship chains
- derived review state
- source/evidence mix
- open questions and challenges
- relationship-promotion pressure

Generated view files are review aids, not canonical data.

## Diff Review

`fo diff-review BASE --json` compares the working tree against a Git base and
reports:

- record additions, modifications, moves, and deletions
- schema and reference errors
- evidence integrity changes
- ontology changes
- review-state movement
- graph edge changes
- archive moves
- freshness and source-preservation warnings
- duplicate-record warnings

Warnings should be explained in the PR even when they are acceptable.

## Timing And Scale

`scripts/validate_with_timing.py` runs the deterministic gate and records step
duration. `scripts/scale_smoke.py` builds a temporary generated repository to
exercise validation, indexing, graph, and review paths at larger record counts.

Timing budgets are advisory unless CI or maintainers make them blocking for a
specific release. Treat regressions as review items.

## Schema Changes

Schema changes should include:

- updated JSON Schema
- updated templates or `fo new` constructors when relevant
- tests for required fields, references, or ontology behavior
- migration notes when existing records need mechanical changes
- documentation updates in `data-model.md`, `ontology.md`, or `contracts.md`

Schema migrations must not guess semantic intent. Use explicit contributor
review for ambiguous changes.
