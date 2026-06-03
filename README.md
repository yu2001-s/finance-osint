# Finance OSINT

Finance OSINT is a local-first, git-native evidence graph for retail investors.

The repo is the canonical database. Contributors pull it, add structured data locally, validate it, and submit changes by pull request. There is no server, hosted database, private moderation layer, or hidden agent state.

## Core Layers

```text
Source -> Dataset -> Evidence -> Metric/Event/Claim -> Relationship -> Thesis
                              -> Validation/Challenge/Question
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
- `questions/`: open proof gaps or next investigation targets for humans and agents.
- `relationships/`: rich typed graph relationships derived from claims or evidence.
- `theses/`: interpretations, forecasts, or arguments built from evidence, claims, metrics, events, datasets, and relationships.
- `relationship-types/`: the graph ontology. Registered types are canonical; provisional types must declare their proposed definition.
- `schemas/`: JSON Schemas enforced locally and in CI.

Examples are separate from canonical data. Prototype debate examples live under
`examples/deferred/`; copyable full corpus examples live under
`examples/corpus/`. Normal `fo` commands do not load those records.

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

For a concrete sourced-research batch workflow, see
`docs/research-batch-contribution.md`.

- Public evidence should be source-backed and reviewable.
- New sources should declare `source_perspective` so review output can separate
  company-originated, independent, social, first-hand, anonymous, internal, and
  fixture sources without changing the underlying evidence.
- First-hand evidence must declare access, attribution, public status, and risk flags.
- Anonymous or internal-source reports can be recorded, but remain visibly low-trust unless independently supported.
- Claims use `support_type` to describe reasoning distance from evidence.
- Questions are investigation tasks, not truth status. Resolve them by linking evidence, claims, relationships, or theses.
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
uv run fo diff-review main --json
uv run fo graph build          # build .local/graph.json from current repo data
uv run fo graph neighbors RECORD --json
uv run fo graph inspect exdev  # find graph records mentioning a string
```

`fo review` is the deterministic truth-surface command. It does not decide
truth. It derives a local label and supporting details from evidence classes,
source independence and source perspective, validation dependency paths, open challenges,
contradictions, supersession, stale markers, and low-trust/private evidence.
Use `fo review RECORD --chain --json` when reviewing a thesis or PR-sensitive
record end to end; it adds a compact source-to-claim chain summary with
dependency counts, source/evidence mix, relationship types, open questions,
open challenges, and risk-flag categories such as social/media, market data,
compiled research, and relationship-promotion pressure.

`fo diff-review BASE` compares the current working tree against a Git base ref
and summarizes repo-native PR impact: record deltas, validation errors, evidence
mutations, reference impact, derived review-state movement, graph edge changes,
ontology changes, and deterministic warnings. Warnings are review pressure;
schema/reference failures are hard errors.

`fo lint` also emits advisory `possible_duplicate_*` warnings for current
records that share deterministic signatures such as entity identifiers, source
URLs, evidence locators, claim structure, or relationship structure. These do
not fail lint; contributors should either clarify the distinction or merge and
archive one record with `duplicate_of` or `superseded_by`.

## Supply-Chain Ontology

Prefer precise relationship types when the evidence supports them. The initial
supply-chain set includes:

- `supplier_relationship` / `customer_relationship`: broad buyer-seller edges.
- `qualified_supplier`: supplier approval or qualification by a buyer/OEM.
- `design_win`: designed-in product, component, technology, or service.
- `capacity_expansion_for`: capacity tied to output, market, customer, or time window.
- `uses_component`: product/architecture/component composition or dependency.
- `substitutes_for`: functional or economic substitution.
- `manufacturing_partner`: foundry, contract manufacturing, assembly, packaging, or test.

Use broad relationship types only when the source does not support a narrower
edge. Use `provisional:` for genuinely new relationship semantics.

## Source Preservation

Mutable web-like sources should not rely on `url` alone. Prefer `archive_url`.
If no archive exists, preserve the source with at least one of:

- bounded `evidence.excerpt`
- source `content_hash`
- small referenced `source_artifacts`

Local source artifacts must live under `artifacts/sources/`, must be referenced
by a source or evidence record, must be `png`, `jpg`, `jpeg`, or `pdf`, and must
stay under 2 MB per file. `fo lint` warns for mutable web sources without a
preservation path and fails hard on invalid artifact files.

## Archive Policy

Archive is path-level lifecycle state. Current records live in top-level data
directories; archived records live under `archive/` and keep their canonical ID.

Archived records must include at least one of `superseded_by`, `duplicate_of`,
or `archive_reason`. Current records must not depend on archived records by
default; point them at a current replacement instead. `fo diff-review` warns
when a PR adds or moves records under `archive/`.

## Deterministic Write Helpers

`fo new` creates valid YAML from explicit inputs only. It does not fetch sources,
summarize documents, infer claims, or decide truth.

```bash
uv run fo new claim \
  --statement "EXDEV uses FNDWY for the X1 processor." \
  --subject entity:company:exdev \
  --predicate disclosed_relationship \
  --object entity:company:fndwy \
  --support-type direct \
  --evidence evidence:synthetic:exdev-fy2025-supplier-note \
  --submitted-by github:username \
  --json
```

Supported constructors:

```text
fo new entity
fo new source
fo new evidence
fo new claim
fo new metric
fo new event
fo new dataset
fo new validation
fo new challenge
fo new question
fo new relationship
fo new thesis
```

## Agent Skills

`AGENTS.md` is a small router for humans and agents. Task-specific workflows
live under `agent-skills/`:

```text
operate-repo
add-evidence
add-claim
add-relationship
validate-or-challenge
add-question
write-thesis
```

These skills teach agents how to use deterministic `fo` commands. They are not
canonical data and do not create hidden agent state.
