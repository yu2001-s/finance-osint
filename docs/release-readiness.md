# Release Readiness

Assessment date: 2026-06-03

Target release: `v0.1.0-alpha`

## Verdict

Finance OSINT is close to public alpha readiness. It is not v1-ready.

Current release posture:

```text
private/dev release: ready
GitHub staging: public and protected
public alpha: blocked on remaining launch gates and tag owner decision
public v1: not ready
```

The repo has a coherent local-first data model, deterministic validation, a PR
review workflow, agent-operable skills, real seeded examples, a clean-clone
smoke test pass, and a public GitHub staging repo.

## GitHub Staging Status

Staging repo:

```text
https://github.com/yu2001-s/finance-osint
visibility: public
default branch: main
```

Observed on 2026-06-03:

- Repo visibility was changed to public.
- Initial `main` push ran `Validate` successfully in GitHub Actions.
- Draft staging PR #5 tested a source-only contribution.
- Draft staging PR #6 tested a source/evidence/claim contribution.
- Draft staging PR #7 tested a question/challenge contribution.
- All three draft PRs passed the `Validate` workflow.
- Each PR run uploaded `validation-reports` and `github-view` artifacts.
- Branch protection is enabled on `main`: strict required `lint` check, one
  approving review, CODEOWNERS review, stale review dismissal, conversation
  resolution, admin enforcement, no force pushes, and no branch deletion.
- GitHub emitted a Node.js 20 action deprecation annotation; this is tracked in
  GitHub issue #4.

Resolved launch-gate issues:

- #1 Enable branch protection and required `Validate` check.

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
- [x] GitHub staging default branch is `main`.
- [x] GitHub Actions workflow passes on `main` and draft PRs.
- [x] GitHub draft PRs exercise source-only, source/evidence/claim,
  and question/challenge contribution shapes.
- [x] Branch protection and CODEOWNERS review enforcement are enabled.
- [x] Owner chooses public repo visibility.
- [ ] Abuse, MNPI, defamation, spam, and takedown operations are documented.
- [ ] GitHub Actions Node.js 20 deprecation annotation is resolved or accepted.
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

Observed result on 2026-06-03:

```text
clean_clone_smoke=pass
tests: 37 passing
records_checked: 376
index nodes: 376
graph edges: 1338
diff-review: ok, 0 changed paths, 0 warnings
```

## Release Scope

This alpha release promises:

- The repo is the canonical database.
- Contributors can add data through pull requests.
- Canonical records do not store truth `status` or `confidence`.
- Evidence, claims, metrics, events, relationships, questions, challenges, and
  theses are separate layers.
- Agents and humans use the same records and deterministic checks.
- Derived review state is local tool output, not committed truth.

This alpha release does not promise:

- Investment advice.
- Complete coverage of public equities.
- A hosted database, server, or API.
- Perfect ontology coverage.
- Automated truth adjudication.
- Protection from all bad contributions without maintainer review.

## Current Known Risks

- The repo is public before an alpha tag; release operations are still tracked
  through GitHub launch-gate issues.
- Release tagging is intentionally deferred by the owner.
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
