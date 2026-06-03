# Internal Session Handoff

We are preparing Finance OSINT for a private `v0.1.0-alpha` checkpoint. Do not
publish the repo or create a release tag unless the user explicitly asks.

Current state:

- Repo is a local-first, git-native finance OSINT evidence graph.
- Apache-2.0 license is committed.
- Public alpha is functionally close; publication/tagging are intentionally
  deferred.
- Seed graph contains representative public-equity research batches and full
  chain review docs.
- Clean-clone smoke has passed.

Main remaining work:

1. Decide when to tag `v0.1.0-alpha`.
2. Optionally run one fake PR simulation before tagging.
3. Improve public README only if it blocks first-time contributor clarity.
4. Continue seed migration only batch-by-batch with mini review.

Do not:

- Add hidden source knowledge, hidden agent state, `agent_run`, or `generated_by`.
- Add canonical truth `status` or `confidence`.
- Bulk-port old stock-research verdict fields.
- Create unsupported supplier/customer/design-win/revenue/valuation claims.
- Publish, push, or tag without explicit user approval.

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
