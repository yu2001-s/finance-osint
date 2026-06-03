# Agent Router

Finance OSINT is a local-first, git-native evidence graph. The repo is the
canonical database. Agents and humans use the same records; the PR submitter is
responsible for all output.

Use the smallest relevant skill under `agent-skills/`:

```text
agent-skills/operate-repo/SKILL.md
  Use for repo orientation, validation, index/search/context/review, and final checks.

agent-skills/add-evidence/SKILL.md
  Use when adding source or evidence records from explicit user-provided material.

agent-skills/add-entity/SKILL.md
  Use when adding companies, products, components, markets, architectures, or other graph entities.

agent-skills/add-metric-event-dataset/SKILL.md
  Use when adding structured numeric facts, events, guidance, datasets, orders, or time-based observations.

agent-skills/add-claim/SKILL.md
  Use when creating a narrow sourced claim from existing evidence.

agent-skills/add-relationship/SKILL.md
  Use when creating typed graph relationships from claims or evidence.

agent-skills/propose-ontology/SKILL.md
  Use when a needed predicate, relationship type, metric definition, entity type, or proof vocabulary is missing.

agent-skills/migrate-stock-research/SKILL.md
  Use when porting seed material from the frozen stock research snapshot.

agent-skills/validate-or-challenge/SKILL.md
  Use when reviewing, supporting, disputing, or pressuring an existing object.

agent-skills/add-question/SKILL.md
  Use when recording an open proof gap or next investigation target.

agent-skills/write-thesis/SKILL.md
  Use when writing interpretation or forecast records from explicit dependencies.
```

Rules for all agents:

- Do not add hidden source knowledge, hidden agent state, `agent_run`, or `generated_by`.
- Do not commit truth `status` or `confidence` into canonical records.
- Do not infer evidence, claims, relationships, or theses without explicit dependencies.
- Prefer deterministic `fo` commands over hand-written YAML when they fit.
- Before finishing data work, run:

```bash
uv run fo lint --json
uv run python -m unittest discover -s tests
uv run fo index build --json
uv run python scripts/chain_review_changed.py HEAD
uv run fo graph build --json
uv run fo diff-review HEAD --json
```
