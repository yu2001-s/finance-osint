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
    "ontology",
    "records",
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


def run_json_command(func, *args, **kwargs) -> tuple[int, dict]:
    stderr = io.StringIO()
    stdout = io.StringIO()
    with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(stdout):
        status = func(*args, json_output=True, **kwargs)
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
    kwargs.setdefault("dry_run", False)
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

    def test_public_record_kinds_have_templates(self) -> None:
        template_dir = ROOT / "templates"
        for kind, schema_file in cli.SCHEMA_BY_KIND.items():
            template_name = schema_file.replace(".schema.json", ".yaml.template")
            template_path = template_dir / template_name
            self.assertTrue(template_path.exists(), f"missing template for {kind}")
            template = load_yaml(template_path)
            self.assertEqual(template.get("kind"), kind)

    def test_direct_claim_cannot_rely_only_on_rumor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            write_yaml(
                repo / "records" / "sources" / "firsthand" / "anonymous-rumor.yml",
                {
                    "schema_version": 1,
                    "kind": "source",
                    "id": "source:firsthand:anonymous-rumor",
                    "source_type": "anonymous_report",
                    "title": "Anonymous rumor fixture",
                    "public_status": "unknown",
                    "source_perspective": "anonymous_source",
                    "accessed_at": "2026-06-02T00:00:00Z",
                    "content_mode": "summary",
                    "risk_flags": ["anonymous_source"],
                },
            )
            write_yaml(
                repo / "records" / "evidence" / "firsthand" / "anonymous-rumor.yml",
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
                repo / "records" / "claims" / "anonymous-correlated-claim.yml",
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
        self.assertIn("direct support_type cannot rely only on low-trust evidence", output)

    def test_direct_claim_cannot_rely_only_on_anonymous_internal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            write_yaml(
                repo / "records" / "sources" / "firsthand" / "anonymous-internal.yml",
                {
                    "schema_version": 1,
                    "kind": "source",
                    "id": "source:firsthand:anonymous-internal",
                    "source_type": "anonymous_report",
                    "title": "Anonymous internal fixture",
                    "public_status": "unknown",
                    "source_perspective": "anonymous_source",
                    "accessed_at": "2026-06-02T00:00:00Z",
                    "content_mode": "summary",
                    "risk_flags": ["anonymous_source"],
                },
            )
            write_yaml(
                repo / "records" / "evidence" / "firsthand" / "anonymous-internal.yml",
                {
                    "schema_version": 1,
                    "kind": "evidence",
                    "id": "evidence:firsthand:anonymous-internal",
                    "evidence_class": "anonymous_internal",
                    "source": "source:firsthand:anonymous-internal",
                    "summary": "Anonymous internal fixture.",
                    "content_mode": "summary",
                    "observed_at": "2026-06-02T00:00:00Z",
                    "submitted_by": "github:tester",
                    "source_attribution": "anonymous_to_public",
                    "source_access": {
                        "nda_or_confidentiality": "unknown",
                        "recording_available": False,
                        "source_identity_public": False,
                    },
                    "risk_flags": ["anonymous_source", "unverified_internal"],
                },
            )
            write_yaml(
                repo / "records" / "claims" / "anonymous-internal-direct.yml",
                {
                    "schema_version": 1,
                    "kind": "claim",
                    "id": "claim:test:anonymous-internal-direct",
                    "statement": "Anonymous internal fixture directly establishes a product issue.",
                    "subject": "entity:company:exdev",
                    "predicate": "product_signal",
                    "object": "rumored product issue",
                    "support_type": "direct",
                    "evidence": [{"id": "evidence:firsthand:anonymous-internal"}],
                    "submitted_by": "github:tester",
                },
            )

            status, output = run_lint(repo)

        self.assertEqual(status, 1, output)
        self.assertIn("direct support_type cannot rely only on low-trust evidence", output)

    def test_claim_predicate_rejects_wrong_object_kind(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            write_yaml(
                repo / "records" / "claims" / "wrong-object-kind.yml",
                {
                    "schema_version": 1,
                    "kind": "claim",
                    "id": "claim:test:wrong-object-kind",
                    "statement": "Synthetic transaction disclosure points to a company object.",
                    "subject": "entity:company:exdev",
                    "predicate": "transaction_disclosure",
                    "object": "entity:company:fndwy",
                    "support_type": "direct",
                    "evidence": [{"id": "evidence:synthetic:exdev-fy2025-supplier-note"}],
                    "submitted_by": "github:tester",
                },
            )

            status, output = run_lint(repo)

        self.assertEqual(status, 1, output)
        self.assertIn("object kind `entity` is not allowed by predicate", output)

    def test_claim_predicate_rejects_missing_required_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            path = repo / "records" / "claims" / "synthetic-exdev-uses-fndwy-for-x1.yml"
            claim = load_yaml(path)
            claim.pop("object")
            write_yaml(path, claim)

            status, output = run_lint(repo)

        self.assertEqual(status, 1, output)
        self.assertIn("predicate `disclosed_relationship` requires field `object`", output)

    def test_claim_predicate_rejects_disallowed_context_reference_kind(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            path = repo / "records" / "claims" / "synthetic-exdev-uses-fndwy-for-x1.yml"
            claim = load_yaml(path)
            claim["qualifiers"]["source_context"] = "source:public:synthetic:exdev-fy2025-report"
            write_yaml(path, claim)

            status, output = run_lint(repo)

        self.assertEqual(status, 1, output)
        self.assertIn("references kind `source`, which is not allowed", output)

    def test_lint_rejects_hidden_agent_provenance_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            path = repo / "records" / "claims" / "synthetic-exdev-uses-fndwy-for-x1.yml"
            claim = load_yaml(path)
            claim["generated_by"] = "codex"
            claim["qualifiers"]["model"] = "gpt-test"
            write_yaml(path, claim)

            status, output = run_lint(repo)

        self.assertEqual(status, 1, output)
        self.assertIn("generated_by uses hidden agent provenance field", output)
        self.assertIn("qualifiers.model uses hidden agent provenance field", output)

    def test_relationship_materiality_level_must_match_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            path = repo / "records" / "relationships" / "synthetic-exdev-fndwy-x1-supply.yml"
            data = load_yaml(path)
            data["materiality"]["level"] = "existential"
            write_yaml(path, data)

            status, output = run_lint(repo)

        self.assertEqual(status, 1, output)
        self.assertIn("materiality level `existential` is not allowed", output)

    def test_relationship_qualifier_must_match_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            path = repo / "records" / "relationships" / "synthetic-exdev-fndwy-x1-supply.yml"
            data = load_yaml(path)
            data["qualifiers"] = ["secret_supplier"]
            write_yaml(path, data)

            status, output = run_lint(repo)

        self.assertEqual(status, 1, output)
        self.assertIn("qualifier `secret_supplier` is not allowed", output)

    def test_metric_unit_must_match_definition(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            path = repo / "records" / "metrics" / "axt" / "q1-2026-inp-revenue.yml"
            metric = load_yaml(path)
            metric["unit"] = "shares"
            write_yaml(path, metric)

            status, output = run_lint(repo)

        self.assertEqual(status, 1, output)
        self.assertIn("unit `shares` is not allowed by metric definition", output)

    def test_metric_value_basis_must_match_definition(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            path = repo / "records" / "metrics" / "xfab" / "price-to-sales-20260529.yml"
            metric = load_yaml(path)
            metric["value_basis"] = "reported"
            write_yaml(path, metric)

            status, output = run_lint(repo)

        self.assertEqual(status, 1, output)
        self.assertIn("value_basis `reported` is not allowed by metric definition", output)

    def test_metric_definition_must_be_registered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            path = repo / "ontology" / "metric-definitions" / "revenue.yml"
            definition = load_yaml(path)
            definition["state"] = "proposed"
            write_yaml(path, definition)

            status, output = run_lint(repo)

        self.assertEqual(status, 1, output)
        self.assertIn("metric_definition `metric_definition:revenue` is not registered", output)

    def test_registered_metric_definition_requires_allowed_units_and_basis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            path = repo / "ontology" / "metric-definitions" / "revenue.yml"
            definition = load_yaml(path)
            definition["allowed_units"] = []
            definition["allowed_value_basis"] = []
            write_yaml(path, definition)

            status, output = run_lint(repo)

        self.assertEqual(status, 1, output)
        self.assertIn("registered metric definition must declare allowed_units", output)
        self.assertIn("registered metric definition must declare allowed_value_basis", output)

    def test_metric_required_period_context_must_be_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            path = repo / "records" / "metrics" / "axt" / "q1-2026-inp-revenue.yml"
            metric = load_yaml(path)
            metric["period"] = {}
            write_yaml(path, metric)

            status, output = run_lint(repo)

        self.assertEqual(status, 1, output)
        self.assertIn("requires `period` context", output)

    def test_metric_required_as_of_context_must_be_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            path = repo / "records" / "metrics" / "fit-hon-teng" / "market-cap-20260529.yml"
            metric = load_yaml(path)
            metric.pop("as_of")
            metric["period"].pop("as_of")
            write_yaml(path, metric)

            status, output = run_lint(repo)

        self.assertEqual(status, 1, output)
        self.assertIn("requires `as_of` context", output)

    def test_metric_required_dimension_context_must_be_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            definition_path = repo / "ontology" / "metric-definitions" / "revenue.yml"
            definition = load_yaml(definition_path)
            definition["required_dimensions"] = ["period", "product"]
            write_yaml(definition_path, definition)
            metric_path = repo / "records" / "metrics" / "axt" / "q1-2026-inp-revenue.yml"
            metric = load_yaml(metric_path)
            metric["dimensions"].pop("product")
            write_yaml(metric_path, metric)

            status, output = run_lint(repo)

        self.assertEqual(status, 1, output)
        self.assertIn("requires `product` context", output)

    def test_metric_required_comparability_must_be_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            definition_path = repo / "ontology" / "metric-definitions" / "revenue.yml"
            definition = load_yaml(definition_path)
            definition["required_comparability"] = ["reporting_currency"]
            write_yaml(definition_path, definition)
            metric_path = repo / "records" / "metrics" / "foci" / "q1-2026-revenue.yml"
            metric = load_yaml(metric_path)
            metric["comparability"].pop("reporting_currency")
            write_yaml(metric_path, metric)

            status, output = run_lint(repo)

        self.assertEqual(status, 1, output)
        self.assertIn("requires `comparability.reporting_currency`", output)

    def test_lint_warns_for_recommended_metric_comparability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            definition_path = repo / "ontology" / "metric-definitions" / "market_cap.yml"
            definition = load_yaml(definition_path)
            definition["recommended_comparability"] = ["trading_currency"]
            write_yaml(definition_path, definition)
            metric_path = repo / "records" / "metrics" / "foci" / "market-cap-20260529.yml"
            metric = load_yaml(metric_path)
            metric["comparability"].pop("trading_currency")
            write_yaml(metric_path, metric)

            status, payload = run_json_command(cli.run_lint, repo)

        self.assertEqual(status, 0, payload)
        warning_codes = {warning["code"] for warning in payload["warnings"]}
        self.assertIn("metric_missing_recommended_comparability", warning_codes)

    def test_derived_and_estimated_metrics_require_methodology(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            derived_path = (
                repo
                / "records"
                / "metrics"
                / "synthetic-exdev"
                / "price-to-sales-derived-20260602.yml"
            )
            derived = load_yaml(derived_path)
            derived.pop("methodology")
            write_yaml(derived_path, derived)

            status, output = run_lint(repo)

        self.assertEqual(status, 1, output)
        self.assertIn("derived metric requires methodology", output)

    def test_restated_metric_requires_restated_from(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            metric_path = (
                repo
                / "records"
                / "metrics"
                / "synthetic-exdev"
                / "fy2025-revenue-restated.yml"
            )
            metric = load_yaml(metric_path)
            metric.pop("restated_from")
            write_yaml(metric_path, metric)

            status, output = run_lint(repo)

        self.assertEqual(status, 1, output)
        self.assertIn("restated metric requires restated_from", output)

    def test_estimated_metric_without_limitations_warns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            metric_path = (
                repo
                / "records"
                / "metrics"
                / "synthetic-exdev"
                / "fy2026-revenue-estimated.yml"
            )
            metric = load_yaml(metric_path)
            metric.pop("limitations")
            write_yaml(metric_path, metric)

            status, payload = run_json_command(cli.run_lint, repo)

        self.assertEqual(status, 0, payload)
        self.assertEqual(
            [warning["code"] for warning in payload["warnings"]],
            ["estimated_metric_missing_limitations"],
        )

    def test_metric_accepts_structured_fx_methodology(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            metric_path = repo / "records" / "metrics" / "foci" / "q1-2026-revenue.yml"
            metric = load_yaml(metric_path)
            metric["unit"] = "USD"
            metric["comparability"]["fx_methodology"] = {
                "method": "period_end_spot_rate",
                "from_currency": "TWD",
                "to_currency": "USD",
                "rate": "0.0312",
                "rate_date": "2026-03-31",
                "rate_source": "evidence:public:foci:q1-2026-financial-report",
            }
            write_yaml(metric_path, metric)

            status, payload = run_json_command(cli.run_lint, repo)

        self.assertEqual(status, 0, payload)
        self.assertEqual(payload["warnings"], [])

    def test_metric_value_basis_fixture_examples_cover_all_kinds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            records, errors = cli.load_records(repo)

        self.assertEqual(errors, [])
        value_bases = {
            record.data.get("value_basis")
            for record in records
            if record.kind == "metric"
        }
        self.assertTrue(
            {"reported", "observed", "derived", "estimated", "restated"}.issubset(value_bases)
        )

    def test_review_chain_includes_derived_metric_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            records, errors = cli.load_records(repo)
            self.assertEqual(errors, [])
            id_map, id_errors = cli.build_id_map(repo, records)
            self.assertEqual(id_errors, [])
            target = id_map["metric:synthetic-exdev:price-to-sales-derived-20260602"]

            dependencies = cli.chain_dependency_ids(target, id_map)

        self.assertIn(
            "metric:synthetic-exdev:fy2025-revenue-restated",
            dependencies["metrics"],
        )

    def test_challenge_references_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            write_yaml(
                repo / "records" / "challenges" / "missing-reference.yml",
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

    def test_source_requires_source_perspective(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            write_yaml(
                repo / "records" / "sources" / "public" / "missing-perspective.yml",
                {
                    "schema_version": 1,
                    "kind": "source",
                    "id": "source:test:missing-perspective",
                    "source_type": "web_page",
                    "title": "Missing source perspective",
                    "url": "https://example.test/missing-perspective",
                    "archive_url": "https://web.archive.org/example-missing-perspective",
                    "public_status": "public",
                    "accessed_at": "2026-06-03T00:00:00Z",
                    "content_mode": "external_link",
                },
            )

            status, payload = run_json_command(cli.run_lint, repo)

        self.assertEqual(status, 1, payload)
        self.assertFalse(payload["ok"])
        self.assertIn("source_perspective", payload["errors"][0]["message"])

    def test_lint_warns_for_unknown_source_perspective(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            write_yaml(
                repo / "records" / "sources" / "public" / "unknown-perspective.yml",
                {
                    "schema_version": 1,
                    "kind": "source",
                    "id": "source:test:unknown-perspective",
                    "source_type": "web_page",
                    "title": "Unknown source perspective",
                    "url": "https://example.test/unknown-perspective",
                    "archive_url": "https://web.archive.org/example-unknown-perspective",
                    "public_status": "public",
                    "source_perspective": "unknown",
                    "accessed_at": "2026-06-03T00:00:00Z",
                    "content_mode": "external_link",
                },
            )

            status, payload = run_json_command(cli.run_lint, repo)

        self.assertEqual(status, 0, payload)
        self.assertEqual(
            [warning["code"] for warning in payload["warnings"]],
            ["unknown_source_perspective"],
        )

    def test_lint_warns_for_duplicate_global_filing_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            source = load_yaml(
                repo
                / "records"
                / "sources"
                / "public"
                / "foci"
                / "q1-2026-financial-report.yml"
            )
            source["id"] = "source:public:foci:q1-2026-financial-report-alt"
            source["title"] = "Duplicate FOCI MOPS financial report for Q1 2026"
            source["url"] = "https://example.test/duplicate-foci-filing"
            write_yaml(
                repo
                / "records"
                / "sources"
                / "public"
                / "foci"
                / "q1-2026-financial-report-alt.yml",
                source,
            )

            status, payload = run_json_command(cli.run_lint, repo)

        self.assertEqual(status, 0, payload)
        warning_codes = {warning["code"] for warning in payload["warnings"]}
        self.assertIn("possible_duplicate_source_filing_identity", warning_codes)
        warning = next(
            warning
            for warning in payload["warnings"]
            if warning["code"] == "possible_duplicate_source_filing_identity"
        )
        self.assertEqual(warning["record_id"], "source:public:foci:q1-2026-financial-report")
        self.assertEqual(
            warning["related_ids"],
            ["source:public:foci:q1-2026-financial-report-alt"],
        )

    def test_submitted_by_shape_is_validated_when_present_on_foundational_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            write_yaml(
                repo / "records" / "sources" / "public" / "bad-submitter-source.yml",
                {
                    "schema_version": 1,
                    "kind": "source",
                    "id": "source:test:bad-submitter-source",
                    "source_type": "web_page",
                    "title": "Bad submitter source",
                    "url": "https://example.test/bad-submitter-source",
                    "archive_url": "https://web.archive.org/example-bad-submitter-source",
                    "public_status": "public",
                    "source_perspective": "independent_media",
                    "accessed_at": "2026-06-03T00:00:00Z",
                    "content_mode": "external_link",
                    "submitted_by": "tester",
                },
            )
            write_yaml(
                repo / "records" / "entities" / "company" / "bad-submitter-entity.yml",
                {
                    "schema_version": 1,
                    "kind": "entity",
                    "id": "entity:company:bad-submitter-entity",
                    "entity_type": "company",
                    "name": "Bad Submitter Entity",
                    "submitted_by": "tester",
                },
            )
            write_yaml(
                repo / "records" / "datasets" / "bad-submitter-dataset.yml",
                {
                    "schema_version": 1,
                    "kind": "dataset",
                    "id": "dataset:test:bad-submitter-dataset",
                    "title": "Bad submitter dataset",
                    "dataset_type": "official_dataset",
                    "publisher": "Finance OSINT tests",
                    "coverage": {"period": "fixture"},
                    "access": {"public_status": "public"},
                    "sources": ["source:public:synthetic-exdev-fy2025-report"],
                    "content_mode": "small_fixture",
                    "submitted_by": "tester",
                },
            )

            status, payload = run_json_command(cli.run_lint, repo)

        self.assertEqual(status, 1, payload)
        messages = "\n".join(error["message"] for error in payload["errors"])
        self.assertEqual(messages.count("does not match '^github:[A-Za-z0-9_.-]+$'"), 3)

    def test_lint_warns_for_mutable_source_without_preservation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            write_yaml(
                repo / "records" / "sources" / "public" / "mutable-web-source.yml",
                {
                    "schema_version": 1,
                    "kind": "source",
                    "id": "source:test:mutable-web-source",
                    "source_type": "web_page",
                    "title": "Mutable web source",
                    "url": "https://example.test/mutable",
                    "public_status": "public",
                    "source_perspective": "independent_media",
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

    def test_lint_warns_for_exchange_filing_without_durable_preservation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            write_yaml(
                repo / "records" / "sources" / "public" / "unpreserved-exchange-filing.yml",
                {
                    "schema_version": 1,
                    "kind": "source",
                    "id": "source:test:unpreserved-exchange-filing",
                    "source_type": "exchange_filing",
                    "title": "Unpreserved exchange filing",
                    "url": "https://example.test/unpreserved-filing.pdf",
                    "public_status": "public",
                    "source_perspective": "company_self",
                    "accessed_at": "2026-06-03T00:00:00Z",
                    "content_mode": "external_link",
                    "filing_jurisdiction": "HK",
                    "filing_authority": "HKEXnews",
                    "filing_regime": "hkex_listed_company_announcement",
                    "local_form_type": "quarterly_financial_information",
                    "issuer_code": "9999",
                    "report_period": "2026-Q1",
                    "filing_date": "2026-05-11",
                    "source_language": "en",
                    "preservation_path": "external:hkexnews/unpreserved-filing.pdf",
                },
            )

            status, payload = run_json_command(cli.run_lint, repo)

        self.assertEqual(status, 0, payload)
        self.assertEqual(
            [warning["code"] for warning in payload["warnings"]],
            ["mutable_source_without_preservation"],
        )

    def test_lint_rejects_partial_filing_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            source = load_yaml(
                repo
                / "records"
                / "sources"
                / "public"
                / "foci"
                / "q1-2026-financial-report.yml"
            )
            source["filing_date"] = "2026-05"
            write_yaml(
                repo
                / "records"
                / "sources"
                / "public"
                / "foci"
                / "bad-filing-date.yml",
                source,
            )

            status, payload = run_json_command(cli.run_lint, repo)

        self.assertEqual(status, 1, payload)
        messages = "\n".join(error["message"] for error in payload["errors"])
        self.assertIn("filing_date", messages)
        self.assertIn("does not match", messages)

    def test_lint_warns_for_non_english_excerpt_without_translation_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            write_yaml(
                repo / "records" / "sources" / "public" / "non-english-source.yml",
                {
                    "schema_version": 1,
                    "kind": "source",
                    "id": "source:test:non-english-source",
                    "source_type": "company_report",
                    "title": "Non-English source",
                    "public_status": "public",
                    "source_perspective": "company_self",
                    "accessed_at": "2026-06-03T00:00:00Z",
                    "content_mode": "external_link",
                    "source_language": "zh-Hant",
                },
            )
            write_yaml(
                repo / "records" / "evidence" / "public" / "non-english-evidence.yml",
                {
                    "schema_version": 1,
                    "kind": "evidence",
                    "id": "evidence:test:non-english-evidence",
                    "evidence_class": "public_primary",
                    "source": "source:test:non-english-source",
                    "summary": "Non-English evidence without translation provenance.",
                    "content_mode": "excerpt",
                    "excerpt": "Reviewer-facing translated excerpt without source-language provenance.",
                    "observed_at": "2026-06-03T00:00:00Z",
                    "submitted_by": "github:tester",
                    "source_attribution": "named_public",
                },
            )

            status, payload = run_json_command(cli.run_lint, repo)

        self.assertEqual(status, 0, payload)
        self.assertEqual(
            [warning["code"] for warning in payload["warnings"]],
            ["non_english_excerpt_without_translation_provenance"],
        )

    def test_lint_warns_for_global_report_without_source_language(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            write_yaml(
                repo / "records" / "sources" / "public" / "missing-source-language.yml",
                {
                    "schema_version": 1,
                    "kind": "source",
                    "id": "source:test:missing-source-language",
                    "source_type": "company_report",
                    "title": "Missing source language report",
                    "public_status": "public",
                    "source_perspective": "company_self",
                    "accessed_at": "2026-06-03T00:00:00Z",
                    "content_mode": "metadata_only",
                },
            )

            status, payload = run_json_command(cli.run_lint, repo)

        self.assertEqual(status, 0, payload)
        self.assertEqual(
            [warning["code"] for warning in payload["warnings"]],
            ["missing_source_language_for_global_source"],
        )

    def test_lint_warns_for_ocr_translation_without_quality_notes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            write_yaml(
                repo / "records" / "sources" / "public" / "ocr-source.yml",
                {
                    "schema_version": 1,
                    "kind": "source",
                    "id": "source:test:ocr-source",
                    "source_type": "company_report",
                    "title": "OCR source",
                    "public_status": "public",
                    "source_perspective": "company_self",
                    "accessed_at": "2026-06-03T00:00:00Z",
                    "content_mode": "external_link",
                    "source_language": "zh-Hant",
                },
            )
            write_yaml(
                repo / "records" / "evidence" / "public" / "ocr-evidence.yml",
                {
                    "schema_version": 1,
                    "kind": "evidence",
                    "id": "evidence:test:ocr-evidence",
                    "evidence_class": "public_primary",
                    "source": "source:test:ocr-source",
                    "summary": "OCR evidence missing quality notes.",
                    "content_mode": "excerpt",
                    "excerpt": "Translated excerpt.",
                    "original_excerpt": "原文摘錄。",
                    "translated_excerpt": "Translated excerpt.",
                    "translation": {
                        "source_language": "zh-Hant",
                        "translated_language": "en",
                        "translator": "github:tester",
                        "machine_translation": True,
                        "translation_date": "2026-06-03",
                        "translation_version": "fixture-v1",
                    },
                    "ocr": {"used": True, "engine": "fixture-ocr"},
                    "observed_at": "2026-06-03T00:00:00Z",
                    "submitted_by": "github:tester",
                    "source_attribution": "named_public",
                },
            )

            status, payload = run_json_command(cli.run_lint, repo)

        self.assertEqual(status, 0, payload)
        self.assertEqual(
            [warning["code"] for warning in payload["warnings"]],
            ["non_english_excerpt_without_translation_provenance"],
        )

    def test_lint_accepts_referenced_source_artifact_for_mutable_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            artifact = repo / "artifacts" / "sources" / "mutable-web-source" / "screenshot.png"
            artifact.parent.mkdir(parents=True)
            artifact.write_bytes(b"small artifact")
            write_yaml(
                repo / "records" / "sources" / "public" / "mutable-web-source.yml",
                {
                    "schema_version": 1,
                    "kind": "source",
                    "id": "source:test:mutable-web-source",
                    "source_type": "web_page",
                    "title": "Mutable web source",
                    "url": "https://example.test/mutable",
                    "public_status": "public",
                    "source_perspective": "independent_media",
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
                repo / "records" / "sources" / "public" / "bad-artifact-path.yml",
                {
                    "schema_version": 1,
                    "kind": "source",
                    "id": "source:test:bad-artifact-path",
                    "source_type": "web_page",
                    "title": "Bad artifact path",
                    "public_status": "public",
                    "source_perspective": "independent_media",
                    "accessed_at": "2026-06-03T00:00:00Z",
                    "content_mode": "external_link",
                    "source_artifacts": ["screenshots/bad.png"],
                },
            )

            status, output = run_lint(repo)

        self.assertEqual(status, 1, output)
        self.assertIn("source_artifacts", output)
        self.assertIn("artifacts/sources", output)

    def test_lint_warns_for_possible_current_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))

            entity = load_yaml(repo / "records" / "entities" / "company" / "exdev.yml")
            entity["id"] = "entity:company:exdev-alt"
            entity["name"] = "Synthetic Example Devices Alternate"
            write_yaml(repo / "records" / "entities" / "company" / "exdev-alt.yml", entity)

            source = load_yaml(
                repo / "records" / "sources" / "public" / "synthetic-exdev-fy2025-report.yml"
            )
            source["url"] = "https://example.test/reports/exdev-fy2025"
            write_yaml(repo / "records" / "sources" / "public" / "synthetic-exdev-fy2025-report.yml", source)
            source["id"] = "source:public:synthetic:exdev-fy2025-report-alt"
            source["title"] = "Synthetic Example Devices FY2025 Report Alternate"
            write_yaml(
                repo / "records" / "sources" / "public" / "synthetic-exdev-fy2025-report-alt.yml",
                source,
            )

            evidence = load_yaml(
                repo / "records" / "evidence" / "public" / "synthetic-exdev-fy2025-supplier-note.yml"
            )
            evidence["id"] = "evidence:synthetic:exdev-fy2025-supplier-note-alt"
            write_yaml(
                repo / "records" / "evidence" / "public" / "synthetic-exdev-fy2025-supplier-note-alt.yml",
                evidence,
            )

            claim = load_yaml(repo / "records" / "claims" / "synthetic-exdev-uses-fndwy-for-x1.yml")
            claim["id"] = "claim:synthetic:exdev-uses-fndwy-for-x1-alt"
            write_yaml(repo / "records" / "claims" / "synthetic-exdev-uses-fndwy-for-x1-alt.yml", claim)

            relationship = load_yaml(
                repo / "records" / "relationships" / "synthetic-exdev-fndwy-x1-supply.yml"
            )
            relationship["id"] = "relationship:synthetic:exdev-fndwy-x1-supply-alt"
            write_yaml(
                repo / "records" / "relationships" / "synthetic-exdev-fndwy-x1-supply-alt.yml",
                relationship,
            )

            status, payload = run_json_command(cli.run_lint, repo)

        self.assertEqual(status, 0, payload)
        warning_codes = {warning["code"] for warning in payload["warnings"]}
        self.assertIn("possible_duplicate_entity_identifier", warning_codes)
        self.assertIn("possible_duplicate_source_url", warning_codes)
        self.assertIn("possible_duplicate_evidence_locator", warning_codes)
        self.assertIn("possible_duplicate_claim_core", warning_codes)
        self.assertIn("possible_duplicate_relationship_core", warning_codes)
        entity_warning = next(
            warning
            for warning in payload["warnings"]
            if warning["code"] == "possible_duplicate_entity_identifier"
        )
        self.assertEqual(entity_warning["record_id"], "entity:company:exdev")
        self.assertEqual(entity_warning["related_ids"], ["entity:company:exdev-alt"])

    def test_lint_warns_for_duplicate_listing_symbol_and_mic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            listing = load_yaml(
                repo
                / "records"
                / "entities"
                / "listing"
                / "synthetic-global-tech-nasdaq-ads.yml"
            )
            listing["id"] = "entity:listing:synthetic-global-tech-nasdaq-ads-alt"
            listing["name"] = "Synthetic Global Technology duplicate NASDAQ ADS listing"
            listing["identifiers"] = {
                "local_symbol": listing["identifiers"]["local_symbol"],
                "mic": listing["identifiers"]["mic"],
            }
            write_yaml(
                repo / "records" / "entities" / "listing" / "synthetic-global-tech-nasdaq-ads-alt.yml",
                listing,
            )

            status, payload = run_json_command(cli.run_lint, repo)

        self.assertEqual(status, 0, payload)
        warning_codes = {warning["code"] for warning in payload["warnings"]}
        self.assertIn("possible_duplicate_listing_symbol_mic", warning_codes)
        listing_warning = next(
            warning
            for warning in payload["warnings"]
            if warning["code"] == "possible_duplicate_listing_symbol_mic"
        )
        self.assertEqual(
            listing_warning["record_id"],
            "entity:listing:synthetic-global-tech-nasdaq-ads",
        )
        self.assertEqual(
            listing_warning["related_ids"],
            ["entity:listing:synthetic-global-tech-nasdaq-ads-alt"],
        )

    def test_lint_duplicate_detection_ignores_archive_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            claim = load_yaml(repo / "records" / "claims" / "synthetic-exdev-uses-fndwy-for-x1.yml")
            claim["id"] = "claim:synthetic:archived-duplicate"
            claim["duplicate_of"] = "claim:synthetic:exdev-uses-fndwy-for-x1"
            write_yaml(repo / "archive" / "claims" / "archived-duplicate.yml", claim)

            status, payload = run_json_command(cli.run_lint, repo)

        self.assertEqual(status, 0, payload)
        warning_codes = {warning["code"] for warning in payload["warnings"]}
        self.assertNotIn("possible_duplicate_claim_core", warning_codes)

    def test_archive_record_requires_reason_or_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            claim = load_yaml(repo / "records" / "claims" / "synthetic-exdev-uses-fndwy-for-x1.yml")
            (repo / "records" / "claims" / "synthetic-exdev-uses-fndwy-for-x1.yml").unlink()
            write_yaml(repo / "archive" / "claims" / "synthetic-exdev-uses-fndwy-for-x1.yml", claim)

            status, output = run_lint(repo)

        self.assertEqual(status, 1, output)
        self.assertIn("archived records must include", output)

    def test_archive_record_with_superseded_by_lints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            original_path = repo / "records" / "claims" / "synthetic-exdev-uses-fndwy-for-x1.yml"
            claim = load_yaml(original_path)
            original_path.unlink()
            claim["superseded_by"] = "claim:test:replacement"
            replacement = dict(claim)
            replacement["id"] = "claim:test:replacement"
            replacement["statement"] = "Replacement synthetic supplier-use claim."
            write_yaml(repo / "archive" / "claims" / "synthetic-exdev-uses-fndwy-for-x1.yml", claim)
            write_yaml(repo / "records" / "claims" / "replacement.yml", replacement)
            thesis_path = repo / "records" / "theses" / "synthetic-exdev-margin-risk-from-foundry-concentration.yml"
            thesis = load_yaml(thesis_path)
            thesis["depends_on"]["claims"] = ["claim:test:replacement"]
            write_yaml(thesis_path, thesis)
            challenge_path = repo / "records" / "challenges" / "synthetic-exdev-margin-risk-needs-alternatives.yml"
            challenge = load_yaml(challenge_path)
            challenge["depends_on"]["claims"] = ["claim:test:replacement"]
            write_yaml(challenge_path, challenge)
            validation_path = repo / "records" / "validations" / "synthetic-exdev-uses-fndwy-for-x1.yml"
            validation = load_yaml(validation_path)
            validation["target"] = "claim:test:replacement"
            validation["depends_on"]["claims"] = ["claim:test:replacement"]
            write_yaml(validation_path, validation)
            relationship_path = repo / "records" / "relationships" / "synthetic-exdev-fndwy-x1-supply.yml"
            relationship = load_yaml(relationship_path)
            relationship["derived_from"]["claims"] = ["claim:test:replacement"]
            write_yaml(relationship_path, relationship)

            status, output = run_lint(repo)

        self.assertEqual(status, 0, output)

    def test_current_record_cannot_depend_on_archived_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            evidence_path = repo / "records" / "evidence" / "public" / "synthetic-exdev-fy2025-supplier-note.yml"
            evidence = load_yaml(evidence_path)
            evidence_path.unlink()
            evidence["archive_reason"] = "Archived for test fixture."
            write_yaml(
                repo / "archive" / "evidence" / "public" / "synthetic-exdev-fy2025-supplier-note.yml",
                evidence,
            )

            status, output = run_lint(repo)

        self.assertEqual(status, 1, output)
        self.assertIn("references archived record", output)

    def test_diff_review_warns_when_record_moves_to_archive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            init_git_repo(repo)
            original_path = repo / "records" / "claims" / "synthetic-exdev-uses-fndwy-for-x1.yml"
            archived_path = repo / "archive" / "claims" / "synthetic-exdev-uses-fndwy-for-x1.yml"
            claim = load_yaml(original_path)
            claim["archive_reason"] = "Archived for diff-review test."
            original_path.unlink()
            write_yaml(archived_path, claim)
            thesis_path = repo / "records" / "theses" / "synthetic-exdev-margin-risk-from-foundry-concentration.yml"
            thesis = load_yaml(thesis_path)
            thesis["depends_on"]["claims"] = []
            write_yaml(thesis_path, thesis)
            challenge_path = repo / "records" / "challenges" / "synthetic-exdev-margin-risk-needs-alternatives.yml"
            challenge = load_yaml(challenge_path)
            challenge["depends_on"]["claims"] = []
            write_yaml(challenge_path, challenge)
            validation_path = repo / "records" / "validations" / "synthetic-exdev-uses-fndwy-for-x1.yml"
            validation = load_yaml(validation_path)
            validation["depends_on"]["claims"] = []
            validation["target"] = "evidence:synthetic:exdev-fy2025-supplier-note"
            write_yaml(validation_path, validation)
            relationship_path = repo / "records" / "relationships" / "synthetic-exdev-fndwy-x1-supply.yml"
            relationship = load_yaml(relationship_path)
            relationship["derived_from"]["claims"] = []
            write_yaml(relationship_path, relationship)

            status, payload = run_json_command(cli.run_diff_review, repo, "HEAD")

        self.assertEqual(status, 0, payload)
        warning_codes = {warning["code"] for warning in payload["warnings"]}
        self.assertIn("moves_record_to_archive", warning_codes)

    def test_index_build_and_search_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))

            status, payload = run_json_command(cli.run_index_build, repo)
            self.assertEqual(status, 0, payload)
            self.assertTrue((repo / ".local" / "index.sqlite").exists())
            records, errors = cli.load_records(repo)
            self.assertEqual(errors, [])
            self.assertEqual(payload["records_indexed"], len(records))

            status, payload = run_json_command(cli.run_search, repo, "exdev")

        self.assertEqual(status, 0, payload)
        self.assertTrue(payload["ok"])
        self.assertGreater(payload["result_count"], 0)
        self.assertIn(
            "entity:company:exdev",
            {result["id"] for result in payload["results"]},
        )

    def test_graph_data_keeps_nested_id_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            records, errors = cli.load_records(repo)
            self.assertEqual(errors, [])
            graph = cli.build_graph_data(repo, records)

        graph_edges = {
            (edge["from"], edge["to"], edge.get("field"))
            for edge in graph["edges"]
        }
        self.assertIn(
            (
                "claim:synthetic:exdev-uses-fndwy-for-x1",
                "evidence:synthetic:exdev-fy2025-supplier-note",
                "evidence.0.id",
            ),
            graph_edges,
        )

    def test_global_identity_fixture_links_company_security_listing_and_adr(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            records, errors = cli.load_records(repo)
            self.assertEqual(errors, [])
            graph = cli.build_graph_data(repo, records)

        graph_edges = {
            (edge["from"], edge["to"], edge.get("field"))
            for edge in graph["edges"]
        }
        self.assertIn(
            (
                "entity:security:synthetic-global-tech-ads",
                "entity:security:synthetic-global-tech-ordinary-shares",
                "underlying_security",
            ),
            graph_edges,
        )
        self.assertIn(
            (
                "entity:listing:synthetic-global-tech-nasdaq-ads",
                "entity:security:synthetic-global-tech-ads",
                "security",
            ),
            graph_edges,
        )
        self.assertIn(
            (
                "entity:listing:synthetic-global-tech-twse",
                "entity:company:synthetic-global-tech",
                "issuer",
            ),
            graph_edges,
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
            self.assertEqual(
                review["support_summary"]["source_independence"][
                    "source_perspective_counts"
                ],
                {"synthetic_fixture": 1},
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

    def test_context_review_and_neighbors_suggest_close_record_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            status, build_payload = run_json_command(cli.run_index_build, repo)
            self.assertEqual(status, 0, build_payload)

            typo = "claim:synthetic:exdev-uses-fndwy-for-xl"
            status, context = run_json_command(cli.run_context, repo, typo)
            self.assertEqual(status, 1, context)
            status, review = run_json_command(cli.run_review, repo, typo)
            self.assertEqual(status, 1, review)
            status, neighbors = run_json_command(cli.run_graph_neighbors, repo, typo)

        self.assertEqual(status, 1, neighbors)
        expected = "claim:synthetic:exdev-uses-fndwy-for-x1"
        for payload in (context, review, neighbors):
            error = payload["errors"][0]
            self.assertEqual(error["code"], "record_not_found")
            self.assertIn(expected, error["related_ids"])
            self.assertIn("Did you mean:", error["hint"])

    def test_context_review_and_neighbors_hint_for_archived_exact_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            archived_id = "claim:test:archived-hint"
            write_yaml(
                repo / "archive" / "records" / "claims" / "archived-hint.yml",
                {
                    "schema_version": 1,
                    "kind": "claim",
                    "id": archived_id,
                    "statement": "Archived hint fixture.",
                    "subject": "entity:company:exdev",
                    "predicate": "disclosed_relationship",
                    "object": "entity:company:fndwy",
                    "support_type": "direct",
                    "evidence": [{"id": "evidence:synthetic:exdev-fy2025-supplier-note"}],
                    "submitted_by": "github:tester",
                    "archive_reason": "Synthetic archive hint fixture.",
                },
            )

            status, build_payload = run_json_command(cli.run_index_build, repo)
            self.assertEqual(status, 0, build_payload)
            status, context = run_json_command(cli.run_context, repo, archived_id)
            self.assertEqual(status, 1, context)
            status, review = run_json_command(cli.run_review, repo, archived_id)
            self.assertEqual(status, 1, review)
            status, neighbors = run_json_command(cli.run_graph_neighbors, repo, archived_id)
            self.assertEqual(status, 1, neighbors)
            status, archived_context = run_json_command(
                cli.run_context,
                repo,
                archived_id,
                include_archive=True,
            )
            self.assertEqual(status, 0, archived_context)
            status, archived_typo_neighbors = run_json_command(
                cli.run_graph_neighbors,
                repo,
                "claim:test:archived-hint-typo",
            )

        self.assertEqual(status, 1, archived_typo_neighbors)
        self.assertNotIn(archived_id, archived_typo_neighbors["errors"][0]["related_ids"])
        for payload in (context, review, neighbors):
            error = payload["errors"][0]
            self.assertEqual(error["code"], "record_not_found")
            self.assertEqual(error["related_ids"], [archived_id])
            self.assertIn("--include-archive", error["hint"])

        fallback = cli.record_not_found_error("claim:test:no-match", include_archive=True)
        self.assertIn('fo search "no-match" --include-archive --json', fallback["hint"])

    def test_qualified_supplier_fixture_surfaces_strong_relationship_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            status, build_payload = run_json_command(cli.run_index_build, repo)
            self.assertEqual(status, 0, build_payload)

            status, review = run_json_command(
                cli.run_review,
                repo,
                "relationship:synthetic:exdev-fndwy-x1-qualified-supplier",
                chain=True,
            )

        self.assertEqual(status, 0, review)
        chain = review["chain_summary"]
        self.assertIn(
            "relationship:synthetic:exdev-fndwy-x1-qualified-supplier",
            chain["relationship_chain"]["strong_relationship_type_ids"],
        )
        self.assertEqual(chain["relationship_chain"]["type_counts"]["qualified_supplier"], 1)
        self.assertIn(
            "evidence:synthetic:exdev-fy2025-avl-note",
            chain["source_evidence_chain"]["evidence_ids"],
        )
        self.assertTrue(chain["relationship_promotion_pressure"]["has_pressure"])
        self.assertIn(
            "supplier_allocation_unproven",
            chain["relationship_promotion_pressure"]["promotion_risk_flags"],
        )

    def test_review_surfaces_company_originated_only_support(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            status, build_payload = run_json_command(cli.run_index_build, repo)
            self.assertEqual(status, 0, build_payload)

            status, review = run_json_command(
                cli.run_review,
                repo,
                "thesis:aaoi:order-backed-ramp-watch",
            )

        self.assertEqual(status, 0, review)
        self.assertEqual(review["review_state"]["primary_label"], "contested")
        self.assertIn("company_originated_only_support", review["review_state"]["flags"])
        source_summary = review["support_summary"]["source_independence"]
        self.assertEqual(source_summary["unique_source_count"], 3)
        self.assertEqual(source_summary["company_originated_source_count"], 3)
        self.assertEqual(source_summary["independent_source_count"], 0)
        self.assertEqual(source_summary["source_perspective_counts"], {"company_self": 3})

    def test_review_chain_summary_surfaces_source_to_claim_chain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            status, build_payload = run_json_command(cli.run_index_build, repo)
            self.assertEqual(status, 0, build_payload)

            status, plain_review = run_json_command(
                cli.run_review,
                repo,
                "thesis:xfab-navitas:800-vdc-foundry-watch",
            )
            self.assertEqual(status, 0, plain_review)
            self.assertNotIn("chain_summary", plain_review)

            status, review = run_json_command(
                cli.run_review,
                repo,
                "thesis:xfab-navitas:800-vdc-foundry-watch",
                chain=True,
            )

        self.assertEqual(status, 0, review)
        chain = review["chain_summary"]
        self.assertEqual(chain["target"]["kind"], "thesis")
        self.assertEqual(chain["source_evidence_chain"]["evidence_count"], 9)
        self.assertEqual(
            chain["source_evidence_chain"]["evidence_class_counts"],
            {"public_primary": 6, "public_secondary": 3},
        )
        self.assertEqual(chain["dependency_counts"]["claims"], 7)
        self.assertEqual(chain["dependency_counts"]["relationships"], 4)
        self.assertEqual(chain["dependency_counts"]["metrics"], 6)
        self.assertEqual(chain["dependency_counts"]["events"], 1)
        self.assertEqual(chain["question_summary"]["open_count"], 2)
        self.assertEqual(
            chain["question_summary"]["open_question_ids"],
            [
                "question:xfab:navitas-nvidia-revenue-bridge",
                "question:xfab:wbg-revenue-customer-split",
            ],
        )
        self.assertEqual(chain["challenge_summary"]["open_count"], 2)
        self.assertIn(
            "relationship:navitas:xfab-sic-manufacturing-partner",
            chain["relationship_chain"]["strong_relationship_type_ids"],
        )
        self.assertEqual(
            chain["relationship_chain"]["type_counts"]["manufacturing_partner"],
            1,
        )
        self.assertIn(
            "nvidia_allocation_unproven",
            chain["relationship_promotion_pressure"]["promotion_risk_flags"],
        )
        self.assertIn(
            "social_reported_by_media",
            chain["risk_flag_summary"]["by_category"]["social_or_media"],
        )
        self.assertIn(
            "market_data_snapshot",
            chain["risk_flag_summary"]["by_category"]["market_data"],
        )
        self.assertIn(
            "compiled_research",
            chain["risk_flag_summary"]["by_category"]["compiled_or_negative_search"],
        )

    def test_review_deduplicates_validation_paths_and_counts_independent_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            write_yaml(
                repo / "records" / "sources" / "public" / "independent-review-source.yml",
                {
                    "schema_version": 1,
                    "kind": "source",
                    "id": "source:public:synthetic:independent-review-source",
                    "source_type": "other",
                    "title": "Independent review source",
                    "public_status": "public",
                    "accessed_at": "2026-06-02T00:00:00Z",
                    "content_mode": "small_fixture",
                    "source_perspective": "independent_research",
                    "risk_flags": ["synthetic_fixture"],
                },
            )
            write_yaml(
                repo / "records" / "evidence" / "public" / "independent-review-evidence.yml",
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
                repo / "records" / "validations" / "duplicate-path.yml",
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
                repo / "records" / "validations" / "independent-path.yml",
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
        self.assertEqual(
            review["support_summary"]["source_independence"]["independent_source_count"],
            1,
        )

    def test_review_derives_stale_from_explicit_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            write_yaml(
                repo / "records" / "validations" / "stale-claim.yml",
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

    def test_review_derives_stale_from_open_outdated_challenge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            write_yaml(
                repo / "records" / "challenges" / "outdated-claim.yml",
                {
                    "schema_version": 1,
                    "kind": "challenge",
                    "id": "challenge:test:outdated-claim",
                    "target": "claim:synthetic:exdev-uses-fndwy-for-x1",
                    "submitted_by": "github:tester",
                    "challenge_type": "outdated",
                    "summary": "Synthetic outdated marker.",
                    "depends_on": {
                        "evidence": ["evidence:synthetic:exdev-fy2025-supplier-note"],
                        "claims": ["claim:synthetic:exdev-uses-fndwy-for-x1"],
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
            review["staleness_summary"]["stale_challenge_ids"],
            ["challenge:test:outdated-claim"],
        )

    def test_review_ignores_closed_outdated_challenge_for_staleness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            write_yaml(
                repo / "records" / "challenges" / "addressed-outdated-claim.yml",
                {
                    "schema_version": 1,
                    "kind": "challenge",
                    "id": "challenge:test:addressed-outdated-claim",
                    "target": "claim:synthetic:exdev-uses-fndwy-for-x1",
                    "submitted_by": "github:tester",
                    "challenge_type": "outdated",
                    "summary": "Synthetic addressed outdated marker.",
                    "depends_on": {
                        "evidence": ["evidence:synthetic:exdev-fy2025-supplier-note"],
                        "claims": ["claim:synthetic:exdev-uses-fndwy-for-x1"],
                    },
                    "risk_flags": ["staleness_risk"],
                    "addressed_by": "validation:synthetic:exdev-uses-fndwy-for-x1",
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
        self.assertNotEqual(review["review_state"]["primary_label"], "stale")
        self.assertNotIn("has_staleness_risk", review["review_state"]["flags"])
        self.assertEqual(review["challenge_summary"]["closed_count"], 1)
        self.assertEqual(
            review["challenge_summary"]["closed_challenge_ids"],
            ["challenge:test:addressed-outdated-claim"],
        )
        self.assertEqual(review["staleness_summary"]["stale_challenge_ids"], [])
        self.assertEqual(review["staleness_summary"]["stale_risk_flags"], [])

    def test_review_derives_low_trust_only_for_rumor_supported_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            write_yaml(
                repo / "records" / "sources" / "firsthand" / "review-rumor.yml",
                {
                    "schema_version": 1,
                    "kind": "source",
                    "id": "source:firsthand:review-rumor",
                    "source_type": "anonymous_report",
                    "title": "Review rumor source",
                    "public_status": "unknown",
                    "source_perspective": "anonymous_source",
                    "accessed_at": "2026-06-02T00:00:00Z",
                    "content_mode": "summary",
                    "risk_flags": ["anonymous_source"],
                },
            )
            write_yaml(
                repo / "records" / "evidence" / "firsthand" / "review-rumor.yml",
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
                repo / "records" / "claims" / "review-rumor.yml",
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
                repo / "records" / "theses" / "self-cycle.yml",
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

            evidence_path = repo / "records" / "evidence" / "public" / "synthetic-exdev-fy2025-supplier-note.yml"
            evidence = load_yaml(evidence_path)
            evidence["excerpt"] = "Updated synthetic excerpt for diff-review."
            write_yaml(evidence_path, evidence)
            write_yaml(
                repo / "records" / "challenges" / "diff-review-open-challenge.yml",
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

    def test_diff_review_flags_translation_evidence_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            init_git_repo(repo)

            evidence_path = (
                repo
                / "records"
                / "evidence"
                / "public"
                / "foci"
                / "q1-2026-financial-report.yml"
            )
            evidence = load_yaml(evidence_path)
            evidence["translated_excerpt"] = "Changed translated excerpt for diff-review."
            write_yaml(evidence_path, evidence)

            status, payload = run_json_command(cli.run_diff_review, repo, "HEAD")

        self.assertEqual(status, 0, payload)
        warning = next(
            warning
            for warning in payload["warnings"]
            if warning["code"] == "modifies_canonical_evidence"
        )
        self.assertEqual(warning["record_id"], "evidence:public:foci:q1-2026-financial-report")
        self.assertIn("translated_excerpt", warning["details"]["fields"])

    def test_diff_review_returns_validation_error_exit_for_invalid_current_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))
            init_git_repo(repo)
            write_yaml(
                repo / "records" / "claims" / "diff-review-invalid.yml",
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
                source_perspective="independent_research",
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
        self.assertEqual(source["record"]["source_perspective"], "independent_research")
        self.assertEqual(claim["record"]["evidence"], [{"id": evidence["id"]}])
        self.assertTrue(claim["path"].startswith("records/claims/generated/"))

    def test_new_source_dry_run_validates_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))

            status, source = run_new_json(
                cli.run_new_source,
                repo,
                source_type="other",
                title="Dry Run Helper Source",
                public_status="public",
                source_perspective="independent_research",
                accessed_at="2026-06-03T00:00:00Z",
                content_mode="small_fixture",
                submitted_by="github:tester",
                publisher="Finance OSINT tests",
                url=None,
                archive_url=None,
                published_at=None,
                provenance="Synthetic dry-run helper test.",
                dry_run=True,
            )
            created_path_exists = (repo / source["path"]).exists()

        self.assertEqual(status, 0, source)
        self.assertFalse(source["created"])
        self.assertTrue(source["dry_run"])
        self.assertFalse(created_path_exists)
        self.assertEqual(source["record"]["title"], "Dry Run Helper Source")

    def test_new_source_helper_records_global_filing_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))

            status, source = run_new_json(
                cli.run_new_source,
                repo,
                source_type="exchange_filing",
                title="Helper HKEX Filing",
                public_status="public",
                source_perspective="company_self",
                accessed_at="2026-06-03T00:00:00Z",
                content_mode="external_link",
                submitted_by="github:tester",
                publisher="HKEXnews / Helper Issuer",
                url="https://example.test/helper-hkex-filing.pdf",
                archive_url="https://web.archive.org/example-helper-hkex-filing",
                published_at="2026-05-11",
                provenance="Synthetic global filing helper test.",
                filing_jurisdiction="HK",
                filing_authority="HKEXnews",
                filing_regime="hkex_listed_company_announcement",
                filing_issuer="entity:company:exdev",
                local_form_type="quarterly_financial_information",
                issuer_code="9999",
                issuer_code_scheme="hkex_stock_code",
                report_period="2026-Q1",
                filing_date="2026-05-11",
                source_language="en",
                preservation_path="external:hkexnews/helper-hkex-filing.pdf",
            )
            self.assertEqual(status, 0, source)

            status, payload = run_json_command(cli.run_lint, repo)

        self.assertEqual(status, 0, payload)
        self.assertEqual(payload["warnings"], [])
        self.assertEqual(source["record"]["source_type"], "exchange_filing")
        self.assertEqual(source["record"]["filing_authority"], "HKEXnews")
        self.assertEqual(source["record"]["filing_issuer"], "entity:company:exdev")
        self.assertEqual(source["record"]["issuer_code_scheme"], "hkex_stock_code")
        self.assertEqual(source["record"]["report_period"], "2026-Q1")

    def test_new_evidence_helper_records_translation_and_ocr_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))

            status, evidence = run_new_json(
                cli.run_new_evidence,
                repo,
                evidence_class="public_primary",
                source="source:public:foci:q1-2026-financial-report",
                summary="Helper translated MOPS evidence.",
                content_mode="excerpt",
                observed_at="2026-03-31T00:00:00Z",
                submitted_by="github:tester",
                source_attribution="named_public",
                excerpt="Helper translated revenue row.",
                original_excerpt="營業收入合計 381,969。",
                translated_excerpt="Total operating revenue was NT$381.969M.",
                translation_json=(
                    '{"source_language":"zh-Hant","translated_language":"en",'
                    '"translator":"github:tester","machine_translation":true,'
                    '"translation_date":"2026-06-03",'
                    '"translation_version":"fixture-v1",'
                    '"method":"machine_translation_with_reviewer_check"}'
                ),
                ocr_json='{"used":false}',
                encoding_notes="Decoded from MOPS Big5/inline-XBRL HTML.",
                locator=["section=statement of comprehensive income", "row=revenue"],
                source_access_json=None,
                verification_status="translated_fixture",
            )
            self.assertEqual(status, 0, evidence)

            status, payload = run_json_command(cli.run_lint, repo)

        self.assertEqual(status, 0, payload)
        self.assertEqual(payload["warnings"], [])
        self.assertEqual(evidence["record"]["translation"]["source_language"], "zh-Hant")
        self.assertEqual(evidence["record"]["ocr"], {"used": False})
        self.assertEqual(
            evidence["record"]["encoding_notes"],
            "Decoded from MOPS Big5/inline-XBRL HTML.",
        )

    def test_new_metric_helper_validates_metric_definition_rules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))

            status, payload = run_new_json(
                cli.run_new_metric,
                repo,
                entity="entity:company:exdev",
                metric_definition="metric_definition:revenue",
                value=123.0,
                unit="shares",
                period=["start=2025-01-01", "end=2025-12-31"],
                value_basis="reported",
                evidence=["evidence:synthetic:exdev-fy2025-supplier-note"],
                source_locator=[],
                dimension=[],
                as_of=None,
                reported_at=None,
                published_at=None,
                restated_from=None,
                methodology=None,
                limitations=None,
                submitted_by="github:tester",
                dry_run=True,
            )

        self.assertEqual(status, 1, payload)
        self.assertFalse(payload["ok"])
        self.assertIn("unit `shares` is not allowed by metric definition", payload["errors"][0]["message"])

    def test_new_metric_helper_records_comparability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))

            status, payload = run_new_json(
                cli.run_new_metric,
                repo,
                entity="entity:company:exdev",
                metric_definition="metric_definition:revenue",
                value=100.0,
                unit="USD",
                period=["type=fiscal_year", "fiscal_year=2025", "period_end=2025-12-31"],
                value_basis="reported",
                evidence=["evidence:synthetic:exdev-fy2025-metric-note"],
                source_locator=["section=synthetic metric note"],
                dimension=[],
                comparability=[
                    "reporting_currency=USD",
                    "accounting_standard=US_GAAP",
                    "consolidation_scope=consolidated",
                    "fiscal_year_end=12-31",
                    "fx_methodology=not_applicable",
                ],
                derived_from_metric=[],
                derived_from_evidence=[],
                derived_from_notes=None,
                as_of=None,
                reported_at="2026-06-02",
                published_at="2026-06-02",
                restated_from=None,
                methodology=None,
                limitations=None,
                submitted_by="github:tester",
                dry_run=True,
            )

        self.assertEqual(status, 0, payload)
        self.assertEqual(
            payload["record"]["comparability"],
            {
                "reporting_currency": "USD",
                "accounting_standard": "US_GAAP",
                "consolidation_scope": "consolidated",
                "fiscal_year_end": "12-31",
                "fx_methodology": "not_applicable",
            },
        )

    def test_new_metric_helper_records_derived_from(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = copy_fixture_repo(Path(tmp))

            status, payload = run_new_json(
                cli.run_new_metric,
                repo,
                entity="entity:company:exdev",
                metric_definition="metric_definition:price_to_sales_ratio",
                value=2.0,
                unit="ratio",
                period=["type=point_in_time", "as_of=2026-06-02"],
                value_basis="derived",
                evidence=["evidence:synthetic:exdev-fy2025-metric-note"],
                source_locator=["section=synthetic metric note"],
                dimension=["source_methodology=synthetic_fixture"],
                comparability=[
                    "trading_currency=USD",
                    "accounting_standard=not_applicable",
                    "consolidation_scope=market_observed",
                    "fiscal_year_end=not_applicable",
                    "fx_methodology=not_applicable",
                ],
                derived_from_metric=["metric:synthetic-exdev:fy2025-revenue-restated"],
                derived_from_evidence=["evidence:synthetic:exdev-fy2025-metric-note"],
                derived_from_notes="Derived from synthetic restated revenue.",
                as_of="2026-06-02",
                reported_at=None,
                published_at="2026-06-02",
                restated_from=None,
                methodology="Market cap divided by restated revenue.",
                limitations=None,
                submitted_by="github:tester",
                dry_run=True,
            )

        self.assertEqual(status, 0, payload)
        self.assertEqual(
            payload["record"]["derived_from"],
            {
                "metrics": ["metric:synthetic-exdev:fy2025-revenue-restated"],
                "evidence": ["evidence:synthetic:exdev-fy2025-metric-note"],
                "notes": "Derived from synthetic restated revenue.",
            },
        )

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
                source_perspective="independent_media",
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
        self.assertTrue(payload["path"].startswith("records/relationships/generated/"))

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

            status, question = run_new_json(
                cli.run_new_question,
                repo,
                question="Can helper evidence convert into a named customer order?",
                entity=["entity:company:exdev", entity["id"]],
                proof_type="customer_order_conversion",
                priority="high",
                related_evidence=["evidence:synthetic:exdev-fy2025-supplier-note"],
                related_claim=["claim:synthetic:exdev-uses-fndwy-for-x1"],
                related_relationship=["relationship:synthetic:exdev-fndwy-x1-supply"],
                related_thesis=[thesis["id"]],
                next_action=["Search customer-side disclosures."],
                resolved_by=[],
                submitted_by="github:tester",
            )
            self.assertEqual(status, 0, question)

            status, output = run_lint(repo)

        self.assertEqual(status, 0, output)
        self.assertTrue(entity["path"].startswith("records/entities/service/generated/"))
        self.assertTrue(metric["path"].startswith("records/metrics/generated/"))
        self.assertTrue(event["path"].startswith("records/events/generated/"))
        self.assertTrue(dataset["path"].startswith("records/datasets/generated/"))
        self.assertTrue(thesis["path"].startswith("records/theses/generated/"))
        self.assertTrue(question["path"].startswith("records/questions/generated/"))
        self.assertEqual(thesis["record"]["depends_on"]["metrics"], [metric["id"]])
        self.assertEqual(question["record"]["related_theses"], [thesis["id"]])


if __name__ == "__main__":
    unittest.main()
