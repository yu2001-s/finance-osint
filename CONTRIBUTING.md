# Contributing

This project is designed for pull-request review.

## Setup

Use `uv` for local tooling:

```bash
uv sync
uv run fo lint
uv run fo index build --json
uv run fo graph build
```

## Add Data

1. Add or update entities under `entities/`.
2. Add source metadata under `sources/`.
3. Add exact evidence or observation reports under `evidence/`.
4. Add metrics, events, or datasets when the information has a structured shape.
5. Add claims only when they point to evidence.
6. Add validations or challenges as append-only review records when you support, dispute, or pressure an object.
7. Add relationships when a typed connection is supported by claims or evidence.
8. Add theses as the interpretive layer.
9. Run `uv run fo lint` before opening a PR.

## PR Validation

GitHub Actions runs the deterministic local checks on every pull request:

```bash
uv sync --locked
uv run fo lint --json
uv run python -m unittest discover -s tests
uv run fo index build --json
uv run fo graph build --json
```

CI validates structure, references, ontology usage, tests, and derived local
read artifacts. It does not decide investment truth.

## Evidence Classes

```text
public_primary       Public primary source: filing, transcript, court doc, official dataset.
public_secondary     Public secondary source: article, research report, trade publication.
firsthand_public     First-hand observation in a public setting.
firsthand_private    First-hand private conversation or closed-door meeting.
anonymous_internal   Anonymous or internal-source report.
rumor                Watchlist signal only; not strong factual support.
```

Low-trust classes `anonymous_internal` and `rumor` are allowed, but they cannot
be the only path to strong derived review state.

## Claims

Claims use `support_type`:

```text
direct
observed
inferred
private_attestation
rumor
```

If a claim predicate does not exist yet, use a provisional predicate with a
proposed definition under `claim-predicates/proposals/`.

## Relationship Types

Use registered types from `relationship-types/` whenever possible.

If a type does not exist yet, use a provisional type:

```yaml
type: provisional:critical_tooling_dependency
proposed_type_definition: relationship-types/proposals/critical_tooling_dependency.yml
```

Provisional types are allowed, but reviewers may register, rename, merge, or reject them.
