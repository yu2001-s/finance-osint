from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


REVIEW_PATH_PREFIXES = ("relationships/", "theses/")


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def git_changed_paths(base_ref: str) -> list[tuple[str, str]]:
    result = run(["git", "diff", "--name-status", base_ref, "--"])
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git diff failed"
        raise RuntimeError(message)

    paths: list[tuple[str, str]] = []
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if not parts:
            continue
        status = parts[0]
        if status.startswith("R") and len(parts) >= 3:
            paths.append(("R", parts[2]))
        elif len(parts) >= 2:
            paths.append((status[:1], parts[1]))
    untracked = run(["git", "ls-files", "--others", "--exclude-standard"])
    if untracked.returncode != 0:
        message = untracked.stderr.strip() or untracked.stdout.strip() or "git ls-files failed"
        raise RuntimeError(message)
    tracked_paths = {path for _, path in paths}
    for path_text in sorted(path for path in untracked.stdout.splitlines() if path):
        if path_text not in tracked_paths:
            paths.append(("A", path_text))
    return paths


def current_review_paths(base_ref: str) -> list[Path]:
    paths: list[Path] = []
    for status, path_text in git_changed_paths(base_ref):
        if status == "D":
            continue
        if not path_text.endswith((".yml", ".yaml")):
            continue
        if not path_text.startswith(REVIEW_PATH_PREFIXES):
            continue
        path = Path(path_text)
        if path.exists():
            paths.append(path)
    return sorted(set(paths), key=lambda path: str(path))


def record_id_for_path(path: Path) -> str | None:
    with path.open("r", encoding="utf-8") as handle:
        loaded: Any = yaml.safe_load(handle)
    if not isinstance(loaded, dict):
        return None
    record_id = loaded.get("id")
    kind = loaded.get("kind")
    if not isinstance(record_id, str) or kind not in {"relationship", "thesis"}:
        return None
    return record_id


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
        description="Run fo review --chain for changed current thesis/relationship records."
    )
    parser.add_argument("base", help="Git base ref to compare against")
    args = parser.parse_args()

    try:
        record_ids = sorted(
            {
                record_id
                for path in current_review_paths(args.base)
                if (record_id := record_id_for_path(path))
            }
        )
        payload = {
            "command": "chain-review-changed",
            "base": args.base,
            "reviewed_ids": record_ids,
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
