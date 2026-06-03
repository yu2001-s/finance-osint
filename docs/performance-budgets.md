# Performance Budgets

Finance OSINT is local-first, but GitHub PRs are the public review surface. The
validation workflow records timing and scale evidence so maintainers can see when
the repository is outgrowing current whole-repo operations.

## Timing Reports

Run the same checklist GitHub Actions runs:

```bash
uv run python scripts/validate_with_timing.py HEAD --json
```

The script writes `.local/validation-timings.json` by default. CI writes
`.local/ci/validation-timings.json` and uploads it as an artifact. The report
includes:

- lint, unit tests, index build, changed chain review, graph build, and
  diff-review timings.
- Advisory budget comparison from `.github/ci/timing-budgets.json`.
- Record, graph, `.local`, source-artifact, and git object summaries.

Budgets are warning-mode before public launch. A step can exceed budget without
failing CI unless maintainers intentionally rerun with `--enforce-budgets`.

## Generated Scale Smoke

Run the deterministic 10k generated smoke test:

```bash
uv run python scripts/scale_smoke.py --records 10000 --json
```

The smoke test creates a temporary repository, copies `schemas/` and `ontology/`,
generates fixed source/evidence/claim records, then exercises:

- `validate_repo`
- `build_graph_data`
- `create_index_database`
- SQLite query plans for major indexed lookup paths

Generated records and `.local` outputs are not canonical data and must not be
committed. CI uploads only the JSON report.

## 100k Path

Before broad public growth, run the same smoke at 100k records on a manual or
scheduled runner:

```bash
uv run python scripts/scale_smoke.py --records 100000 --json --output .local/scale-smoke-100k.json
```

Do not make 100k a normal PR gate until GitHub runner baselines exist. Also do
not make 10k `diff-review` a hard scale gate until base-tree loading avoids one
`git show` process per YAML file.

## Query-Plan Gate

The scale smoke asserts SQLite uses indexes for:

- refs and graph edges by source/target.
- identifier lookup by type/value.
- evidence by source.
- claims by subject and predicate.
- validation/challenge review records by target.
- relationship participants and metrics by entity.

If one of these plans regresses to a full scan, the smoke test fails even if the
functional output is correct.
