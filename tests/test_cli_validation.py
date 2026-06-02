from __future__ import annotations

import argparse
import contextlib
import io
import shutil
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


if __name__ == "__main__":
    unittest.main()
