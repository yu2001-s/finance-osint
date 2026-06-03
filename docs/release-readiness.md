# Release Readiness

Assessment date: 2026-06-04

Target release: `v0.1.0-alpha`

## Verdict

Finance OSINT is public as a repository and close to `v0.1.0-alpha` tag
readiness. It is not v1-ready.

Current release posture:

```text
private/dev release: ready
public GitHub repository: active
v0.1.0-alpha tag: blocked on pre-tag owner/operations decisions
public v1: not ready
```

The repo has a coherent local-first data model, deterministic validation, a PR
review workflow, agent-operable skills, real seeded examples, a clean-clone
smoke test pass, and a public GitHub review surface.

## Public GitHub Status

Repository:

```text
https://github.com/yu2001-s/finance-osint
visibility: public
default branch: main
```

Observed on 2026-06-04:

- Repository visibility is public.
- Default branch is `main`.
- Branch protection is enabled for `main`.
- `Validate` is a required fresh status check.
- Repository-owner PRs use an explicit fast-pass for the required PR check; the
  full workflow still runs on every push to `main`.
- Force pushes and branch deletion are disabled on `main`.
- Conversation resolution is required before merge.
- Admin enforcement is enabled.
- Required approving review count is currently `0`; CODEOWNERS review routing
  is advisory until the owner chooses stricter public-alpha review settings.
- `Validate` passed on post-merge `main` commit `9fa223d` in 2m8s, including
  timed validation, 10k generated scale smoke, and GitHub review view build.

Open launch-gate issues:

- #2 Define abuse, MNPI, defamation, spam, and takedown operations.
- #3 Decide `v0.1.0-alpha` tag.
- #4 Address GitHub Actions Node.js 20 deprecation annotation.

## Alpha Release Gate

Required before tagging `v0.1.0-alpha`:

- [x] Core schemas exist for canonical records.
- [x] Claim predicate, metric definition, and relationship type registries exist.
- [x] CLI validates records and builds local read artifacts.
- [x] `fo review --chain` exposes source-to-claim review state.
- [x] `fo diff-review` summarizes PR-native record impact.
- [x] CI runs lint, diff review, tests, index build, changed chain review, and graph build.
- [x] Agent skills exist as small task-specific workflows.
- [x] Seed data covers multiple messy public-equity research shapes.
- [x] Full-chain seeded graph review exists.
- [x] Contributor research-batch workflow exists.
- [x] Clean clone smoke test passed.
- [x] Owner chose and committed Apache-2.0 license.
- [x] Public repository default branch is `main`.
- [x] Public repository GitHub Actions workflow passes on `main` and PRs.
- [x] Staging PRs exercised source-only, source/evidence/claim,
  and question/challenge contribution shapes.
- [x] Branch protection is enabled with required fresh `Validate`, no force
  pushes/deletions, conversation resolution, and admin enforcement.
- [x] Owner PR fast-pass is explicit and documented; full `Validate` still runs
  on `main` pushes.
- [x] Owner chose public repo visibility.
- [ ] Owner decides whether to require approving reviews and/or CODEOWNERS
  review for public alpha.
- [ ] Abuse/MNPI/defamation/spam/source-takedown operations are live-tested.
- [ ] GitHub Actions Node.js 20 deprecation annotation is resolved on CI.
- [ ] Owner decides whether to tag `v0.1.0-alpha`.

## Clean Clone Smoke

Smoke command pattern:

```bash
git clone --local --no-hardlinks "." /tmp/finance-osint-smoke/repo
cd /tmp/finance-osint-smoke/repo
uv sync --locked
uv run fo --help
uv run fo lint --json
uv run python -m unittest discover -s tests
uv run fo index build --json
uv run python scripts/chain_review_changed.py HEAD
uv run fo graph build --json
uv run fo diff-review HEAD --json
```

Observed result after public fixture cleanup on 2026-06-04:

```text
clean_clone_smoke=pass
tests: 109 passing
records_checked: 371
index records: 371
graph nodes: 371
graph edges: 1320
diff-review: ok
```

## Release Scope

This alpha tag would promise:

- The repo is the canonical database.
- Contributors can add data through pull requests.
- Canonical records do not store truth `status` or `confidence`.
- Evidence, claims, metrics, events, relationships, questions, challenges, and
  theses are separate layers.
- Agents and humans use the same records and deterministic checks.
- Derived review state is local tool output, not committed truth.

This alpha tag would not promise:

- Investment advice.
- Complete coverage of public equities.
- A hosted database, server, or API.
- Perfect ontology coverage.
- Automated truth adjudication.
- Protection from all bad contributions without maintainer review.

## Current Known Risks

- Release tagging is intentionally deferred by the owner.
- Public alpha review settings currently require `Validate` and conversation
  resolution, but not an approving review.
- Governance is intentionally lightweight; maintainer decisions still matter.
- Source archival policy is usable but not fully mature.
- Seed data is representative, not comprehensive.
- `source_attestation` for compiled negative-search sidecars is acceptable for
  alpha but should be watched for overuse.
- Review labels are deterministic summaries, not truth.
- Strong relationship promotion still needs human review. FIT/Broadcom is the
  current positive example: a narrow supplier edge can be accepted while the
  thesis remains contested.

## Recommended Tag Checklist

Before tagging:

```bash
uv run fo lint --json
uv run python -m unittest discover -s tests
uv run fo index build --json
uv run python scripts/chain_review_changed.py HEAD
uv run fo graph build --json
uv run fo diff-review HEAD --json
```

Then:

```bash
git status --short
git tag -a v0.1.0-alpha -m "Finance OSINT v0.1.0-alpha"
```

Do not tag while the worktree is dirty.
