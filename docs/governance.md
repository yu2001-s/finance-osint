# Governance

Finance OSINT uses lightweight repo governance. The goal is to keep evidence
visible, reviewable, and falsifiable without creating hidden moderation state.

## Adult Review Principle

Finance OSINT treats contributors and readers as adults. The repository does
not suppress unusual, speculative, low-trust, promotional, bearish, bullish, or
disputed research views merely because they are uncertain or unpopular.

Contributors may submit rumors, anonymous reports, unverifiable reports,
speculative theses, weak signals, contradictions, and aggressive claims when
they are formatted honestly and visibly labeled with provenance, evidence
class, source perspective, source attribution, support type, risk flags, and
open objections where applicable.

The repository's job is not to decide what investors are allowed to think. Its
job is to make evidence chains, uncertainty, and disagreement inspectable.

## Maintainer Role

Maintainers review pull requests for structure, provenance, evidence quality,
ontology fit, and repository hygiene. Maintainers do not turn review labels into
canonical truth and should not reject a PR solely because they disagree with
the investment view.

For now, maintainers are the GitHub users with merge rights on the repo.

## GitHub Controls

The GitHub repository is the contribution queue and public audit trail. Current
public-alpha controls are tracked in `docs/github-public-launch-checklist.md`
and release/tag state is tracked in `docs/release-readiness.md`.

At minimum:

- Protect the default branch.
- Require the `Validate` workflow before merge.
- Require conversation resolution before merge.
- Block force pushes and default-branch deletion.
- Route disputes, ontology proposals, source/takedown concerns, and abuse or
  market-integrity concerns through GitHub issue templates.

Current branch protection requires fresh `Validate`, conversation resolution,
blocks force pushes/deletions, and enforces those rules for admins. Required
approving review and required CODEOWNERS review are not enabled yet; the owner
should decide whether to enable them before tagging `v0.1.0-alpha`.

## Merge Criteria

A PR is mergeable when:

- Required CI passes.
- `fo diff-review` warnings are reviewed and explained.
- Support-affecting information is visible in the repo.
- Atomic contributions satisfy the dependencies required by their own record
  type; full source-to-thesis chains are not mandatory.
- New claims point to evidence.
- New relationships are supported by claims, evidence, metrics, or events.
- Strong relationships such as `supplier_relationship`, `customer_relationship`,
  `qualified_supplier`, `design_win`, or `manufacturing_partner` are scoped to
  what the source actually supports.
- Open proof gaps are captured as questions or challenges.
- Agent-assisted output has been reviewed by the PR submitter.

## Review Outcomes

A PR should be handled with the narrowest intervention that preserves safety,
provenance, and format.

Allowed but visibly low-trust:

- Rumor, anonymous, internal, social, first-hand, or unverifiable reports that
  are labeled honestly.
- Speculative, contrarian, promotional, bearish, bullish, or unusual theses that
  declare dependencies and open proof gaps.
- Weak signals that are used for investigation, questions, challenges, or
  explicitly speculative theses.

Send back for relabeling or narrowing:

- Evidence class, source perspective, source attribution, support type, or risk
  flags are missing or too strong.
- A weak source path is promoted as direct support.
- A thesis or claim overstates what the evidence supports.
- New relationships are broader, narrower, or stronger than the source permits.

Reject or remove only when the PR:

- Adds hidden source knowledge, hidden agent state, `agent_run`, or
  `generated_by`.
- Adds canonical truth `status` or `confidence`.
- Contains possible MNPI, private-source identity leakage, unsupported
  defamatory claims, coordinated promotion, spam, or rumor laundering.
- Uploads secrets, credentials, doxxing material, malware, or large copyrighted
  artifacts.
- Breaks schemas, references, ontology rules, tests, or deterministic review
  checks.

## Ontology Changes

Prefer existing registered terms.

Use provisional terms only when the existing ontology cannot represent the
relationship, claim predicate, or metric definition without losing meaning.

Ontology PRs should include:

- Proposed definition.
- Allowed roles or fields.
- Source requirements.
- At least one concrete example.
- Whether an existing type can cover the case instead.

Maintainers may register, rename, merge, narrow, broaden, or reject provisional
terms.

## Disputes

Do not overwrite sourced records to win an argument.

Use:

- `challenge` for open objections.
- `validation` for review verdicts on support.
- `contradicts`, `supersedes`, `corrects`, `narrows`, or `broadens` when a
  record relationship is explicit.
- `question` for unresolved proof gaps.

The preferred outcome is a better graph, not a deleted debate.
