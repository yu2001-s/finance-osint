We are preparing Finance OSINT, a local-first, git-native finance OSINT evidence graph.

Useful docs:

- `docs/release-readiness.md`
- `docs/governance.md`
- `docs/research-batch-contribution.md`
- `docs/seed-full-chain-review-20260603.md`
- `docs/seed-migration.md`

Before committing meaningful changes, run:

```bash
uv run fo lint --json
uv run python -m unittest discover -s tests
uv run fo index build --json
uv run python scripts/chain_review_changed.py HEAD
uv run fo graph build --json
uv run fo diff-review HEAD --json
```
