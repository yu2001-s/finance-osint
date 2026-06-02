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
    "claim_predicate": "claim-predicate.schema.json",
    "metric_definition": "metric-definition.schema.json",
    "metric": "metric.schema.json",
    "event": "event.schema.json",
    "dataset": "dataset.schema.json",
    "claim": "claim.schema.json",
    "validation": "validation.schema.json",
    "challenge": "challenge.schema.json",
    "relationship_type": "relationship-type.schema.json",
    "relationship": "relationship.schema.json",
    "thesis": "thesis.schema.json",
}

REF_PREFIXES = (
    "entity:",
    "source:",
    "evidence:",
    "claim_predicate:",
    "metric_definition:",
    "metric:",
    "event:",
    "dataset:",
    "claim:",
    "validation:",
    "challenge:",
    "relationship:",
    "rel:",
    "thesis:",
    "debate:",
    "arg:",
    "resolution:",
)

SKIP_PARTS = {".git", ".local", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache"}
DATA_DIRS = (
    "relationship-types",
    "claim-predicates",
    "metric-definitions",
    "entities",
    "sources",
    "evidence",
    "datasets",
    "metrics",
    "events",
    "claims",
    "validations",
    "challenges",
    "relationships",
    "theses",
)

EVIDENCE_CLASSES_REQUIRING_ACCESS = {
    "firsthand_public",
    "firsthand_private",
    "anonymous_internal",
    "rumor",
}
LOW_TRUST_EVIDENCE_CLASSES = {"anonymous_internal", "rumor"}
OLD_EVIDENCE_CLASSES = {
    "E0_public_primary",
    "E1_public_secondary",
    "E2_firsthand_public",
    "E3_firsthand_private",
    "E4_anonymous_internal",
    "E5_unverified_rumor",
}
NO_TRUTH_FIELDS_KINDS = {"claim", "relationship", "thesis", "metric", "event", "evidence"}
NO_AUTHOR_FIELD_KINDS = {"validation", "challenge", "thesis"}


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


def iter_yaml_files(root: Path, include_archive: bool = True) -> list[Path]:
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
    if include_archive:
        archive = root / "archive"
        if archive.exists():
            for path in archive.rglob("*"):
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


def load_records(root: Path, include_archive: bool = True) -> tuple[list[Record], list[str]]:
    records: list[Record] = []
    errors: list[str] = []
    for path in iter_yaml_files(root, include_archive=include_archive):
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
            if path == ("id",):
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
        if record.kind == "relationship_type" and record.data.get("state") == "registered"
    }


def proposed_relationship_types(records: list[Record]) -> dict[str, Record]:
    return {
        record.id: record
        for record in records
        if record.kind == "relationship_type" and record.data.get("state") == "proposed"
    }


def registered_claim_predicates(records: list[Record]) -> dict[str, Record]:
    return {
        str(record.data.get("name")): record
        for record in records
        if record.kind == "claim_predicate" and record.data.get("state") == "registered"
    }


