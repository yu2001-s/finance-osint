from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
    from jsonschema import Draft202012Validator
except ImportError as exc:  # pragma: no cover
    print(f"Missing dependency: {exc.name}. Run `pip install -e .` first.", file=sys.stderr)
    raise SystemExit(2) from exc


SCHEMA_BY_KIND = {
    "entity": "entity.schema.json",
    "source": "source.schema.json",
    "evidence": "evidence.schema.json",
    "claim": "claim.schema.json",
    "validation": "validation.schema.json",
    "challenge": "challenge.schema.json",
    "relationship_type": "relationship-type.schema.json",
    "relationship": "relationship.schema.json",
    "thesis": "thesis.schema.json",
    "debate": "debate.schema.json",
    "argument": "argument.schema.json",
    "resolution": "resolution.schema.json",
}

REF_PREFIXES = (
    "entity:",
    "source:",
    "evidence:",
    "claim:",
    "validation:",
    "challenge:",
    "rel:",
    "thesis:",
    "debate:",
    "arg:",
    "resolution:",
)

SKIP_PARTS = {".git", ".local", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache"}
DATA_DIRS = (
    "relationship-types",
    "entities",
    "sources",
    "evidence",
    "claims",
    "validations",
    "challenges",
    "relationships",
    "theses",
    "debates",
)

FIRST_HAND_EVIDENCE_CLASSES = {
    "E2_firsthand_public",
    "E3_firsthand_private",
    "E4_anonymous_internal",
    "E5_unverified_rumor",
}
LOW_TRUST_EVIDENCE_CLASSES = {"E4_anonymous_internal", "E5_unverified_rumor"}
CANONICAL_CLAIM_STATUSES = {"corroborated", "falsified"}
CANONICAL_RELATIONSHIP_STATUSES = {"supported", "corroborated", "falsified"}
CANONICAL_VALIDATION_VERDICTS = {"corroborates", "falsifies"}


@dataclass(frozen=True)
class Record:
    path: Path
    data: dict[str, Any]

    @property
    def id(self) -> str:
        return str(self.data.get("id", ""))

    @property
    def kind(self) -> str:
        return str(self.data.get("kind", ""))


def repo_root() -> Path:
    current = Path.cwd()
    for path in [current, *current.parents]:
        if (path / "pyproject.toml").exists() and (path / "schemas").exists():
            return path
    return current


def iter_yaml_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for dirname in DATA_DIRS:
        directory = root / dirname
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if any(part in SKIP_PARTS for part in path.parts):
                continue
            if path.is_file() and path.suffix in {".yml", ".yaml"}:
                files.append(path)
    return sorted(files)


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ValueError("YAML document must be an object")
    return loaded


def load_records(root: Path) -> tuple[list[Record], list[str]]:
    records: list[Record] = []
    errors: list[str] = []
    for path in iter_yaml_files(root):
        try:
            records.append(Record(path=path, data=load_yaml(path)))
        except Exception as exc:
            errors.append(f"{path.relative_to(root)}: failed to load YAML: {exc}")
    return records, errors


def load_schemas(root: Path) -> dict[str, Draft202012Validator]:
    validators: dict[str, Draft202012Validator] = {}
    for kind, filename in SCHEMA_BY_KIND.items():
        with (root / "schemas" / filename).open("r", encoding="utf-8") as handle:
            schema = json.load(handle)
        validators[kind] = Draft202012Validator(schema)
    return validators


def format_error_path(error: Any) -> str:
    if not error.path:
        return "$"
    return "$." + ".".join(str(part) for part in error.path)


def validate_schemas(
    root: Path, records: list[Record], validators: dict[str, Draft202012Validator]
) -> list[str]:
    errors: list[str] = []
    for record in records:
        relative = record.path.relative_to(root)
        kind = record.data.get("kind")
        if kind not in validators:
            errors.append(f"{relative}: unknown or missing kind `{kind}`")
            continue
        for error in sorted(validators[kind].iter_errors(record.data), key=lambda item: item.path):
            errors.append(f"{relative}: {format_error_path(error)}: {error.message}")
    return errors


def build_id_map(root: Path, records: list[Record]) -> tuple[dict[str, Record], list[str]]:
    id_map: dict[str, Record] = {}
    errors: list[str] = []
    for record in records:
        record_id = record.id
        if not record_id:
            continue
        if record_id in id_map:
            errors.append(
                f"{record.path.relative_to(root)}: duplicate id `{record_id}` already used by "
                f"{id_map[record_id].path.relative_to(root)}"
            )
            continue
        id_map[record_id] = record
    return id_map, errors


def walk_strings(value: Any, path: tuple[str, ...] = ()) -> list[tuple[tuple[str, ...], str]]:
    found: list[tuple[tuple[str, ...], str]] = []
    if isinstance(value, str):
        found.append((path, value))
    elif isinstance(value, dict):
        for key, child in value.items():
            found.extend(walk_strings(child, (*path, str(key))))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(walk_strings(child, (*path, str(index))))
    return found


def is_reference(value: str) -> bool:
    return value.startswith(REF_PREFIXES)


def validate_references(root: Path, records: list[Record], id_map: dict[str, Record]) -> list[str]:
    errors: list[str] = []
    for record in records:
        for path, value in walk_strings(record.data):
            if path and path[-1] == "id":
                continue
            if not is_reference(value):
                continue
            if value not in id_map:
                dotted = ".".join(path) or "$"
                errors.append(
                    f"{record.path.relative_to(root)}: {dotted} references missing id `{value}`"
                )
    return errors


def registered_relationship_types(records: list[Record]) -> dict[str, Record]:
    return {
        record.id: record
        for record in records
        if record.kind == "relationship_type" and record.data.get("status") == "registered"
    }


def proposed_relationship_types(records: list[Record]) -> dict[str, Record]:
    return {
        record.id: record
        for record in records
        if record.kind == "relationship_type" and record.data.get("status") == "proposed"
    }


def entity_type_for(record_id: str, id_map: dict[str, Record]) -> str | None:
    record = id_map.get(record_id)
    if not record or record.kind != "entity":
        return None
    return str(record.data.get("entity_type"))


def as_string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def evidence_class_for(record_id: str, id_map: dict[str, Record]) -> str | None:
    record = id_map.get(record_id)
    if not record or record.kind != "evidence":
        return None
    return str(record.data.get("evidence_class"))


def evidence_ids_for_claim(record: Record) -> list[str]:
    return as_string_list(record.data.get("evidence"))


def evidence_ids_for_relationship(record: Record, id_map: dict[str, Record]) -> list[str]:
    derived_from = record.data.get("derived_from", {})
    if not isinstance(derived_from, dict):
        return []

    evidence_ids = as_string_list(derived_from.get("evidence"))
    for claim_id in as_string_list(derived_from.get("claims")):
        claim = id_map.get(claim_id)
        if claim and claim.kind == "claim":
            evidence_ids.extend(evidence_ids_for_claim(claim))
    return sorted(set(evidence_ids))


def evidence_ids_for_validation(record: Record, id_map: dict[str, Record]) -> list[str]:
    depends_on = record.data.get("depends_on", {})
    if not isinstance(depends_on, dict):
        return []

    evidence_ids = as_string_list(depends_on.get("evidence"))
    for claim_id in as_string_list(depends_on.get("claims")):
        claim = id_map.get(claim_id)
        if claim and claim.kind == "claim":
            evidence_ids.extend(evidence_ids_for_claim(claim))
    for relationship_id in as_string_list(depends_on.get("relationships")):
        relationship = id_map.get(relationship_id)
        if relationship and relationship.kind == "relationship":
            evidence_ids.extend(evidence_ids_for_relationship(relationship, id_map))
    return sorted(set(evidence_ids))


def evidence_support_classes(evidence_ids: list[str], id_map: dict[str, Record]) -> set[str]:
    return {
        evidence_class
        for evidence_id in evidence_ids
        if (evidence_class := evidence_class_for(evidence_id, id_map))
    }


def has_non_low_trust_support(evidence_ids: list[str], id_map: dict[str, Record]) -> bool:
    classes = evidence_support_classes(evidence_ids, id_map)
    return any(evidence_class not in LOW_TRUST_EVIDENCE_CLASSES for evidence_class in classes)


def normalize_qualifiers(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    if isinstance(value, dict):
        return [str(key) for key, enabled in value.items() if enabled]
    return []


def validate_relationships(
    root: Path, records: list[Record], id_map: dict[str, Record]
) -> list[str]:
    errors: list[str] = []
    registered = registered_relationship_types(records)
    proposed = proposed_relationship_types(records)

    for record in records:
        if record.kind != "relationship":
            continue

        relative = record.path.relative_to(root)
        rel_type = str(record.data.get("type", ""))
        type_def: Record | None = None

        if rel_type.startswith("provisional:"):
            proposed_id = rel_type.split(":", 1)[1]
            proposed_path = record.data.get("proposed_type_definition")
            if not proposed_path:
                errors.append(f"{relative}: provisional type `{rel_type}` needs proposed_type_definition")
            else:
                definition_path = root / str(proposed_path)
                if not definition_path.exists():
                    errors.append(
                        f"{relative}: proposed_type_definition `{proposed_path}` does not exist"
                    )
            if proposed_id not in proposed:
                errors.append(
                    f"{relative}: provisional type `{rel_type}` has no proposed relationship_type record"
                )
            else:
                type_def = proposed[proposed_id]
        else:
            if rel_type not in registered:
                errors.append(f"{relative}: relationship type `{rel_type}` is not registered")
            else:
                type_def = registered[rel_type]

        if type_def is None:
            continue

        roles = type_def.data.get("roles", {})
        participants = record.data.get("participants", {})
        for role, participant_id in participants.items():
            if role not in roles:
                errors.append(
                    f"{relative}: participant role `{role}` is not allowed by type `{rel_type}`"
                )
                continue
            if not isinstance(participant_id, str) or not participant_id.startswith("entity:"):
                errors.append(
                    f"{relative}: participant `{role}` must reference an entity id, got "
                    f"`{participant_id}`"
                )
                continue
            actual_entity_type = entity_type_for(participant_id, id_map)
            allowed_entity_types = roles[role].get("entity_types", [])
            if actual_entity_type and actual_entity_type not in allowed_entity_types:
                errors.append(
                    f"{relative}: `{participant_id}` has entity_type `{actual_entity_type}`, "
                    f"but role `{role}` expects one of {allowed_entity_types}"
                )

        allowed_scope = set(type_def.data.get("allowed_scope", []))
        scope = record.data.get("scope", {})
        if allowed_scope and isinstance(scope, dict):
            for key in scope:
                if key not in allowed_scope:
                    errors.append(
                        f"{relative}: scope `{key}` is not allowed by "
                        f"relationship type `{rel_type}`"
                    )

        allowed_qualifiers = set(type_def.data.get("allowed_qualifiers", []))
        if allowed_qualifiers:
            for qualifier in normalize_qualifiers(record.data.get("qualifiers")):
                if qualifier not in allowed_qualifiers:
                    errors.append(
                        f"{relative}: qualifier `{qualifier}` is not allowed by "
                        f"relationship type `{rel_type}`"
                    )

        allowed_materiality = type_def.data.get("materiality", {}).get("allowed_values", [])
        materiality_level = record.data.get("materiality", {}).get("level")
        if allowed_materiality and materiality_level and materiality_level not in allowed_materiality:
            errors.append(
                f"{relative}: materiality level `{materiality_level}` is not allowed by "
                f"relationship type `{rel_type}`"
            )

        if type_def.data.get("evidence_required"):
            derived_from = record.data.get("derived_from", {})
            has_claims = bool(derived_from.get("claims"))
            has_evidence = bool(derived_from.get("evidence"))
            if not has_claims and not has_evidence:
                errors.append(f"{relative}: relationship type `{rel_type}` requires evidence or claims")

    return errors


def validate_evidence_policy(
    root: Path, records: list[Record], id_map: dict[str, Record]
) -> list[str]:
    errors: list[str] = []

    for record in records:
        relative = record.path.relative_to(root)

        if record.kind == "evidence":
            evidence_class = str(record.data.get("evidence_class", ""))
            if evidence_class in FIRST_HAND_EVIDENCE_CLASSES:
                if "attribution" not in record.data:
                    errors.append(f"{relative}: first-hand evidence must declare attribution")
                if not isinstance(record.data.get("source_access"), dict):
                    errors.append(f"{relative}: first-hand evidence must declare source_access")
                if "risk_flags" not in record.data:
                    errors.append(f"{relative}: first-hand evidence must declare risk_flags")
            if evidence_class in LOW_TRUST_EVIDENCE_CLASSES and not record.data.get("risk_flags"):
                errors.append(f"{relative}: low-trust evidence must include at least one risk_flag")

        if record.kind == "claim":
            status = str(record.data.get("status", ""))
            confidence = str(record.data.get("confidence", ""))
            evidence_ids = evidence_ids_for_claim(record)
            if (status in CANONICAL_CLAIM_STATUSES or confidence == "high") and not (
                has_non_low_trust_support(evidence_ids, id_map)
            ):
                errors.append(
                    f"{relative}: `{status}` claim with `{confidence}` confidence needs at least "
                    "one non-low-trust evidence record"
                )

        if record.kind == "relationship":
            status = str(record.data.get("status", ""))
            confidence = str(record.data.get("confidence", ""))
            evidence_ids = evidence_ids_for_relationship(record, id_map)
            if (status in CANONICAL_RELATIONSHIP_STATUSES or confidence == "high") and not (
                has_non_low_trust_support(evidence_ids, id_map)
            ):
                errors.append(
                    f"{relative}: `{status}` relationship with `{confidence}` confidence needs at "
                    "least one non-low-trust evidence record through derived_from"
                )

        if record.kind == "validation":
            verdict = str(record.data.get("verdict", ""))
            confidence = str(record.data.get("confidence", ""))
            evidence_ids = evidence_ids_for_validation(record, id_map)
            if (verdict in CANONICAL_VALIDATION_VERDICTS or confidence == "high") and not (
                has_non_low_trust_support(evidence_ids, id_map)
            ):
                errors.append(
                    f"{relative}: `{verdict}` validation with `{confidence}` confidence needs at "
                    "least one non-low-trust evidence record"
                )

    return errors


def record_label(record: Record) -> str:
    for key in ("name", "title", "statement", "summary", "label"):
        value = record.data.get(key)
        if isinstance(value, str) and value:
            return value
    return record.id


def build_graph_data(root: Path, records: list[Record]) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    for record in records:
        if not record.id:
            continue
        nodes.append(
            {
                "id": record.id,
                "kind": record.kind,
                "label": record_label(record),
                "path": str(record.path.relative_to(root)),
            }
        )

        if record.kind == "relationship":
            for role, participant_id in record.data.get("participants", {}).items():
                if isinstance(participant_id, str) and is_reference(participant_id):
                    edges.append(
                        {
                            "from": participant_id,
                            "to": record.id,
                            "type": f"participant:{role}",
                        }
                    )

        if record.kind == "claim":
            subject = record.data.get("subject")
            obj = record.data.get("object")
            predicate = record.data.get("predicate", "claims")
            if isinstance(subject, str) and is_reference(subject):
                edges.append({"from": subject, "to": record.id, "type": "subject"})
            if isinstance(obj, str) and is_reference(obj):
                edges.append({"from": record.id, "to": obj, "type": str(predicate)})

        for path, value in walk_strings(record.data):
            if path and path[-1] == "id":
                continue
            if is_reference(value):
                edges.append(
                    {
                        "from": record.id,
                        "to": value,
                        "type": "references",
                        "field": ".".join(path),
                    }
                )

    unique_edges = []
    seen_edges: set[tuple[str, str, str, str]] = set()
    for edge in edges:
        key = (
            str(edge.get("from")),
            str(edge.get("to")),
            str(edge.get("type")),
            str(edge.get("field", "")),
        )
        if key in seen_edges:
            continue
        seen_edges.add(key)
        unique_edges.append(edge)

    return {
        "schema_version": "0.1",
        "node_count": len(nodes),
        "edge_count": len(unique_edges),
        "nodes": nodes,
        "edges": unique_edges,
    }


def run_lint(root: Path) -> int:
    validators = load_schemas(root)
    records, load_errors = load_records(root)
    id_map, id_errors = build_id_map(root, records)

    errors: list[str] = []
    errors.extend(load_errors)
    errors.extend(validate_schemas(root, records, validators))
    errors.extend(id_errors)
    errors.extend(validate_references(root, records, id_map))
    errors.extend(validate_relationships(root, records, id_map))
    errors.extend(validate_evidence_policy(root, records, id_map))

    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        print(f"\n{len(errors)} validation error(s)", file=sys.stderr)
        return 1

    print(f"OK {len(records)} records validated")
    return 0


def cmd_lint(_: argparse.Namespace) -> int:
    return run_lint(repo_root())


def cmd_graph_build(_: argparse.Namespace) -> int:
    root = repo_root()
    lint_status = run_lint(root)
    if lint_status != 0:
        return lint_status

    records, _ = load_records(root)
    graph = build_graph_data(root, records)
    output_dir = root / ".local"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "graph.json"
    output_path.write_text(json.dumps(graph, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {output_path.relative_to(root)}")
    return 0


def cmd_graph_inspect(args: argparse.Namespace) -> int:
    root = repo_root()
    graph_path = root / ".local" / "graph.json"
    if graph_path.exists():
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
    else:
        records, errors = load_records(root)
        if errors:
            for error in errors:
                print(f"ERROR {error}", file=sys.stderr)
            return 1
        graph = build_graph_data(root, records)

    needle = args.term.lower()
    matches = [
        node
        for node in graph.get("nodes", [])
        if needle in node.get("id", "").lower()
        or needle in node.get("label", "").lower()
        or needle in node.get("path", "").lower()
    ]
    for node in matches:
        print(f"{node['id']} [{node['kind']}] {node['path']}")
        print(f"  {node['label']}")
    print(f"{len(matches)} match(es)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fo", description="Finance OSINT local tooling")
    subparsers = parser.add_subparsers(dest="command", required=True)

    lint_parser = subparsers.add_parser("lint", help="validate repo records")
    lint_parser.set_defaults(func=cmd_lint)

    graph_parser = subparsers.add_parser("graph", help="graph utilities")
    graph_subparsers = graph_parser.add_subparsers(dest="graph_command", required=True)

    build_parser_ = graph_subparsers.add_parser("build", help="build .local/graph.json")
    build_parser_.set_defaults(func=cmd_graph_build)

    inspect_parser = graph_subparsers.add_parser("inspect", help="inspect graph records")
    inspect_parser.add_argument("term", help="case-insensitive search term")
    inspect_parser.set_defaults(func=cmd_graph_inspect)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
