# Pull Request

## Change Type

- [ ] Source / evidence
- [ ] Claim
- [ ] Metric / event / dataset
- [ ] Relationship / relationship type
- [ ] Validation / challenge
- [ ] Thesis
- [ ] Docs / tooling / tests

## Summary

Briefly describe what changed and why.

## Evidence And Provenance

List the main source/evidence records this PR depends on:

- Source IDs:
- Evidence IDs:
- `source_attribution`:
- `content_mode`:
- `support_type` for claims:

## Graph / Review Impact

- New or changed entity IDs:
- New or changed relationship IDs:
- Contradicts / supersedes / duplicate_of links:
- Open challenges added or addressed:

## Contributor Check

- [ ] I ran `uv run fo lint --json`.
- [ ] I ran `uv run python -m unittest discover -s tests`.
- [ ] I ran `uv run fo index build --json`.
- [ ] I ran `uv run fo graph build --json`.
- [ ] All support-affecting information is visible in the repo.
- [ ] I checked any agent-assisted output and take responsibility for this PR.
