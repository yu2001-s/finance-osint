# Finance OSINT

Finance OSINT is a local-first, git-native evidence graph for retail investors.

The repo is the canonical database. Contributors pull it, add structured data locally, validate it, and submit changes by pull request. There is no server, hosted database, private moderation layer, or hidden agent state.

## Core Layers

```text
Source -> Dataset -> Evidence -> Metric/Event/Claim -> Relationship -> Thesis
                              -> Validation/Challenge
```

- `sources/`: provenance metadata for filings, transcripts, pages, datasets, meetings, and observations.
- `evidence/`: exact excerpts, locators, observations, or first-hand reports tied to sources.
- `claim-predicates/`: registered claim predicate vocabulary.
- `metric-definitions/`: registered metric vocabulary.
- `metrics/`: structured numeric observations with provenance.
- `events/`: structured time-bound occurrences or expected occurrences.
- `datasets/`: metadata about source datasets.
- `claims/`: narrow checkable statements backed by evidence.
- `validations/`: append-only review records that evaluate support.
- `challenges/`: append-only unresolved objections about evidence quality, scope, ontology, materiality, or missing support.
- `relationships/`: rich typed graph relationships derived from claims or evidence.
- `theses/`: interpretations, forecasts, or arguments built from evidence, claims, metrics, events, datasets, and relationships.
- `relationship-types/`: the graph ontology. Registered types are canonical; provisional types must declare their proposed definition.
- `schemas/`: JSON Schemas enforced locally and in CI.

Debate records are deferred from public v1. Prototype debate examples live under `examples/deferred/`.

## Quick Start

```bash
uv sync
uv run fo lint
uv run fo lint --json
uv run fo index build --json
uv run fo graph build
```

Generated graph files go into `.local/` and are intentionally ignored by git.

If you cannot use `uv`, the fallback is:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
fo lint
```

## Contribution Policy

Evidence is the strict layer. Claims, relationships, theses, validations, and challenges can be contested, but they must preserve their dependency chain.

- Public evidence should be source-backed and reviewable.
- First-hand evidence must declare access, attribution, public status, and risk flags.
- Anonymous or internal-source reports can be recorded, but remain visibly low-trust unless independently supported.
- Claims use `support_type` to describe reasoning distance from evidence.
- Relationship types must be registered or marked `provisional:` with a proposed type definition.
- Relationship participants, scope, materiality, and qualifiers must fit the selected relationship type.
- Canonical records do not store truth `status` or `confidence`; tools derive review state locally.

## Local Commands

```bash
uv run fo lint                 # validate schemas, references, and ontology usage
uv run fo lint --json          # machine-readable lint output for agents/CI
uv run fo index build --json   # build .local/index.sqlite from YAML
uv run fo search exdev --json  # search indexed records
uv run fo context RECORD --json
uv run fo review RECORD --json
uv run fo graph build          # build .local/graph.json from current repo data
uv run fo graph neighbors RECORD --json
uv run fo graph inspect exdev  # find graph records mentioning a string
```
