---
name: operate-repo
description: Use when an agent needs to orient in the Finance OSINT repo, validate records, build local derived indexes, search records, inspect graph context, or prepare a PR-safe final check.
---

# Operate Repo

Use this skill for repo-safe navigation and verification. Do not create or edit
canonical records unless another task-specific skill applies.

## Workflow

1. Start at the repo root.
2. Validate current records:

```bash
uv run fo lint --json
```

3. Build local derived read artifacts when context is needed:

```bash
uv run fo index build --json
uv run fo graph build --json
```

4. Use read commands before editing:

```bash
uv run fo search QUERY --json
uv run fo context ID --json
uv run fo review ID --json
uv run fo graph neighbors ID --json
```

5. Before final response after data/tooling work, rerun:

```bash
uv run fo lint --json
uv run python -m unittest discover -s tests
uv run fo index build --json
uv run fo graph build --json
uv run fo diff-review HEAD --json
```

## Boundaries

- `.local/` is derived state and not canonical.
- GitHub PR identity owns agent-assisted output.
- Do not add model provenance to canonical records.
- Do not use live web lookup unless the user explicitly asks or the task truly needs current external data.
