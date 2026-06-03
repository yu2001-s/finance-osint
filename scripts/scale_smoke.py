from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from fosint import cli


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = Path(".local/scale-smoke-10k.json")


QUERY_PLAN_CHECKS = [
    {
        "name": "refs_by_source",
        "sql": "select target_id from refs where source_id = ?",
        "params": ("claim:scale:00001",),
        "expected_index": "refs_source_idx",
    },
    {
        "name": "refs_by_target",
        "sql": "select source_id from refs where target_id = ?",
        "params": ("evidence:scale:00001",),
        "expected_index": "refs_target_idx",
    },
    {
        "name": "edges_by_source",
        "sql": "select target_id from edges where source_id = ?",
        "params": ("claim:scale:00001",),
        "expected_index": "edges_source_idx",
    },
    {
        "name": "edges_by_target",
        "sql": "select source_id from edges where target_id = ?",
        "params": ("evidence:scale:00001",),
        "expected_index": "edges_target_idx",
    },
    {
        "name": "identifier_lookup",
        "sql": "select record_id from identifiers where id_type = ? and id_value = ?",
        "params": ("ticker", "SCALE"),
        "expected_index": "identifiers_type_value_idx",
    },
    {
        "name": "evidence_by_source",
        "sql": "select id from evidence where source_id = ?",
        "params": ("source:public:scale-smoke",),
        "expected_index": "evidence_source_idx",
    },
    {
        "name": "claims_by_subject",
        "sql": "select id from claims where subject = ?",
        "params": ("entity:company:scale-co",),
        "expected_index": "claims_subject_idx",
    },
    {
        "name": "claims_by_predicate",
        "sql": "select id from claims where predicate = ?",
        "params": ("product_signal",),
        "expected_index": "claims_predicate_idx",
    },
    {
        "name": "review_validations_by_target",
        "sql": "select id from validations where target_id = ?",
        "params": ("claim:scale:00001",),
        "expected_index": "validations_target_idx",
    },
    {
        "name": "review_challenges_by_target",
        "sql": "select id from challenges where target_id = ?",
        "params": ("claim:scale:00001",),
        "expected_index": "challenges_target_idx",
    },
    {
        "name": "relationship_participants_by_entity",
        "sql": "select relationship_id from relationship_participants where entity_id = ?",
        "params": ("entity:company:scale-co",),
        "expected_index": "relationship_participants_entity_idx",
    },
    {
        "name": "metrics_by_entity",
        "sql": "select id from metrics where entity_id = ?",
        "params": ("entity:company:scale-co",),
        "expected_index": "metrics_entity_idx",
    },
]


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False)


def copy_static_dirs(repo: Path) -> None:
    for dirname in ("schemas", "ontology"):
        shutil.copytree(PROJECT_ROOT / dirname, repo / dirname)


def generate_scale_records(repo: Path, record_count: int) -> dict[str, Any]:
    if record_count < 4:
        raise ValueError("record_count must be at least 4")

    pair_count = (record_count - 2) // 2
    extra_entities = record_count - 2 - (pair_count * 2)
    width = max(5, len(str(pair_count)))

    write_yaml(
        repo / "records" / "entities" / "scale" / "scale-co.yml",
        {
            "schema_version": 1,
            "kind": "entity",
            "id": "entity:company:scale-co",
            "entity_type": "company",
            "name": "Scale Smoke Company",
            "identifiers": {"ticker": "SCALE"},
            "submitted_by": "github:scale-smoke",
        },
    )
    if extra_entities:
        write_yaml(
            repo / "records" / "entities" / "scale" / "scale-extra.yml",
            {
                "schema_version": 1,
                "kind": "entity",
                "id": "entity:company:scale-extra",
                "entity_type": "company",
                "name": "Scale Smoke Extra Company",
                "submitted_by": "github:scale-smoke",
            },
        )

    write_yaml(
        repo / "records" / "sources" / "public" / "scale-smoke.yml",
        {
            "schema_version": 1,
            "kind": "source",
            "id": "source:public:scale-smoke",
            "source_type": "other",
            "title": "Scale smoke deterministic source",
            "public_status": "public",
            "source_perspective": "synthetic_fixture",
            "accessed_at": "2026-06-03T00:00:00Z",
            "content_mode": "small_fixture",
            "submitted_by": "github:scale-smoke",
            "risk_flags": ["synthetic_fixture"],
        },
    )

    for number in range(1, pair_count + 1):
        slug = f"{number:0{width}d}"
        evidence_id = f"evidence:scale:{slug}"
        write_yaml(
            repo / "records" / "evidence" / "public" / "scale" / f"{slug}.yml",
            {
                "schema_version": 1,
                "kind": "evidence",
                "id": evidence_id,
                "evidence_class": "public_secondary",
                "source": "source:public:scale-smoke",
                "summary": f"Scale smoke evidence {slug} observes a deterministic product signal.",
                "content_mode": "small_fixture",
                "observed_at": "2026-06-03T00:00:00Z",
                "submitted_by": "github:scale-smoke",
                "source_attribution": "named_public",
                "risk_flags": ["synthetic_fixture"],
            },
        )
        write_yaml(
            repo / "records" / "claims" / "scale" / f"{slug}.yml",
            {
                "schema_version": 1,
                "kind": "claim",
                "id": f"claim:scale:{slug}",
                "statement": f"Scale smoke claim {slug} has a deterministic product signal.",
                "subject": "entity:company:scale-co",
                "predicate": "product_signal",
                "object": f"scale product signal {slug}",
                "support_type": "observed",
                "evidence": [{"id": evidence_id}],
                "submitted_by": "github:scale-smoke",
                "risk_flags": ["synthetic_fixture"],
            },
        )

    return {
        "generated_records": 2 + extra_entities + (pair_count * 2),
        "generated_claims": pair_count,
        "generated_evidence": pair_count,
    }


