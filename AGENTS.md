We are preparing Finance OSINT, a local-first, git-native finance OSINT database.

Before committing meaningful changes on database, run:

```bash
uv run fo lint --json
uv run python -m unittest discover -s tests
uv run fo index build --json
uv run python scripts/chain_review_changed.py HEAD
uv run fo graph build --json
uv run fo diff-review HEAD --json
```
