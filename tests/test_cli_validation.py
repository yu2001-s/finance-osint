from __future__ import annotations

import argparse
import contextlib
import io
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

from fosint import cli


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIRS = (
    "schemas",
    "relationship-types",
    "claim-predicates",
    "metric-definitions",
    "entities",
    "sources",
    "evidence",
    "claims",
    "validations",
    "challenges",
    "relationships",
    "theses",
)


def copy_fixture_repo(target: Path) -> Path:
    repo = target / "repo"
    repo.mkdir()
    for dirname in FIXTURE_DIRS:
        source = ROOT / dirname
        if source.exists():
            shutil.copytree(source, repo / dirname)
    return repo


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    assert isinstance(loaded, dict)
    return loaded


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False)


def init_git_repo(repo: Path) -> None:
    commands = (
        ["git", "init"],
        ["git", "config", "user.email", "tester@example.com"],
        ["git", "config", "user.name", "Test User"],
        ["git", "add", "."],
        ["git", "commit", "-m", "base fixture"],
    )
    for command in commands:
        subprocess.run(command, cwd=repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def run_lint(root: Path) -> tuple[int, str]:
    stderr = io.StringIO()
    stdout = io.StringIO()
    with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(stdout):
        status = cli.run_lint(root)
    return status, stdout.getvalue() + stderr.getvalue()


def run_json_command(func, *args) -> tuple[int, dict]:
    stderr = io.StringIO()
    stdout = io.StringIO()
    with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(stdout):
        status = func(*args, json_output=True)
    payload = yaml.safe_load(stdout.getvalue())
    assert isinstance(payload, dict), stderr.getvalue()
    return status, payload


def run_new_json(func, repo: Path, **kwargs) -> tuple[int, dict]:
    stderr = io.StringIO()
    stdout = io.StringIO()
    kwargs.setdefault("id", None)
    kwargs.setdefault("path", None)
    kwargs.setdefault("created_at", None)
    kwargs.setdefault("risk_flag", [])
    kwargs.setdefault("overwrite", False)
    kwargs["json"] = True
    args = argparse.Namespace(**kwargs)
    with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(stdout):
        status = func(repo, args)
    payload = yaml.safe_load(stdout.getvalue())
    assert isinstance(payload, dict), stderr.getvalue()
    return status, payload


class CliValidationTests(unittest.TestCase):
    def test_scaffold_lints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))

            status, output = run_lint(repo)

        self.assertEqual(status, 0, output)
        self.assertIn("OK", output)

    def test_direct_claim_cannot_rely_only_on_rumor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            write_yaml(
                repo / "sources" / "firsthand" / "anonymous-rumor.yml",
                {
                    "schema_version": 1,
                    "kind": "source",
                    "id": "source:firsthand:anonymous-rumor",
                    "source_type": "anonymous_report",
                    "title": "Anonymous rumor fixture",
                    "public_status": "unknown",
                    "accessed_at": "2026-06-02T00:00:00Z",
                    "content_mode": "summary",
                    "risk_flags": ["anonymous_source"],
                },
            )
            write_yaml(
                repo / "evidence" / "firsthand" / "anonymous-rumor.yml",
                {
                    "schema_version": 1,
                    "kind": "evidence",
                    "id": "evidence:firsthand:anonymous-rumor",
                    "evidence_class": "rumor",
                    "source": "source:firsthand:anonymous-rumor",
                    "summary": "Anonymous rumor fixture.",
                    "content_mode": "summary",
                    "observed_at": "2026-06-02T00:00:00Z",
                    "submitted_by": "github:tester",
                    "source_attribution": "anonymous_to_public",
                    "source_access": {
                        "nda_or_confidentiality": "unknown",
                        "recording_available": False,
                        "source_identity_public": False,
                    },
                    "risk_flags": ["anonymous_source", "unverified_rumor"],
                },
            )
            write_yaml(
                repo / "claims" / "anonymous-correlated-claim.yml",
                {
                    "schema_version": 1,
                    "kind": "claim",
                    "id": "claim:test:anonymous-correlated-claim",
                    "statement": "Anonymous rumor fixture directly establishes a product issue.",
                    "subject": "entity:company:exdev",
                    "predicate": "product_signal",
                    "object": True,
                    "support_type": "direct",
                    "evidence": [{"id": "evidence:firsthand:anonymous-rumor"}],
                    "submitted_by": "github:tester",
                },
            )

            status, output = run_lint(repo)

        self.assertEqual(status, 1, output)
        self.assertIn("direct support_type cannot rely only on rumor evidence", output)

    def test_relationship_materiality_level_must_match_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            path = repo / "relationships" / "synthetic-exdev-fndwy-x1-supply.yml"
            data = load_yaml(path)
            data["materiality"]["level"] = "existential"
            write_yaml(path, data)

            status, output = run_lint(repo)

        self.assertEqual(status, 1, output)
        self.assertIn("materiality level `existential` is not allowed", output)

    def test_relationship_qualifier_must_match_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            path = repo / "relationships" / "synthetic-exdev-fndwy-x1-supply.yml"
            data = load_yaml(path)
            data["qualifiers"] = ["secret_supplier"]
            write_yaml(path, data)

            status, output = run_lint(repo)

        self.assertEqual(status, 1, output)
        self.assertIn("qualifier `secret_supplier` is not allowed", output)

    def test_challenge_references_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            write_yaml(
                repo / "challenges" / "missing-reference.yml",
                {
                    "schema_version": 1,
                    "kind": "challenge",
                    "id": "challenge:test:missing-reference",
                    "target": "thesis:synthetic:exdev-margin-risk-from-foundry-concentration",
                    "submitted_by": "github:tester",
                    "challenge_type": "missing_evidence",
                    "summary": "Fixture challenge with a missing dependency.",
                    "depends_on": {"claims": ["claim:test:does-not-exist"]},
                },
            )

            status, output = run_lint(repo)

        self.assertEqual(status, 1, output)
        self.assertIn("references missing id `claim:test:does-not-exist`", output)

    def test_json_lint_output_is_machine_readable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            stderr = io.StringIO()
            stdout = io.StringIO()
            with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(stdout):
                status = cli.run_lint(repo, json_output=True)

        self.assertEqual(status, 0, stderr.getvalue())
        payload = yaml.safe_load(stdout.getvalue())
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["command"], "lint")
        self.assertEqual(payload["errors"], [])

    def test_lint_warns_for_mutable_source_without_preservation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            write_yaml(
                repo / "sources" / "public" / "mutable-web-source.yml",
                {
                    "schema_version": 1,
                    "kind": "source",
                    "id": "source:test:mutable-web-source",
                    "source_type": "web_page",
                    "title": "Mutable web source",
                    "url": "https://example.test/mutable",
                    "public_status": "public",
                    "accessed_at": "2026-06-03T00:00:00Z",
                    "content_mode": "external_link",
                },
            )

            status, payload = run_json_command(cli.run_lint, repo)

        self.assertEqual(status, 0, payload)
        self.assertEqual(
            [warning["code"] for warning in payload["warnings"]],
            ["mutable_source_without_preservation"],
        )

    def test_lint_accepts_referenced_source_artifact_for_mutable_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            artifact = repo / "artifacts" / "sources" / "mutable-web-source" / "screenshot.png"
            artifact.parent.mkdir(parents=True)
            artifact.write_bytes(b"small artifact")
            write_yaml(
                repo / "sources" / "public" / "mutable-web-source.yml",
                {
                    "schema_version": 1,
                    "kind": "source",
                    "id": "source:test:mutable-web-source",
                    "source_type": "web_page",
                    "title": "Mutable web source",
                    "url": "https://example.test/mutable",
                    "public_status": "public",
                    "accessed_at": "2026-06-03T00:00:00Z",
                    "content_mode": "external_link",
                    "source_artifacts": [
                        "artifacts/sources/mutable-web-source/screenshot.png"
                    ],
                },
            )

            status, payload = run_json_command(cli.run_lint, repo)

        self.assertEqual(status, 0, payload)
        self.assertEqual(payload["warnings"], [])

    def test_lint_rejects_unreferenced_source_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            artifact = repo / "artifacts" / "sources" / "unreferenced" / "screenshot.png"
            artifact.parent.mkdir(parents=True)
            artifact.write_bytes(b"small artifact")

            status, output = run_lint(repo)

        self.assertEqual(status, 1, output)
        self.assertIn("source artifact is not referenced", output)

    def test_lint_rejects_bad_source_artifact_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            write_yaml(
                repo / "sources" / "public" / "bad-artifact-path.yml",
                {
                    "schema_version": 1,
                    "kind": "source",
                    "id": "source:test:bad-artifact-path",
                    "source_type": "web_page",
                    "title": "Bad artifact path",
                    "public_status": "public",
                    "accessed_at": "2026-06-03T00:00:00Z",
                    "content_mode": "external_link",
                    "source_artifacts": ["screenshots/bad.png"],
                },
            )

            status, output = run_lint(repo)

        self.assertEqual(status, 1, output)
        self.assertIn("source_artifacts", output)
        self.assertIn("artifacts/sources", output)

    def test_index_build_and_search_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))

            status, payload = run_json_command(cli.run_index_build, repo)
            self.assertEqual(status, 0, payload)
            self.assertTrue((repo / ".local" / "index.sqlite").exists())
            self.assertEqual(payload["records_indexed"], 39)

            status, payload = run_json_command(cli.run_search, repo, "exdev")

        self.assertEqual(status, 0, payload)
        self.assertTrue(payload["ok"])
        self.assertGreater(payload["result_count"], 0)
        self.assertIn(
            "entity:company:exdev",
            {result["id"] for result in payload["results"]},
        )

    def test_context_review_and_neighbors_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            status, build_payload = run_json_command(cli.run_index_build, repo)
            self.assertEqual(status, 0, build_payload)

            status, context = run_json_command(
                cli.run_context,
                repo,
                "claim:synthetic:exdev-uses-fndwy-for-x1",
            )
            self.assertEqual(status, 0, context)
            self.assertEqual(context["record"]["kind"], "claim")
            self.assertIn(
                "evidence:synthetic:exdev-fy2025-supplier-note",
                {item["target_id"] for item in context["outgoing_refs"]},
            )

            status, review = run_json_command(
                cli.run_review,
                repo,
                "thesis:synthetic:exdev-margin-risk-from-foundry-concentration",
            )
            self.assertEqual(status, 0, review)
            self.assertEqual(review["review_state"]["primary_label"], "contested")
            self.assertIn("has_open_challenge", review["review_state"]["flags"])
            self.assertEqual(review["challenge_summary"]["open_count"], 1)
            self.assertEqual(
                review["support_summary"]["evidence_class_counts"]["public_primary"],
                1,
            )
            self.assertEqual(
                review["support_summary"]["source_independence"]["unique_source_count"],
                1,
            )

            status, neighbors = run_json_command(
                cli.run_graph_neighbors,
                repo,
                "relationship:synthetic:exdev-fndwy-x1-supply",
            )

        self.assertEqual(status, 0, neighbors)
        self.assertIn(
            "entity:company:exdev",
            {neighbor["id"] for neighbor in neighbors["neighbors"]},
        )

    def test_review_deduplicates_validation_paths_and_counts_independent_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            write_yaml(
                repo / "sources" / "public" / "independent-review-source.yml",
                {
                    "schema_version": 1,
                    "kind": "source",
                    "id": "source:public:synthetic:independent-review-source",
                    "source_type": "other",
                    "title": "Independent review source",
                    "public_status": "public",
                    "accessed_at": "2026-06-02T00:00:00Z",
                    "content_mode": "small_fixture",
                    "risk_flags": ["synthetic_fixture"],
                },
            )
            write_yaml(
                repo / "evidence" / "public" / "independent-review-evidence.yml",
                {
                    "schema_version": 1,
                    "kind": "evidence",
                    "id": "evidence:synthetic:independent-review-evidence",
                    "evidence_class": "public_secondary",
                    "source": "source:public:synthetic:independent-review-source",
                    "summary": "Independent synthetic source also supports the supplier relationship.",
                    "content_mode": "small_fixture",
                    "observed_at": "2026-06-02T00:00:00Z",
                    "submitted_by": "github:tester",
                    "source_attribution": "named_public",
                    "risk_flags": ["synthetic_fixture"],
                },
            )
            write_yaml(
                repo / "validations" / "duplicate-path.yml",
                {
                    "schema_version": 1,
                    "kind": "validation",
                    "id": "validation:test:duplicate-path",
                    "target": "claim:synthetic:exdev-uses-fndwy-for-x1",
                    "submitted_by": "github:tester",
                    "verdict": "supports",
                    "summary": "Duplicate support path for de-duplication.",
                    "depends_on": {
                        "evidence": ["evidence:synthetic:exdev-fy2025-supplier-note"],
                        "claims": ["claim:synthetic:exdev-uses-fndwy-for-x1"],
                        "relationships": [],
                        "theses": [],
                    },
                },
            )
            write_yaml(
                repo / "validations" / "independent-path.yml",
                {
                    "schema_version": 1,
                    "kind": "validation",
                    "id": "validation:test:independent-path",
                    "target": "claim:synthetic:exdev-uses-fndwy-for-x1",
                    "submitted_by": "github:tester",
                    "verdict": "supports",
                    "summary": "Independent source support path.",
                    "depends_on": {
                        "evidence": ["evidence:synthetic:independent-review-evidence"],
                        "claims": [],
                        "relationships": [],
                        "theses": [],
                    },
                },
            )

            status, build_payload = run_json_command(cli.run_index_build, repo)
            self.assertEqual(status, 0, build_payload)
            status, review = run_json_command(
                cli.run_review,
                repo,
                "claim:synthetic:exdev-uses-fndwy-for-x1",
            )

        self.assertEqual(status, 0, review)
        self.assertEqual(review["validation_summary"]["total_count"], 3)
        self.assertEqual(review["validation_summary"]["unique_dependency_path_count"], 2)
        self.assertEqual(review["validation_summary"]["repeated_dependency_path_count"], 1)
        self.assertEqual(
            review["support_summary"]["source_independence"]["unique_source_count"],
            2,
        )
        self.assertEqual(
            review["support_summary"]["evidence_class_counts"],
            {"public_primary": 1, "public_secondary": 1},
        )

    def test_review_derives_stale_from_explicit_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            write_yaml(
                repo / "validations" / "stale-claim.yml",
                {
                    "schema_version": 1,
                    "kind": "validation",
                    "id": "validation:test:stale-claim",
                    "target": "claim:synthetic:exdev-uses-fndwy-for-x1",
                    "submitted_by": "github:tester",
                    "verdict": "marks_stale",
                    "summary": "Synthetic stale marker.",
                    "depends_on": {
                        "evidence": ["evidence:synthetic:exdev-fy2025-supplier-note"],
                        "claims": ["claim:synthetic:exdev-uses-fndwy-for-x1"],
                        "relationships": [],
                        "theses": [],
                    },
                },
            )

            status, build_payload = run_json_command(cli.run_index_build, repo)
            self.assertEqual(status, 0, build_payload)
            status, review = run_json_command(
                cli.run_review,
                repo,
                "claim:synthetic:exdev-uses-fndwy-for-x1",
            )

        self.assertEqual(status, 0, review)
        self.assertEqual(review["review_state"]["primary_label"], "stale")
        self.assertIn("has_staleness_risk", review["review_state"]["flags"])
        self.assertEqual(
            review["staleness_summary"]["stale_validation_ids"],
            ["validation:test:stale-claim"],
        )

    def test_review_derives_low_trust_only_for_rumor_supported_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            write_yaml(
                repo / "sources" / "firsthand" / "review-rumor.yml",
                {
                    "schema_version": 1,
                    "kind": "source",
                    "id": "source:firsthand:review-rumor",
                    "source_type": "anonymous_report",
                    "title": "Review rumor source",
                    "public_status": "unknown",
                    "accessed_at": "2026-06-02T00:00:00Z",
                    "content_mode": "summary",
                    "risk_flags": ["anonymous_source"],
                },
            )
            write_yaml(
                repo / "evidence" / "firsthand" / "review-rumor.yml",
                {
                    "schema_version": 1,
                    "kind": "evidence",
                    "id": "evidence:firsthand:review-rumor",
                    "evidence_class": "rumor",
                    "source": "source:firsthand:review-rumor",
                    "summary": "Synthetic rumor evidence for review state.",
                    "content_mode": "summary",
                    "observed_at": "2026-06-02T00:00:00Z",
                    "submitted_by": "github:tester",
                    "source_attribution": "anonymous_to_public",
                    "source_access": {
                        "nda_or_confidentiality": "unknown",
                        "recording_available": False,
                        "source_identity_public": False,
                    },
                    "risk_flags": ["anonymous_source", "unverified_rumor"],
                },
            )
            write_yaml(
                repo / "claims" / "review-rumor.yml",
                {
                    "schema_version": 1,
                    "kind": "claim",
                    "id": "claim:test:review-rumor",
                    "statement": "Synthetic rumor says EXDEV has a product issue.",
                    "subject": "entity:company:exdev",
                    "predicate": "product_signal",
                    "object": "rumored product issue",
                    "support_type": "rumor",
                    "evidence": [{"id": "evidence:firsthand:review-rumor"}],
                    "submitted_by": "github:tester",
                },
            )

            status, build_payload = run_json_command(cli.run_index_build, repo)
            self.assertEqual(status, 0, build_payload)
            status, review = run_json_command(cli.run_review, repo, "claim:test:review-rumor")

        self.assertEqual(status, 0, review)
        self.assertEqual(review["review_state"]["primary_label"], "low_trust_only")
        self.assertIn("has_low_trust_support", review["review_state"]["flags"])
        self.assertEqual(
            review["support_summary"]["low_trust_evidence_ids"],
            ["evidence:firsthand:review-rumor"],
        )

    def test_review_handles_cyclic_thesis_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            write_yaml(
                repo / "theses" / "self-cycle.yml",
                {
                    "schema_version": 1,
                    "kind": "thesis",
                    "id": "thesis:test:self-cycle",
                    "title": "Self cycle thesis",
                    "summary": "Synthetic thesis with a cyclic thesis dependency.",
                    "depends_on": {
                        "evidence": ["evidence:synthetic:exdev-fy2025-supplier-note"],
                        "claims": [],
                        "relationships": [],
                        "theses": ["thesis:test:self-cycle"],
                        "metrics": [],
                        "events": [],
                        "datasets": [],
                    },
                    "submitted_by": "github:tester",
                },
            )

            status, build_payload = run_json_command(cli.run_index_build, repo)
            self.assertEqual(status, 0, build_payload)
            status, review = run_json_command(cli.run_review, repo, "thesis:test:self-cycle")

        self.assertEqual(status, 0, review)
        self.assertEqual(
            review["target_evidence_summary"]["evidence_ids"],
            ["evidence:synthetic:exdev-fy2025-supplier-note"],
        )

    def test_diff_review_flags_evidence_mutation_and_review_state_impact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            init_git_repo(repo)

            evidence_path = repo / "evidence" / "public" / "synthetic-exdev-fy2025-supplier-note.yml"
            evidence = load_yaml(evidence_path)
            evidence["excerpt"] = "Updated synthetic excerpt for diff-review."
            write_yaml(evidence_path, evidence)
            write_yaml(
                repo / "challenges" / "diff-review-open-challenge.yml",
                {
                    "schema_version": 1,
                    "kind": "challenge",
                    "id": "challenge:test:diff-review-open",
                    "target": "claim:synthetic:exdev-uses-fndwy-for-x1",
                    "submitted_by": "github:tester",
                    "challenge_type": "missing_evidence",
                    "summary": "Synthetic open challenge added by diff-review test.",
                    "depends_on": {
                        "evidence": ["evidence:synthetic:exdev-fy2025-supplier-note"],
                        "claims": ["claim:synthetic:exdev-uses-fndwy-for-x1"],
                        "relationships": [],
                        "theses": [],
                    },
                },
            )

            status, payload = run_json_command(cli.run_diff_review, repo, "HEAD")

        self.assertEqual(status, 0, payload)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["record_delta"]["total"]["added"], 1)
        self.assertEqual(payload["record_delta"]["total"]["modified"], 1)
        warning_codes = {warning["code"] for warning in payload["warnings"]}
        self.assertIn("modifies_canonical_evidence", warning_codes)
        self.assertIn("adds_or_updates_open_challenge", warning_codes)
        self.assertIn("review_state_changed", warning_codes)
        review_impacts = {item["id"]: item for item in payload["review_state_impact"]}
        self.assertEqual(
            review_impacts["claim:synthetic:exdev-uses-fndwy-for-x1"]["before"]["review_state"][
                "primary_label"
            ],
            "supported",
        )
        self.assertEqual(
            review_impacts["claim:synthetic:exdev-uses-fndwy-for-x1"]["after"]["review_state"][
                "primary_label"
            ],
            "contested",
        )
        self.assertIn(
            "challenge:test:diff-review-open",
            {item["id"] for item in payload["record_delta"]["added"]},
        )

    def test_diff_review_returns_validation_error_exit_for_invalid_current_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            init_git_repo(repo)
            write_yaml(
                repo / "claims" / "diff-review-invalid.yml",
                {
                    "schema_version": 1,
                    "kind": "claim",
                    "id": "claim:test:diff-review-invalid",
                    "statement": "Invalid diff-review claim references missing evidence.",
                    "subject": "entity:company:exdev",
                    "predicate": "product_signal",
                    "object": "missing evidence",
                    "support_type": "direct",
                    "evidence": [{"id": "evidence:test:missing"}],
                    "submitted_by": "github:tester",
                },
            )

            status, payload = run_json_command(cli.run_diff_review, repo, "HEAD")

        self.assertEqual(status, 1, payload)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["record_delta"]["total"]["added"], 1)
        self.assertIn("references missing id", payload["errors"][0]["message"])

    def test_new_source_evidence_and_claim_helpers_create_valid_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))

            status, source = run_new_json(
                cli.run_new_source,
                repo,
                source_type="other",
                title="Helper Source",
                public_status="public",
                accessed_at="2026-06-02T00:00:00Z",
                content_mode="small_fixture",
                submitted_by="github:tester",
                publisher="Finance OSINT tests",
                url=None,
                archive_url=None,
                published_at=None,
                provenance="Synthetic helper test.",
            )
            self.assertEqual(status, 0, source)

            status, evidence = run_new_json(
                cli.run_new_evidence,
                repo,
                evidence_class="public_primary",
                source=source["id"],
                summary="Helper evidence states a deterministic supplier relationship.",
                content_mode="small_fixture",
                observed_at="2026-06-02T00:00:00Z",
                submitted_by="github:tester",
                source_attribution="named_public",
                excerpt="Helper evidence excerpt.",
                locator=["section=Helper"],
                source_access_json=None,
                verification_status="synthetic_fixture",
            )
            self.assertEqual(status, 0, evidence)

            status, claim = run_new_json(
                cli.run_new_claim,
                repo,
                statement="Helper claim says EXDEV uses FNDWY.",
                subject="entity:company:exdev",
                predicate="disclosed_relationship",
                object="entity:company:fndwy",
                support_type="direct",
                evidence=[evidence["id"]],
                qualifier=["component=entity:component:x1-processor"],
                time_start=None,
                time_end=None,
                methodology=None,
                proposed_predicate_definition=None,
                submitted_by="github:tester",
            )
            self.assertEqual(status, 0, claim)

            status, output = run_lint(repo)

        self.assertEqual(status, 0, output)
        self.assertEqual(claim["record"]["evidence"], [{"id": evidence["id"]}])
        self.assertTrue(claim["path"].startswith("claims/generated/"))

    def test_new_source_helper_records_source_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            artifact = repo / "artifacts" / "sources" / "helper-source" / "screenshot.png"
            artifact.parent.mkdir(parents=True)
            artifact.write_bytes(b"small artifact")

            status, source = run_new_json(
                cli.run_new_source,
                repo,
                source_type="web_page",
                title="Helper Source With Artifact",
                public_status="public",
                accessed_at="2026-06-03T00:00:00Z",
                content_mode="external_link",
                submitted_by="github:tester",
                publisher="Finance OSINT tests",
                url="https://example.test/helper-source",
                archive_url=None,
                published_at=None,
                provenance="Synthetic helper artifact test.",
                source_artifact=["artifacts/sources/helper-source/screenshot.png"],
            )
            self.assertEqual(status, 0, source)

            status, payload = run_json_command(cli.run_lint, repo)

        self.assertEqual(status, 0, payload)
        self.assertEqual(payload["warnings"], [])
        self.assertEqual(
            source["record"]["source_artifacts"],
            ["artifacts/sources/helper-source/screenshot.png"],
        )

    def test_new_claim_helper_rejects_missing_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))

            status, payload = run_new_json(
                cli.run_new_claim,
                repo,
                statement="Helper claim with missing evidence.",
                subject="entity:company:exdev",
                predicate="disclosed_relationship",
                object="entity:company:fndwy",
                support_type="direct",
                evidence=["evidence:test:missing"],
                qualifier=[],
                time_start=None,
                time_end=None,
                methodology=None,
                proposed_predicate_definition=None,
                submitted_by="github:tester",
            )

        self.assertEqual(status, 1, payload)
        self.assertFalse(payload["ok"])
        self.assertIn("references missing id", payload["errors"][0]["message"])

    def test_new_relationship_helper_creates_valid_relationship(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))

            status, payload = run_new_json(
                cli.run_new_relationship,
                repo,
                type="supplier_relationship",
                participant=[
                    "buyer=entity:company:exdev",
                    "supplier=entity:company:fndwy",
                ],
                derived_claim=["claim:synthetic:exdev-uses-fndwy-for-x1"],
                derived_evidence=["evidence:synthetic:exdev-fy2025-supplier-note"],
                scope=["product=entity:product:example-phone"],
                qualifier=[],
                time_start=None,
                time_end=None,
                materiality_level="medium",
                materiality_basis="inferred",
                proposed_type_definition=None,
                submitted_by="github:tester",
            )
            self.assertEqual(status, 0, payload)

            status, output = run_lint(repo)

        self.assertEqual(status, 0, output)
        self.assertEqual(payload["record"]["participants"][0]["role"], "buyer")
        self.assertTrue(payload["path"].startswith("relationships/generated/"))

    def test_new_entity_metric_event_dataset_and_thesis_helpers_create_valid_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))

            status, entity = run_new_json(
                cli.run_new_entity,
                repo,
                entity_type="service",
                name="Helper Service",
                alias=["HS"],
                identifier=["internal=helper-service"],
                description="Synthetic service generated by helper tests.",
                state="proposed",
                submitted_by="github:tester",
            )
            self.assertEqual(status, 0, entity)

            status, metric = run_new_json(
                cli.run_new_metric,
                repo,
                entity="entity:company:exdev",
                metric_definition="metric_definition:revenue",
                value=123.0,
                unit="USD",
                period=["start=2025-01-01", "end=2025-12-31"],
                value_basis="reported",
                evidence=["evidence:synthetic:exdev-fy2025-supplier-note"],
                source_locator=["section=Synthetic supplier note"],
                dimension=["segment=synthetic"],
                as_of=None,
                reported_at=None,
                published_at=None,
                restated_from=None,
                methodology=None,
                limitations=None,
                submitted_by="github:tester",
            )
            self.assertEqual(status, 0, metric)

            status, event = run_new_json(
                cli.run_new_event,
                repo,
                event_type="product_launch",
                event_state="expected",
                title="Helper Product Launch",
                entity=["entity:company:exdev"],
                evidence=["evidence:synthetic:exdev-fy2025-supplier-note"],
                occurred_at=None,
                expected_at="2026-12-31",
                effective_at=None,
                period=[],
                property=["product=entity:product:example-phone"],
                submitted_by="github:tester",
            )
            self.assertEqual(status, 0, event)

            status, dataset = run_new_json(
                cli.run_new_dataset,
                repo,
                title="Helper Dataset",
                dataset_type="official_dataset",
                publisher="Finance OSINT tests",
                coverage=["start=2025-01-01", "end=2025-12-31"],
                access=["public_status=public"],
                source=["source:public:synthetic:exdev-fy2025-report"],
                content_mode="small_fixture",
                content_hash=None,
                license=None,
                limitations="Synthetic fixture only.",
                submitted_by="github:tester",
            )
            self.assertEqual(status, 0, dataset)

            status, thesis = run_new_json(
                cli.run_new_thesis,
                repo,
                title="Helper Thesis",
                summary="Synthetic thesis created from explicit dependencies.",
                stance="exploratory",
                time_horizon="12 months",
                forecast_json=None,
                contradicting_evidence=[],
                evidence=["evidence:synthetic:exdev-fy2025-supplier-note"],
                claim=["claim:synthetic:exdev-uses-fndwy-for-x1"],
                relationship=["relationship:synthetic:exdev-fndwy-x1-supply"],
                thesis=[],
                metric=[metric["id"]],
                event=[event["id"]],
                dataset=[dataset["id"]],
                submitted_by="github:tester",
            )
            self.assertEqual(status, 0, thesis)

            status, output = run_lint(repo)

        self.assertEqual(status, 0, output)
        self.assertTrue(entity["path"].startswith("entities/service/generated/"))
        self.assertTrue(metric["path"].startswith("metrics/generated/"))
        self.assertTrue(event["path"].startswith("events/generated/"))
        self.assertTrue(dataset["path"].startswith("datasets/generated/"))
        self.assertTrue(thesis["path"].startswith("theses/generated/"))
        self.assertEqual(thesis["record"]["depends_on"]["metrics"], [metric["id"]])


if __name__ == "__main__":
    unittest.main()
