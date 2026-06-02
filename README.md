# Finance OSINT

Finance OSINT is a local-first, git-native evidence graph for retail investors.

The repo is the canonical database. Contributors pull it, add structured data locally, validate it, and submit changes by pull request. There is no server, hosted database, private moderation layer, or hidden agent state.

## Core Layers

```text
Source -> Evidence -> Claim -> Validation/Challenge -> Relationship -> Thesis -> Debate
```

- `sources/`: provenance metadata for filings, transcripts, pages, datasets, meetings, and observations.
- `evidence/`: exact excerpts, observations, or first-hand reports tied to sources.
- `claims/`: narrow checkable statements backed by evidence.
- `validations/`: append-only review records that attest, corroborate, dispute, or falsify specific objects.
- `challenges/`: append-only objections about evidence quality, scope, ontology, materiality, or missing support.
- `relationships/`: rich typed graph relationships derived from claims or evidence.
- `theses/`: interpretations, forecasts, or arguments built from evidence, claims, and relationships.
- `debates/`: structured adversarial review around claims, relationships, and theses.
- `relationship-types/`: the graph ontology. Registered types are canonical; provisional types must declare their proposed definition.
- `schemas/`: JSON Schemas enforced locally and in CI.

## Quick Start

```bash
uv sync
uv run fo lint
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

Evidence is the strict layer. Claims, relationships, theses, and debates can be contested, but they must preserve their dependency chain.

- Public evidence should be source-backed and reviewable.
- First-hand evidence must declare access, attribution, public status, and risk flags.
- Anonymous or internal-source reports can be recorded as attestations, not upgraded to hard fact without corroboration.
- Relationship types must be registered or marked `provisional:` with a proposed type definition.
- Relationship materiality and qualifiers must fit the selected relationship type.
- Corroborated or falsified claims, relationships, and validations need at least one non-low-trust evidence path.
- Debates should target specific claims, relationships, theses, arguments, or evidence.

## Local Commands

```bash
uv run fo lint                 # validate schemas, references, and relationship type usage
uv run fo graph build          # build .local/graph.json from repo data
uv run fo graph inspect AAPL   # find graph records mentioning a string
```
