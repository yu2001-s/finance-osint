from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_BUDGETS_SECONDS = {
    "lint": 15.0,
    "unit_tests": 180.0,
    "index_build": 30.0,
    "changed_chain_review": 60.0,
    "graph_build": 30.0,
    "diff_review": 60.0,
}
DEFAULT_BUDGET_FILE = Path(".github/ci/timing-budgets.json")


def command_specs(base_ref: str) -> list[tuple[str, list[str]]]:
    return [
        ("lint", ["uv", "run", "fo", "lint", "--json"]),
        ("unit_tests", ["uv", "run", "python", "-m", "unittest", "discover", "-s", "tests"]),
        ("index_build", ["uv", "run", "fo", "index", "build", "--json"]),
        (
            "changed_chain_review",
            ["uv", "run", "python", "scripts/chain_review_changed.py", base_ref],
        ),
        ("graph_build", ["uv", "run", "fo", "graph", "build", "--json"]),
        ("diff_review", ["uv", "run", "fo", "diff-review", base_ref, "--json"]),
    ]


def directory_size(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            total += item.stat().st_size
    return total


def git_output(args: list[str]) -> str | None:
    result = subprocess.run(["git", *args], check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def git_count_objects() -> dict[str, str]:
    output = git_output(["count-objects", "-v"])
    if not output:
        return {}
    values: dict[str, str] = {}
    for line in output.splitlines():
        if ": " in line:
            key, value = line.split(": ", 1)
            values[key] = value
    return values


def git_commit_sha(ref: str) -> str | None:
    return git_output(["rev-parse", "--verify", f"{ref}^{{commit}}"])


def load_budget_spec(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "schema_version": 1,
            "budget_mode": "warning",
            "steps": {
                name: {"budget_ms": int(seconds * 1000), "class": "full_corpus"}
                for name, seconds in DEFAULT_BUDGETS_SECONDS.items()
            },
        }
    with path.open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    if not isinstance(loaded, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return loaded


def step_budget(spec: dict[str, Any], name: str) -> dict[str, Any]:
    steps = spec.get("steps", {})
    configured = steps.get(name, {}) if isinstance(steps, dict) else {}
    if not isinstance(configured, dict):
        configured = {}
    default_budget_ms = int(DEFAULT_BUDGETS_SECONDS[name] * 1000)
    return {
        "budget_ms": int(configured.get("budget_ms", default_budget_ms)),
        "class": str(configured.get("class", "full_corpus")),
    }


def parse_json_object(text: str) -> dict[str, Any] | None:
    try:
        loaded = json.loads(text)
    except json.JSONDecodeError:
        return None
    return loaded if isinstance(loaded, dict) else None


def output_summary(name: str, stdout: str) -> dict[str, Any]:
    loaded = parse_json_object(stdout)
    if not loaded:
        return {}
    summary: dict[str, Any] = {}
    for key in (
        "records_checked",
        "records_indexed",
        "node_count",
        "edge_count",
        "ref_count",
        "reviewed_count",
    ):
        if key in loaded:
            summary[key] = loaded[key]
    if name == "diff_review":
        total = loaded.get("record_delta", {}).get("total", {})
        if isinstance(total, dict):
            summary["record_delta"] = total
        graph = loaded.get("graph_impact", {})
        if isinstance(graph, dict):
            for key in ("after_node_count", "after_edge_count", "added_edge_count", "removed_edge_count"):
                if key in graph:
                    summary[key] = graph[key]
    warnings = loaded.get("warnings")
    errors = loaded.get("errors")
    if isinstance(warnings, list):
        summary["warning_count"] = len(warnings)
    if isinstance(errors, list):
        summary["error_count"] = len(errors)
    return summary


def run_timed(name: str, command: list[str], budget: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    result = subprocess.run(command, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    elapsed_ms = int(round((time.perf_counter() - started) * 1000))
    budget_ms = int(budget["budget_ms"])
    over_budget = elapsed_ms > budget_ms
    item: dict[str, Any] = {
        "name": name,
        "command": " ".join(command),
        "class": budget["class"],
        "exit_code": result.returncode,
        "elapsed_ms": elapsed_ms,
        "budget_ms": budget_ms,
        "over_budget": over_budget,
        "ok": result.returncode == 0,
        "output_summary": output_summary(name, result.stdout),
    }
    if result.returncode != 0:
        item["stdout_tail"] = result.stdout[-4000:]
        item["stderr_tail"] = result.stderr[-4000:]
    return item


def corpus_summary(root: Path, steps: list[dict[str, Any]]) -> dict[str, Any]:
    lint = next((step for step in steps if step["name"] == "lint"), {})
    graph = next((step for step in steps if step["name"] == "graph_build"), {})
    records = lint.get("output_summary", {}).get("records_checked")
    return {
        "records": records,
        "graph_nodes": graph.get("output_summary", {}).get("node_count"),
        "graph_edges": graph.get("output_summary", {}).get("edge_count"),
        "source_artifact_bytes": directory_size(root / "artifacts"),
        "local_bytes": directory_size(root / ".local"),
        "git_count_objects": git_count_objects(),
    }


def build_payload(root: Path, base_ref: str, budget_path: Path) -> dict[str, Any]:
    budget_spec = load_budget_spec(budget_path)
    base_sha = git_commit_sha(base_ref)
    resolved_base_ref = base_sha or base_ref
    steps = [
        run_timed(name, command, step_budget(budget_spec, name))
        for name, command in command_specs(resolved_base_ref)
    ]
    return {
        "schema_version": 1,
        "ok": all(step["ok"] for step in steps),
        "command": "validate-with-timing",
        "base": base_ref,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "budget_file": str(budget_path),
        "budget_mode": str(budget_spec.get("budget_mode", "warning")),
        "git": {
            "sha": git_output(["rev-parse", "HEAD"]),
            "base_ref": base_ref,
            "base_sha": base_sha,
            "event": os.environ.get("GITHUB_EVENT_NAME", "local"),
        },
        "environment": {
            "os": platform.platform(),
            "python": platform.python_version(),
            "uv_lock": (root / "uv.lock").exists(),
        },
        "corpus": corpus_summary(root, steps),
        "steps": steps,
        "summary": {
            "total_elapsed_ms": sum(step["elapsed_ms"] for step in steps),
            "failed_steps": [step["name"] for step in steps if not step["ok"]],
            "over_budget_steps": [step["name"] for step in steps if step["over_budget"]],
        },
    }


def print_human(payload: dict[str, Any]) -> None:
    print(f"Validation timing vs {payload['base']}")
    for step in payload["steps"]:
        status = "OK" if step["ok"] else f"FAIL({step['exit_code']})"
        budget = "over budget" if step["over_budget"] else "within budget"
        print(
            f"{step['name']}: {status}, {step['elapsed_ms']}ms / "
            f"{step['budget_ms']}ms ({budget})"
        )


def markdown_summary(payload: dict[str, Any]) -> str:
    lines = [
        "### Validation Timing",
        "",
        f"Base ref: `{payload['base']}`",
        f"Base SHA: `{payload['git'].get('base_sha') or 'unresolved'}`",
        "",
        "| Step | Status | Elapsed | Budget |",
        "| --- | ---: | ---: | ---: |",
    ]
    for step in payload["steps"]:
        status = "OK" if step["ok"] else f"FAIL {step['exit_code']}"
        lines.append(
            f"| `{step['name']}` | {status} | {step['elapsed_ms']} ms | {step['budget_ms']} ms |"
        )
    lines.append("")
    lines.append(f"Total: {payload['summary']['total_elapsed_ms']} ms")
    if payload["summary"]["over_budget_steps"]:
        lines.append("Over advisory budget: " + ", ".join(payload["summary"]["over_budget_steps"]))
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the repository validation checklist and record per-command timings."
    )
    parser.add_argument(
        "base",
        nargs="?",
        default="HEAD",
        help="Git base commit ref for changed chain review and diff review",
    )
    parser.add_argument(
        "--output",
        default=".local/validation-timings.json",
        help="Path for the timing JSON artifact.",
    )
    parser.add_argument(
        "--budget-file",
        default=str(DEFAULT_BUDGET_FILE),
        help="JSON budget spec to use.",
    )
    parser.add_argument(
        "--markdown-summary",
        default=None,
        help="Optional path for a GitHub step-summary markdown table.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON summary to stdout")
    parser.add_argument(
        "--enforce-budgets",
        action="store_true",
        help="Exit non-zero when a command exceeds its advisory budget.",
    )
    args = parser.parse_args()

    root = Path.cwd()
    payload = build_payload(root, str(args.base), Path(args.budget_file))
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.markdown_summary:
        markdown_path = Path(args.markdown_summary)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(markdown_summary(payload), encoding="utf-8")

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_human(payload)

    failed = bool(payload["summary"]["failed_steps"])
    over_budget = bool(payload["summary"]["over_budget_steps"])
    if failed or (args.enforce_budgets and over_budget):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