def proposed_claim_predicates(records: list[Record]) -> dict[str, Record]:
    return {
        str(record.data.get("name")): record
        for record in records
        if record.kind == "claim_predicate" and record.data.get("state") == "proposed"
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


def as_reference_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if not isinstance(value, list):
        return []
    found: list[str] = []
    for item in value:
        if isinstance(item, str):
            found.append(item)
        elif isinstance(item, dict) and isinstance(item.get("id"), str):
            found.append(str(item["id"]))
    return found


def evidence_class_for(record_id: str, id_map: dict[str, Record]) -> str | None:
    record = id_map.get(record_id)
    if not record or record.kind != "evidence":
        return None
    return str(record.data.get("evidence_class"))


def evidence_ids_for_claim(record: Record) -> list[str]:
    return as_reference_list(record.data.get("evidence"))


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

        role_defs = {
            role.get("name"): role
            for role in type_def.data.get("roles", [])
            if isinstance(role, dict) and isinstance(role.get("name"), str)
        }
        participants = record.data.get("participants", [])
        role_counts: dict[str, int] = {}
        if not isinstance(participants, list):
            continue

        for participant in participants:
            if not isinstance(participant, dict):
                continue
            role = str(participant.get("role", ""))
            participant_id = participant.get("entity")
            role_counts[role] = role_counts.get(role, 0) + 1

            if role not in role_defs:
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
            allowed_entity_types = role_defs[role].get("allowed_entity_types", [])
            if actual_entity_type and actual_entity_type not in allowed_entity_types:
                errors.append(
                    f"{relative}: `{participant_id}` has entity_type `{actual_entity_type}`, "
                    f"but role `{role}` expects one of {allowed_entity_types}"
                )

        for role_name, role_def in role_defs.items():
            count = role_counts.get(str(role_name), 0)
            min_count = int(role_def.get("min", 0))
            max_count = role_def.get("max")
            if role_def.get("required") and count < min_count:
                errors.append(
                    f"{relative}: relationship type `{rel_type}` requires at least "
                    f"{min_count} participant(s) for role `{role_name}`"
                )
            if isinstance(max_count, int) and count > max_count:
                errors.append(
                    f"{relative}: relationship type `{rel_type}` allows at most "
                    f"{max_count} participant(s) for role `{role_name}`"
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


def evidence_items_have_methodology(record: Record) -> bool:
    evidence = record.data.get("evidence")
    if not isinstance(evidence, list):
        return False
    return any(isinstance(item, dict) and bool(item.get("methodology")) for item in evidence)


def validate_claim_predicates(root: Path, records: list[Record]) -> list[str]:
    errors: list[str] = []
    registered = registered_claim_predicates(records)
    proposed = proposed_claim_predicates(records)

    for record in records:
        if record.kind != "claim":
            continue

        relative = record.path.relative_to(root)
        predicate = str(record.data.get("predicate", ""))
        predicate_def: Record | None = None

        if predicate.startswith("provisional:"):
            proposed_name = predicate.split(":", 1)[1]
            proposed_path = record.data.get("proposed_predicate_definition")
            if not proposed_path:
                errors.append(
                    f"{relative}: provisional predicate `{predicate}` needs "
                    "proposed_predicate_definition"
                )
            else:
                definition_path = root / str(proposed_path)
                if not definition_path.exists():
                    errors.append(
                        f"{relative}: proposed_predicate_definition `{proposed_path}` does not exist"
                    )
            if proposed_name not in proposed:
                errors.append(
                    f"{relative}: provisional predicate `{predicate}` has no proposed "
                    "claim_predicate record"
                )
            else:
                predicate_def = proposed[proposed_name]
        else:
            if predicate not in registered:
                errors.append(f"{relative}: claim predicate `{predicate}` is not registered")
            else:
                predicate_def = registered[predicate]

        if predicate_def is None:
            continue

        allowed_support = predicate_def.data.get("allowed_support_type", [])
        support_type = record.data.get("support_type")
        if allowed_support and support_type not in allowed_support:
            errors.append(
                f"{relative}: support_type `{support_type}` is not allowed by predicate "
                f"`{predicate}`"
            )

    return errors


def validate_evidence_policy(
    root: Path, records: list[Record], id_map: dict[str, Record]
) -> list[str]:
    errors: list[str] = []

    for record in records:
        relative = record.path.relative_to(root)

        for path, value in walk_strings(record.data):
            if value == "anonymous_to_maintainers":
                dotted = ".".join(path) or "$"
                errors.append(f"{relative}: {dotted} uses hidden attribution `anonymous_to_maintainers`")

        if record.kind in NO_TRUTH_FIELDS_KINDS:
            for field in ("status", "confidence"):
                if field in record.data:
                    errors.append(
                        f"{relative}: canonical `{record.kind}` records must not store `{field}`; "
                        "derive review state locally"
                    )

        if record.kind == "validation" and "confidence" in record.data:
            errors.append(
                f"{relative}: validation records must not store `confidence`; derive review state locally"
            )

        if record.kind == "challenge" and "status" in record.data:
            errors.append(
                f"{relative}: challenge records must not store `status`; use addressed_by, "
                "withdrawn_by, or superseded_by"
            )

        if record.kind in NO_AUTHOR_FIELD_KINDS and "author" in record.data:
            errors.append(f"{relative}: use `submitted_by`, not `author`")

        if record.kind == "evidence":
            evidence_class = str(record.data.get("evidence_class", ""))
            if evidence_class in OLD_EVIDENCE_CLASSES:
                errors.append(f"{relative}: use plain v1 evidence_class labels, not `{evidence_class}`")
            if evidence_class in EVIDENCE_CLASSES_REQUIRING_ACCESS:
                if "source_attribution" not in record.data:
                    errors.append(f"{relative}: evidence must declare source_attribution")
                if not isinstance(record.data.get("source_access"), dict):
                    errors.append(f"{relative}: evidence must declare source_access")
                if "risk_flags" not in record.data:
                    errors.append(f"{relative}: evidence must declare risk_flags")
            if evidence_class in LOW_TRUST_EVIDENCE_CLASSES and not record.data.get("risk_flags"):
                errors.append(f"{relative}: low-trust evidence must include at least one risk_flag")

        if record.kind == "claim":
            support_type = str(record.data.get("support_type", ""))
            evidence_ids = evidence_ids_for_claim(record)
            evidence_classes = evidence_support_classes(evidence_ids, id_map)
            methodology_present = bool(record.data.get("methodology")) or evidence_items_have_methodology(
                record
            )

            if support_type == "direct" and evidence_classes and evidence_classes <= {"rumor"}:
                errors.append(
                    f"{relative}: direct support_type cannot rely only on rumor evidence"
                )
            if support_type == "inferred" and len(evidence_ids) < 2 and not methodology_present:
                errors.append(
                    f"{relative}: inferred support_type needs multiple evidence records or methodology"
                )
            if support_type == "private_attestation" and not (
                evidence_classes & {"firsthand_private", "anonymous_internal"}
            ):
                errors.append(
                    f"{relative}: private_attestation support_type needs firsthand_private or "
                    "anonymous_internal evidence"
                )
            if support_type == "rumor" and "rumor" not in evidence_classes:
                errors.append(f"{relative}: rumor support_type needs rumor evidence")

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
            participants = record.data.get("participants", [])
            if isinstance(participants, list):
                participant_items = [
                    (str(item.get("role")), item.get("entity"))
                    for item in participants
                    if isinstance(item, dict)
                ]
            elif isinstance(participants, dict):
                participant_items = list(participants.items())
            else:
                participant_items = []
            for role, participant_id in participant_items:
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
        "schema_version": 1,
        "node_count": len(nodes),
        "edge_count": len(unique_edges),
        "nodes": nodes,
        "edges": unique_edges,
    }


def json_error(error: str) -> dict[str, Any]:
    path = ""
    message = error
    if ": " in error:
        maybe_path, maybe_message = error.split(": ", 1)
        if "/" in maybe_path or maybe_path.endswith((".yml", ".yaml")):
            path = maybe_path
            message = maybe_message
    return {
        "code": "validation_error",
        "path": path,
        "json_pointer": None,
        "message": message,
        "hint": None,
        "record_id": None,
        "related_ids": [],
    }


def run_lint(root: Path, json_output: bool = False, current_only: bool = False) -> int:
    validators = load_schemas(root)
    records, load_errors = load_records(root, include_archive=not current_only)
    id_map, id_errors = build_id_map(root, records)

    errors: list[str] = []
    errors.extend(load_errors)
    errors.extend(validate_schemas(root, records, validators))
    errors.extend(id_errors)
    errors.extend(validate_references(root, records, id_map))
    errors.extend(validate_claim_predicates(root, records))
    errors.extend(validate_relationships(root, records, id_map))
    errors.extend(validate_evidence_policy(root, records, id_map))

    if json_output:
        print(
            json.dumps(
                {
                    "ok": not errors,
                    "command": "lint",
                    "repo_root": str(root),
                    "records_checked": len(records),
                    "warnings": [],
                    "errors": [json_error(error) for error in errors],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1 if errors else 0

    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        print(f"\n{len(errors)} validation error(s)", file=sys.stderr)
        return 1

    print(f"OK {len(records)} records validated")
    return 0


def cmd_lint(args: argparse.Namespace) -> int:
    return run_lint(repo_root(), json_output=bool(args.json), current_only=bool(args.current_only))


def cmd_graph_build(_: argparse.Namespace) -> int:
    root = repo_root()
    lint_status = run_lint(root, current_only=True)
    if lint_status != 0:
        return lint_status

    records, _ = load_records(root, include_archive=False)
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
        records, errors = load_records(root, include_archive=False)
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
    lint_parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    lint_parser.add_argument(
        "--current-only",
        action="store_true",
        help="skip archive records during validation",
    )
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
