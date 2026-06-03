from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from fosint import cli as fosint_cli


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def review_record(record_id: str) -> dict[str, Any]:
    result = run(["uv", "run", "fo", "review", record_id, "--chain", "--json"])
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "fo review failed"
        raise RuntimeError(f"{record_id}: {message}")
    loaded = json.loads(result.stdout)
    if not isinstance(loaded, dict):
        raise RuntimeError(f"{record_id}: fo review did not return a JSON object")
    return loaded


def compact_review(payload: dict[str, Any]) -> dict[str, Any]:
    chain = payload.get("chain_summary", {})
    source_evidence = chain.get("source_evidence_chain", {})
    relationships = chain.get("relationship_chain", {})
    questions = chain.get("question_summary", {})
    challenges = chain.get("challenge_summary", {})
    pressure = chain.get("relationship_promotion_pressure", {})
    risks = chain.get("risk_flag_summary", {})
    return {
        "id": payload.get("id"),
        "review_state": payload.get("review_state"),
        "dependency_counts": chain.get("dependency_counts", {}),
        "evidence_class_counts": source_evidence.get("evidence_class_counts", {}),
        "source_perspective_counts": source_evidence.get("source_perspective_counts", {}),
        "relationship_type_counts": relationships.get("type_counts", {}),
        "open_question_ids": questions.get("open_question_ids", []),
        "open_challenge_ids": challenges.get("open_challenge_ids", []),
        "relationship_promotion_pressure": pressure,
        "risk_flag_categories": risks.get("by_category", {}),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run fo review --chain for changed or impacted current thesis/relationship records."
    )
    parser.add_argument("base", help="Git base commit ref to compare against")
    args = parser.parse_args()

    try:
        root = Path.cwd()
        diff_payload, diff_status = fosint_cli.build_diff_review(root, args.base)
        if diff_status:
            messages = [error["message"] for error in diff_payload.get("errors", [])] or [
                f"diff-review failed for `{args.base}`"
            ]
            raise RuntimeError("; ".join(messages))
        records, load_errors = fosint_cli.load_records(Path.cwd(), include_archive=False)
        if load_errors:
            raise RuntimeError("; ".join(load_errors))
        target_map = fosint_cli.impacted_chain_target_map(
            root,
            records,
            fosint_cli.chain_seed_map_from_payload(diff_payload),
        )
        record_ids = sorted(target_map)
        chain_impact = diff_payload.get("chain_impact", {})
        payload = {
            "command": "chain-review-changed",
            "base": args.base,
            "base_sha": diff_payload.get("base_sha"),
            "chain_impact": chain_impact,
            "changed_seed_ids": chain_impact.get("seed_ids", []),
            "expanded_seed_ids": chain_impact.get("expanded_seed_ids", []),
            "reviewed_ids": record_ids,
            "reviewed_targets": [
                {"id": record_id, "seed_ids": target_map[record_id]} for record_id in record_ids
            ],
            "reviewed_count": len(record_ids),
            "reviews": [compact_review(review_record(record_id)) for record_id in record_ids],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
