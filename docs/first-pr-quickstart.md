# First PR Quickstart

This guide is for a first small Finance OSINT contribution. Keep the first PR
small: one source/evidence pair plus one claim, question, challenge, or
validation is enough.

## 1. Set Up

```bash
uv sync
uv run fo lint --json
uv run fo index build --json
```

If setup fails, run the fallback from `README.md`.

## 2. Search Before Adding

Search for the company, source, or evidence terms first:

```bash
uv run fo search "company or source terms" --json
```

Inspect nearby records:

```bash
uv run fo context RECORD_ID --json
uv run fo review RECORD_ID --json
```

Do not add a duplicate record when an existing one can be updated, validated, or
challenged.

## 3. Add A Source

Use explicit source material only. Do not rely on hidden memory or hidden agent
state.

```bash
uv run fo new source \
  --source-type web_page \
  --title "Example source title" \
  --url "https://example.com/source" \
  --archive-url "https://web.archive.org/example" \
  --public-status public \
  --source-perspective independent_media \
  --accessed-at "2026-06-03T00:00:00Z" \
  --content-mode external_link \
  --submitted-by github:YOUR_USERNAME \
  --json
```

For mutable web-like sources, prefer `archive_url`. If no archive exists, add a
bounded evidence excerpt, `content_hash`, or a small referenced artifact.

## 4. Add Evidence

Evidence is the strict layer. Quote or summarize only the bounded item needed
for review.

```bash
uv run fo new evidence \
  --evidence-class public_primary \
  --source source:... \
  --summary "Narrow summary of the exact evidence." \
  --content-mode excerpt \
  --excerpt "Short exact excerpt." \
  --observed-at "2026-06-03T00:00:00Z" \
  --source-attribution named_public \
  --submitted-by github:YOUR_USERNAME \
  --json
```

## 5. Add One Reviewable Object

For a narrow sourced assertion:

```bash
uv run fo new claim \
  --statement "Narrow checkable statement." \
  --subject entity:company:example \
  --predicate management_statement \
  --object "Short object or value" \
  --support-type direct \
  --evidence evidence:... \
  --submitted-by github:YOUR_USERNAME \
  --json
```

If the evidence does not prove the stronger business conclusion, add a question
or challenge instead of stretching the claim.

## 6. Review Locally

Run:

```bash
uv run fo lint --json
uv run fo index build --json
uv run fo review RECORD_ID --chain --json
uv run fo graph build --json
uv run fo diff-review HEAD --json
```

If you changed tests or tooling, also run:

```bash
uv run python -m unittest discover -s tests
```

Review every warning. Warnings are review pressure. Explain them in the PR.

## 7. Open The PR

In the PR, summarize:

- Records added or changed.
- Main source and evidence IDs.
- Evidence class, source perspective, attribution, content mode, and support
  type.
- What the evidence proves.
- What remains unproven.
- Open questions or challenges.
- `fo diff-review` warnings, even when they are expected.

Do not add canonical `status`, `confidence`, `agent_run`, `generated_by`, or
hidden source knowledge.

