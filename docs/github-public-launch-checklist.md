# GitHub Public Launch Checklist

Finance OSINT is designed so the GitHub repository is the database, review
surface, contribution queue, and public audit trail. This checklist captures the
GitHub-side controls that must be verified before a public launch or public
alpha tag.

## Required Repository Settings

- Default branch is chosen and documented.
- Branch protection is enabled for the default branch.
- Direct pushes to the default branch are blocked except for emergency
  maintainer recovery.
- Force pushes and branch deletion are blocked on the default branch.
- The `Validate` workflow is required before merge.
- Required checks use fresh results from the PR head commit.
- At least one approving review is required before merge.
- Stale approvals are dismissed when support-affecting files change.
- Conversations must be resolved before merge.
- CODEOWNERS review is required for owned paths.
- Maintainer admin bypass is disabled or explicitly documented.

## Required Review Ownership

Use `.github/CODEOWNERS` as the baseline for GitHub review routing.

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

## Required PR Gates

Every support-affecting PR should include:

- Source and evidence IDs.
- Evidence class, source attribution, source perspective, and content mode.
- Claim support type.
- Changed relationship and thesis IDs.
- Open questions and challenges added or addressed.
- `fo review ID --chain --json` summary for changed thesis or relationship
  records.
- `fo diff-review BASE --json` warning acknowledgement.

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
git status --short
```

Also record:

```bash
git count-objects -vH
du -sh .git artifacts 2>/dev/null || true
```

