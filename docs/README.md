# Documentation Home

Finance OSINT keeps its public documentation in this `docs/` directory so
documentation changes use the same pull-request review, CI, and Git history as
the database. The GitHub Wiki feature is currently disabled for the repository;
this page is the canonical wiki-style entry point.

## Start Here

- First contribution: `docs/first-pr-quickstart.md`
- Contributor guide: `CONTRIBUTING.md`
- Data model overview: `docs/data-model.md`
- CLI and schema contracts: `docs/contracts.md`
- Research batch workflow: `docs/research-batch-contribution.md`
- Example corpora: `examples/corpus/README.md`

## How Review Works

- Governance: `docs/governance.md`
- Review policy: `docs/review-policy.md`
- Review rubric: `docs/review-rubric.md`
- GitHub public launch controls: `docs/github-public-launch-checklist.md`
- Performance and scale budgets: `docs/performance-budgets.md`

Finance OSINT does not hide disagreement. Rumor, anonymous reports,
unverifiable reports, speculative theses, and aggressive claims are allowed
when they are labeled honestly and fit the record format. Review should make
the evidence chain, uncertainty, and objections visible so readers can decide
for themselves.

## Public Alpha Status

- Repository: `https://github.com/yu2001-s/finance-osint`
- Visibility: public
- Default branch: `main`
- Required GitHub check: `Validate`
- Current target tag: `v0.1.0-alpha`, not tagged yet

Launch and tag state lives in `docs/release-readiness.md`. GitHub issues with
the `launch-gate` or `pre-tag` labels are the live operational backlog.

## Canonical Data Boundaries

Canonical records live under `records/`. Examples and fixtures are not loaded by
normal `fo` commands:

- Copyable examples: `examples/corpus/`
- Deferred prototype examples: `examples/deferred/`
- Test-only synthetic records: `tests/fixtures/synthetic-records/`

Do not cite example or fixture IDs as real-world research support.

## Maintainer Operations

Before a meaningful database or tooling merge, run the same local gate used by
CI:

```bash
uv run fo lint --json
uv run python -m unittest discover -s tests
uv run fo index build --json
uv run python scripts/chain_review_changed.py HEAD
uv run fo graph build --json
uv run fo diff-review HEAD --json
```

Before tagging, use the fuller pre-tag checklist in
`docs/github-public-launch-checklist.md`.

## Historical Review Artifacts

These dated files document how the public alpha was reviewed and should not be
treated as the current operating surface when they conflict with the files
above:

- `docs/pre-public-review-20260603.md`
- `docs/pre-public-issue-backlog-20260603.md`
- `docs/seed-full-chain-review-20260603.md`
- `docs/schema-migration-v1.md`
