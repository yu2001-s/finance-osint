# Contributing

This project is designed for pull-request review.

## Setup

Use `uv` for local tooling:

```bash
uv sync
uv run fo lint
uv run fo graph build
```

## Add Data

1. Add or update entities under `entities/`.
2. Add source metadata under `sources/`.
3. Add exact evidence or observation reports under `evidence/`.
4. Add claims only when they point to evidence.
5. Add validations or challenges as append-only review records when you support, dispute, or falsify an object.
6. Add relationships when a typed connection is supported by claims or evidence.
7. Add theses and debates as separate interpretive layers.
8. Run `uv run fo lint` before opening a PR.

## Evidence Classes

```text
E0_public_primary       Public primary source: filing, transcript, court doc, official dataset.
E1_public_secondary     Public secondary source: article, research report, trade publication.
E2_firsthand_public     First-hand observation in a public setting.
E3_firsthand_private    First-hand private conversation or closed-door meeting.
E4_anonymous_internal   Anonymous or internal-source report.
E5_unverified_rumor     Watchlist signal only; not canonical fact.
```

Low-trust classes `E4_anonymous_internal` and `E5_unverified_rumor` are allowed, but they cannot be the only support for a corroborated or falsified claim, relationship, or validation.

## Relationship Types

Use registered types from `relationship-types/` whenever possible.

If a type does not exist yet, use a provisional type:

```yaml
type: provisional:critical_tooling_dependency
proposed_type_definition: relationship-types/proposals/critical_tooling_dependency.yml
```

Provisional types are allowed, but reviewers may register, rename, merge, or reject them.
