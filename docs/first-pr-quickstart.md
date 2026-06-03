# First PR Quickstart

This guide is for a first small Finance OSINT contribution. Keep the first PR
small. One useful record is enough when it fits the existing graph: a source,
evidence item, claim, question, challenge, validation, entity, metric, or event
can each be a valid contribution. A source/evidence pair plus one claim,
question, challenge, or validation is a good first chain, but it is not
required.

## 1. Set Up

```bash
uv sync --locked
uv run fo lint --json
uv run fo index build --json
```

Set the review base before running diff-oriented commands. In a local clone with
no GitHub remote yet, use `HEAD`. On a GitHub PR branch, use the PR base branch.

```bash
BASE=HEAD

# On a branch with a GitHub remote:
# git fetch origin main
# BASE=origin/main
```

If setup fails, run the fallback from `README.md` to verify the local Python
environment before editing records.

## 2. Search Before Adding

Search for the company, source, or evidence terms first. This fixture query is
copy-runnable in a clean clone:

```bash
uv run fo search "exdev" --json
```

Inspect nearby records:

```bash
uv run fo context entity:company:exdev --json
uv run fo review thesis:synthetic:exdev-margin-risk-from-foundry-concentration --chain --json
```

Do not add a duplicate record when an existing one can be updated, validated, or
challenged.

## 3. Choose The Smallest Useful Unit

Add the smallest record or record set that makes the database better:

- Add a `source` when you found a useful filing, transcript, article, dataset,
  or page that future evidence can cite.
- Add `evidence` when an existing source contains a bounded excerpt,
  observation, or locator worth preserving.
- Add a `claim` only when it points to evidence and says no more than the
  evidence supports.
- Add a `question` for a proof gap, next investigation target, or missing
  underwriting bridge.
- Add a `challenge` or `validation` to review an existing record without
  overwriting it.

Full chains are optional. If your PR adds only one point, state what it adds and
what remains missing.

## 4. Add A Source

Use explicit source material only. Do not rely on hidden memory or hidden agent
state. The examples use `github:quickstart` so they can be pasted as smoke
tests; replace it with your GitHub username before writing a real contribution.

```bash
uv run fo new source \
  --source-type web_page \
  --title "Quickstart dry-run source" \
  --url "https://example.com/source" \
  --archive-url "https://web.archive.org/web/20260603000000/https://example.com/source" \
  --public-status public \
  --source-perspective independent_media \
  --accessed-at "2026-06-03T00:00:00Z" \
  --content-mode external_link \
  --submitted-by github:quickstart \
  --dry-run \
  --json
```

Remove `--dry-run` to write the record after the preview looks correct. Copy the
returned `id` into evidence that depends on this source. The fixture IDs in the
next two sections are for copy-paste smoke tests only; do not write those
examples as-is for a real PR.

For a real chained PR:

- Write the source, then copy the returned source `id`.
- Replace the fixture `--source` below with that source `id`, write the
  evidence, then copy the returned evidence `id`.
- Replace the fixture `--evidence` in the claim command with that evidence
  `id`.

For mutable web-like sources, prefer `archive_url`. If no archive exists, add a
bounded evidence excerpt, `content_hash`, or a small referenced artifact.

## 5. Add Evidence

Evidence is the strict layer. Quote or summarize only the bounded item needed
for review. This command uses an existing fixture source so the dry-run is
copy-runnable. For a real PR, replace `--source` with the source `id` you just
wrote.

```bash
uv run fo new evidence \
  --evidence-class public_primary \
  --source source:public:synthetic:exdev-fy2025-report \
  --summary "Quickstart dry-run evidence preview." \
  --content-mode excerpt \
  --excerpt "Short exact excerpt." \
  --observed-at "2026-06-03T00:00:00Z" \
  --source-attribution named_public \
  --submitted-by github:quickstart \
  --dry-run \
  --json
```

Remove `--dry-run` only after the preview is valid. Copy the returned `id` into
claims, validations, questions, or challenges that depend on this evidence.

## 6. Add One Reviewable Object

For a narrow sourced assertion, first choose an existing entity from search or
add a new entity record. This command uses an existing fixture entity and
evidence so the dry-run is copy-runnable.

```bash
uv run fo new claim \
  --statement "Quickstart dry-run claim preview." \
  --subject entity:company:exdev \
  --predicate product_signal \
  --object "quickstart product signal" \
  --support-type observed \
  --evidence evidence:synthetic:exdev-fy2025-supplier-note \
  --submitted-by github:quickstart \
  --dry-run \
  --json
```

Remove `--dry-run` only after replacing the fixture IDs with the source and
evidence IDs for your contribution.

If the evidence does not prove the stronger business conclusion, add a question
or challenge instead of stretching the claim.

## 7. Review Locally

For a meaningful database PR, run:

```bash
uv run fo lint --json
uv run python -m unittest discover -s tests
uv run fo index build --json
uv run fo review RECORD_ID --chain --json
uv run python scripts/chain_review_changed.py "$BASE"
uv run fo graph build --json
uv run fo diff-review "$BASE" --json
uv run fo view build "$BASE" --json
```

Replace `RECORD_ID` with the ID returned by `fo new`, or with the main changed
thesis or relationship ID when the PR changes a chain.

For tooling, schema, graph/index, or large data PRs, also run the heavier CI
parity checks:

```bash
uv run python scripts/validate_with_timing.py "$BASE" --json
uv run python scripts/scale_smoke.py --records 10000 --json
uv run fo view build "$BASE" --output .local/ci/github-view --json
```

Review every warning. Warnings are review pressure. Explain them in the PR. The
`.local/` outputs are generated review artifacts and should stay uncommitted.

## 8. Open The PR

In the PR, summarize:

- Records added or changed.
- Main source and evidence IDs.
- Evidence class, source perspective, attribution, content mode, and support
  type.
- What the evidence proves.
- What remains unproven.
- Open questions or challenges.
- `fo diff-review` warnings, even when they are expected.
- `fo view build` output or the CI `github-view` artifact when a thesis or
  relationship changed.

Do not add canonical `status`, `confidence`, `agent_run`, `generated_by`, or
hidden source knowledge.
