# Supplier Risk Example Corpus

This is a fictional, separate example corpus. It demonstrates one complete
finance OSINT graph without adding records to the canonical database.

The sample covers:

- public primary evidence
- public secondary evidence
- first-hand public conference evidence
- a reported metric
- an expected event
- direct and inferred claims
- a supplier relationship
- a thesis
- a validation
- a challenge

Use it in a scratch clone:

```bash
tmp="$(mktemp -d)"
rsync -a --exclude .git ./ "$tmp/finance-osint-example/"
rsync -a examples/corpus/supplier-risk/records/ "$tmp/finance-osint-example/"
cd "$tmp/finance-osint-example"
uv run fo lint --json
uv run fo index build --json
uv run fo review thesis:example:alpd-margin-risk-from-nfab-concentration --json
uv run fo graph build --json
```

The records are intentionally fictional. They are a contribution pattern, not
canonical market data.

