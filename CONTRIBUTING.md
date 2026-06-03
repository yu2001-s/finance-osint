# Contributing

Finance OSINT is designed for pull-request review. The repository should show
where information came from, how strongly it supports each record, and what
remains disputed or unknown.

## Setup

```bash
uv sync
uv run fo lint --json
uv run fo index build --json
uv run fo graph build --json
```

Use a clean branch for contribution work. Generated files under `.local/` are
local read artifacts and should not be committed.

## What To Contribute

Small, well-labeled changes are preferred over large opaque batches. Good
atomic PRs include:

- one entity with identifiers
- one public source record
- one bounded evidence excerpt or observation
- one reported metric or event
- one narrow claim tied to evidence
- one typed relationship supported by claims or evidence
- one question for a proof gap
- one challenge or validation record
- one thesis that names its dependencies and limitations

A PR does not need to add a complete source-to-thesis chain. Each record must
satisfy the dependencies required by its own type.

## Authoring Order

Add data in layers:

```text
entity
source
evidence
metric / event / dataset
claim
relationship
question / challenge / validation
thesis
```

Do not start with a thesis and backfill support later. Do not promote a
relationship until the evidence or claim chain supports that exact relationship
type and scope.

## Attribution

New canonical records must use the PR author's GitHub login:

```yaml
submitted_by: github:your-login
```

CI rejects new records whose `submitted_by` value does not match the pull
request author. Existing records may keep their original submitter. Do not add
agent provenance such as `generated_by`, `agent_run`, `model`, prompts, or
hidden source notes to canonical records.

Maintainer-approved automation may use `github:codex` or `github:scaffold` only
with the explicit `allow-automation-attribution` PR label.

## Evidence Standard

Evidence is the strict layer. Claims, relationships, theses, validations, and
challenges can be contested, but their dependency chain must remain visible.

Use the supported evidence classes:

```text
public_primary
public_secondary
firsthand_public
firsthand_private
anonymous_internal
rumor
```

Low-trust evidence is allowed when labeled honestly. It should not silently
become strong factual support. First-hand, private, anonymous, social,
unverifiable, or rumor-like material should expose access, attribution, source
perspective, risk flags, limitations, and open objections.

Mutable web-like sources should have `archive_url`, `content_hash`, a bounded
evidence excerpt, or referenced source artifacts. Local artifacts must live
under `artifacts/sources/`, use `png`, `jpg`, `jpeg`, or `pdf`, and stay under
2 MB per file.

## Ontology Standard

Use registered ontology records whenever possible:

- claim predicates in `ontology/claim-predicates/`
- metric definitions in `ontology/metric-definitions/`
- relationship types in `ontology/relationship-types/`

If the existing ontology cannot represent a case, add a proposed ontology
record and use a provisional value:

```yaml
type: provisional:critical_tooling_dependency
proposed_type_definition: ontology/relationship-types/proposals/critical_tooling_dependency.yml
```

Ontology PRs should include the definition, allowed roles or fields, source
requirements, at least one concrete example, and an explanation of why existing
terms are not enough.

## Local Checks

Before opening a PR, run:

```bash
uv run fo lint --json
uv run python -m unittest discover -s tests
uv run fo index build --json
uv run fo graph build --json
uv run fo diff-review BASE --json
uv run fo view build BASE --json
```

For changed or impacted theses and strong relationships, also run:

```bash
uv run fo review RECORD_ID --chain --json
uv run python scripts/chain_review_changed.py BASE
```

Review every warning from `fo diff-review`. Warnings are review pressure, not
automatic failure, but the PR should explain why each warning is acceptable or
how it was addressed.

## CI

GitHub Actions runs the same deterministic checks used locally:

```bash
uv sync --locked
uv run python scripts/check_pr_attribution.py BASE --pr-author AUTHOR
uv run python scripts/validate_with_timing.py BASE --json
uv run python scripts/scale_smoke.py --records 10000 --json
uv run fo view build BASE --output .local/ci/github-view --json
```

CI validates schemas, references, ontology usage, tests, contributor
attribution, generated views, and scale smoke behavior. It does not decide
investment truth.

## Review Outcomes

Use the narrowest change that preserves provenance and reviewability:

- Add a question when support is missing.
- Add a challenge when support is contested.
- Add a validation when support has been reviewed.
- Narrow a claim or relationship when the source supports less than stated.
- Archive or supersede records instead of deleting history to settle disputes.

Reject or remove content that adds hidden source knowledge, possible MNPI,
private-source identity leakage, unsupported defamatory claims, spam,
coordinated promotion, secrets, credentials, malware, or large copyrighted
artifacts.

See `docs/governance.md` for review and dispute policy.