def explain_query_plan(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...]) -> list[str]:
    rows = conn.execute(f"explain query plan {sql}", params).fetchall()
    return [str(row[3]) for row in rows]


def query_plan_report(db_path: Path) -> list[dict[str, Any]]:
    with sqlite3.connect(db_path) as conn:
        plans = []
        for check in QUERY_PLAN_CHECKS:
            details = explain_query_plan(conn, check["sql"], check["params"])
            joined = " | ".join(details)
            expected_index = str(check["expected_index"])
            plans.append(
                {
                    "name": check["name"],
                    "expected_index": expected_index,
                    "uses_index": expected_index in joined,
                    "plan": details,
                }
            )
        return plans


def run_in_repo(repo: Path, record_count: int) -> dict[str, Any]:
    copy_static_dirs(repo)
    generated = generate_scale_records(repo, record_count)

    timings: dict[str, int] = {}

    started = time.perf_counter()
    records, errors = cli.validate_repo(repo, current_only=True)
    timings["validate_repo_ms"] = int(round((time.perf_counter() - started) * 1000))

    started = time.perf_counter()
    graph = cli.build_graph_data(repo, records)
    timings["build_graph_ms"] = int(round((time.perf_counter() - started) * 1000))

    index_result: dict[str, Any] = {}
    if not errors:
        started = time.perf_counter()
        index_result = cli.create_index_database(repo, records)
        timings["create_index_ms"] = int(round((time.perf_counter() - started) * 1000))
    else:
        timings["create_index_ms"] = 0

    plans = query_plan_report(Path(index_result["index_path"])) if index_result else []
    failed_plans = [plan["name"] for plan in plans if not plan["uses_index"]]
    violations = [*errors, *[f"query plan `{name}` did not use expected index" for name in failed_plans]]

    return {
        "schema_version": 1,
        "ok": not violations,
        "command": "scale-smoke",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "scenario": f"{record_count // 1000}k" if record_count % 1000 == 0 else str(record_count),
        "requested_records": record_count,
        **generated,
        "records_loaded_including_ontology": len(records),
        "timings_ms": timings,
        "graph": {"node_count": graph["node_count"], "edge_count": graph["edge_count"]},
        "index": {
            "records_indexed": index_result.get("records_indexed"),
            "ref_count": index_result.get("ref_count"),
            "edge_count": index_result.get("edge_count"),
        },
        "query_plans": plans,
        "violations": violations,
    }


def run_scale_smoke(record_count: int = 10000, keep_repo: Path | None = None) -> dict[str, Any]:
    if keep_repo is not None:
        keep_repo.mkdir(parents=True, exist_ok=True)
        return run_in_repo(keep_repo, record_count)
    with tempfile.TemporaryDirectory(prefix="finance-osint-scale-") as tmp:
        return run_in_repo(Path(tmp) / "repo", record_count)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a deterministic generated scale smoke test.")
    parser.add_argument("--records", type=int, default=10000, help="Number of generated records")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Path for the JSON report")
    parser.add_argument("--json", action="store_true", help="Print the JSON report to stdout")
    parser.add_argument(
        "--keep-repo",
        default=None,
        help="Optional path where the generated repository should be kept for inspection.",
    )
    args = parser.parse_args()

    payload = run_scale_smoke(args.records, Path(args.keep_repo) if args.keep_repo else None)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        status = "OK" if payload["ok"] else "FAIL"
        print(
            f"{status} scale smoke {payload['scenario']}: "
            f"{payload['generated_records']} generated records, "
            f"{payload['graph']['edge_count']} graph edges"
        )

    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
