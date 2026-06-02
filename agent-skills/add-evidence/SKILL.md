---
name: add-evidence
description: Use when adding source and evidence records from explicit material the user or repo provides, including excerpts, observations, meeting notes, or public-source locators.
---

# Add Evidence

Evidence is the strict layer. Add evidence only from explicit material available
to the contributor or already in the repo.

## Workflow

1. Search for existing source/evidence first:

```bash
uv run fo index build --json
uv run fo search "source or excerpt terms" --json
```

2. If the source does not exist, create it from explicit metadata:

```bash
uv run fo new source \
  --source-type SOURCE_TYPE \
  --title "TITLE" \
  --public-status public \
  --accessed-at "YYYY-MM-DDTHH:MM:SSZ" \
  --content-mode external_link \
  --submitted-by github:USERNAME \
  --json
```

3. Create evidence with explicit provenance:

```bash
uv run fo new evidence \
  --evidence-class public_primary \
  --source source:... \
  --summary "Narrow summary of the exact evidence." \
  --content-mode excerpt \
  --observed-at "YYYY-MM-DDTHH:MM:SSZ" \
  --source-attribution named_public \
  --submitted-by github:USERNAME \
  --json
```

4. Run validation:

```bash
uv run fo lint --json
```

## Required Judgments

Pick evidence fields conservatively:

- `evidence_class`: provenance, not truth.
- `source_attribution`: visible to public repo readers.
- `content_mode`: how much content is stored.
- `risk_flags`: required for private, anonymous, rumor, or sensitive evidence.

## Boundaries

- Do not store large PDFs, datasets, transcripts, screenshots, or raw private leaks.
- Do not use `anonymous_to_maintainers`.
- Do not upgrade evidence into claims unless the user asks or the task requires it.
