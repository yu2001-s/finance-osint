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

agent-skills/add-claim/SKILL.md
  Use when creating a narrow sourced claim from existing evidence.

agent-skills/add-relationship/SKILL.md
  Use when creating typed graph relationships from claims or evidence.

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
uv run fo index build --json
uv run fo graph build --json
```
