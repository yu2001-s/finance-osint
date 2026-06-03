# GitHub Public Launch Checklist

Finance OSINT is designed so the GitHub repository is the database, review
surface, contribution queue, and public audit trail. This checklist captures the
GitHub-side controls for the public repository and the remaining pre-tag gates
before `v0.1.0-alpha`.

## Current Public Status

Repository:

```text
https://github.com/yu2001-s/finance-osint
visibility: public
default branch: main
```

Observed on 2026-06-04:

- Repository visibility is public.
- Branch protection is enabled for `main`.
- Required status check: fresh `Validate`.
- Repository-owner PRs use an explicit fast-pass for the PR check; `main` push
  still runs full validation after merge.
- Force pushes and branch deletion are disabled for `main`.
- Conversation resolution is required before merge.
- Admin enforcement is enabled.
- Required approving review count is currently `0`.
- CODEOWNERS review is currently advisory, not required by branch protection.
- Post-merge `main` `Validate` passed on commit `9fa223d` in 2m8s.
- GitHub Actions emitted a Node.js 20 action deprecation annotation on the
  current workflow pins. Track in GitHub issue #4 before the alpha tag.

## Required Repository Settings

- [x] Default branch is chosen and documented.
- [x] Branch protection is enabled for the default branch.
- [x] Force pushes and branch deletion are blocked on the default branch.
- [x] The `Validate` workflow is required before merge.
- [x] Required checks use fresh results from the PR head commit.
- [x] Repository-owner PR fast-pass is explicit in the workflow and documented.
- [x] Conversations must be resolved before merge.
- [x] Maintainer admin bypass is disabled through admin enforcement.
- [ ] Owner decides whether public-alpha PRs should require at least one
  approving review before merge.
- [ ] Owner decides whether CODEOWNERS review should be required for owned
  paths.
- [ ] Node.js 20 action deprecation annotation is resolved on a fresh CI run.

## Required Review Ownership

Use `.github/CODEOWNERS` as the baseline for GitHub review routing. It is
currently advisory. If the owner enables required CODEOWNERS review, high-risk
paths should require maintainer review.

High-risk paths should require maintainer review:

```text
.github/
docs/governance.md
docs/review-policy.md
docs/contracts.md
schemas/
ontology/
fosint/
scripts/
records/sources/
records/evidence/
records/relationships/
records/theses/
```

## Required Issue And Discussion Routing

GitHub Issues should be used for actionable repo work:

- Challenges or disputes that may become `challenge` or `validation` records.
- Ontology proposals that may become relationship types, claim predicates, or
  metric definitions.
- Source preservation, copyright, artifact, or takedown concerns.
- Abuse, market-integrity, MNPI, defamation, spam, doxxing, credential, or
  malware concerns.

GitHub Discussions, when enabled, should be used for exploratory research and
coordination. Durable evidence, claims, challenges, validations, questions, and
relationships should move into repo records through PRs.

GitHub Wiki is currently disabled. Public documentation lives under `docs/` and
starts at `docs/README.md`.

## Required PR Gates

Every non-owner support-affecting PR should include:

- Source and evidence IDs.
- Evidence class, source attribution, source perspective, and content mode.
- Claim support type.
- Changed relationship and thesis IDs.
- Open questions and challenges added or addressed.
- `fo review ID --chain --json` summary for changed thesis or relationship
  records.
- `fo diff-review BASE --json` warning acknowledgement.

Owner PRs may merge on the fast-pass, but owner changes should still use local
validation before merge and rely on the full post-merge `main` workflow as the
final public signal.

Warnings are not automatic failures, but public maintainers should treat these
warning classes as review blockers until explicitly acknowledged:

- Evidence mutation or deletion.
- Low-trust, private, anonymous, or rumor evidence additions.
- Mutable sources without preservation.
- Ontology changes.
- Derived review-state movement.
- Strong relationship promotion pressure.
- New or moved archive records.

## Abuse And Market-Integrity Triage

Maintainers should send a PR or issue back when it:

- Launders rumor or social-media activity into company-fact proof.
- Promotes a stock thesis without visible evidence limitations.
- Adds unsupported supplier, customer, design-win, qualified-supplier, BOM,
  AVL, revenue, margin, or valuation-conversion claims.
- Contains possible MNPI, private-source identity leakage, doxxing, secrets,
  credentials, malware, or unsafe private material.
- Makes unsupported defamatory claims about a company or person.
- Uploads large copyrighted artifacts instead of metadata, hashes, archive URLs,
  or bounded excerpts.

Resolution should be visible through PR review, issue closure, commit history,
or repo-native records such as `challenge`, `validation`, `superseded_by`,
`duplicate_of`, or `archive_reason`.

## Pre-Tag Verification

Run these from a clean worktree before a public tag:

```bash
uv run fo lint --json
uv run python -m unittest discover -s tests
uv run fo index build --json
uv run python scripts/chain_review_changed.py HEAD
uv run fo graph build --json
uv run fo diff-review HEAD --json
uv run python scripts/validate_with_timing.py HEAD --json
uv run python scripts/scale_smoke.py --records 10000 --json
git status --short
```

Also record:

```bash
uv run python scripts/scale_smoke.py --records 100000 --json --output .local/scale-smoke-100k.json
git count-objects -vH
du -sh .git .local artifacts 2>/dev/null || true
```

Do not tag until the timing report, 10k generated smoke, query-plan checks, and
artifact-size policy have been reviewed. The 100k generated smoke is a manual
pre-tag benchmark, not a normal PR requirement.
