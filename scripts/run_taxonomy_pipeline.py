#!/usr/bin/env python3
"""Read-only input-adapter preflight for future taxonomy pipeline runs.

The validated pilot and full-ZINC builders currently have dataset-specific output
contracts. This command validates a replacement dataset and emits a machine-readable
execution plan; it deliberately does not write or modify taxonomy artifacts.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from rdkit import Chem, rdBase


ROOT = Path(__file__).resolve().parents[1]
RULESET_VERSION = "dag-rdkit-rules-1.1.1"
ID_CANDIDATES = ("source_compound_id", "compound_id", "source_id", "zinc_id", "id", "ID")
SMILES_CANDIDATES = ("isomeric_smiles", "smiles", "SMILES", "original_smiles")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_column(fieldnames: list[str], requested: str | None, candidates: tuple[str, ...], kind: str) -> str:
    if requested:
        if requested not in fieldnames:
            raise ValueError(f"requested {kind} column {requested!r} is absent; columns={fieldnames}")
        return requested
    for candidate in candidates:
        if candidate in fieldnames:
            return candidate
    raise ValueError(f"could not infer {kind} column; pass --{kind}-column; columns={fieldnames}")


def within_project(path: Path) -> bool:
    try:
        path.resolve().relative_to(ROOT.resolve())
        return True
    except ValueError:
        return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Validate an input table and print the adapter/execution plan. This is read-only: "
            "it does not standardize, classify, or modify canonical outputs."
        )
    )
    parser.add_argument("--input", required=True, type=Path, help="TSV or CSV input located inside the project root")
    parser.add_argument("--source", required=True, help="Source label, e.g. enamine or zinc")
    parser.add_argument("--output-prefix", required=True, help="Safe lowercase output namespace, e.g. enamine")
    parser.add_argument("--id-column", help="Stable source identifier column; inferred when omitted")
    parser.add_argument("--smiles-column", help="SMILES column; inferred when omitted")
    parser.add_argument("--delimiter", choices=("tab", "comma"), help="Override delimiter inference from filename")
    parser.add_argument("--max-rows", type=int, help="Bound validation for a quick probe; omitted scans all rows")
    args = parser.parse_args()

    input_path = args.input if args.input.is_absolute() else ROOT / args.input
    if not within_project(input_path):
        parser.error("--input must resolve inside /data01/cris/projects/DAG")
    if not input_path.is_file():
        parser.error(f"input does not exist or is not a file: {input_path}")
    if not args.output_prefix.replace("_", "").replace("-", "").isalnum() or args.output_prefix.lower() != args.output_prefix:
        parser.error("--output-prefix must be lowercase alphanumeric with optional '_' or '-'")
    if args.max_rows is not None and args.max_rows <= 0:
        parser.error("--max-rows must be positive")

    delimiter = "\t" if args.delimiter == "tab" or (args.delimiter is None and input_path.suffix.lower() != ".csv") else ","
    row_count = missing_ids = missing_smiles = invalid_smiles = duplicate_ids = 0
    seen_ids: set[str] = set()
    invalid_examples: list[dict[str, str]] = []
    with input_path.open(newline="", encoding="utf-8-sig", errors="strict") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        if not reader.fieldnames:
            parser.error("input has no header")
        try:
            id_column = resolve_column(reader.fieldnames, args.id_column, ID_CANDIDATES, "id")
            smiles_column = resolve_column(reader.fieldnames, args.smiles_column, SMILES_CANDIDATES, "smiles")
        except ValueError as exc:
            parser.error(str(exc))
        for row in reader:
            row_count += 1
            identifier = (row.get(id_column) or "").strip()
            smiles = (row.get(smiles_column) or "").strip()
            if not identifier:
                missing_ids += 1
            elif identifier in seen_ids:
                duplicate_ids += 1
            else:
                seen_ids.add(identifier)
            if not smiles:
                missing_smiles += 1
            elif Chem.MolFromSmiles(smiles) is None:
                invalid_smiles += 1
                if len(invalid_examples) < 10:
                    invalid_examples.append({"id": identifier, "smiles": smiles})
            if args.max_rows is not None and row_count >= args.max_rows:
                break

    critical = []
    if row_count == 0:
        critical.append("input contains no data rows")
    if missing_ids:
        critical.append(f"{missing_ids} rows have missing source identifiers")
    if duplicate_ids:
        critical.append(f"{duplicate_ids} rows repeat a source identifier")
    if missing_smiles:
        critical.append(f"{missing_smiles} rows have missing SMILES")
    plan = {
        "status": "READY_FOR_ADAPTER_IMPLEMENTATION" if not critical else "INPUT_SCHEMA_FAIL",
        "mode": "read_only_preflight",
        "input": str(input_path.relative_to(ROOT)),
        "input_sha256": sha256(input_path),
        "source": args.source,
        "output_prefix": args.output_prefix,
        "delimiter": "tab" if delimiter == "\t" else "comma",
        "id_column": id_column,
        "smiles_column": smiles_column,
        "rows_scanned": row_count,
        "scan_was_bounded": args.max_rows is not None,
        "missing_ids": missing_ids,
        "duplicate_ids": duplicate_ids,
        "missing_smiles": missing_smiles,
        "rdkit_parse_failures": invalid_smiles,
        "rdkit_parse_failure_examples": invalid_examples,
        "critical_errors": critical,
        "ruleset_version": RULESET_VERSION,
        "rdkit_version": rdBase.rdkitVersion,
        "planned_outputs": {
            "standardized": f"data/processed/{args.output_prefix}_compounds_standardised.tsv",
            "failed": f"data/processed/{args.output_prefix}_failed_compounds.tsv",
            "duplicates": f"data/processed/{args.output_prefix}_duplicate_mapping.tsv",
            "database": f"database/chemical_taxonomy_{args.output_prefix}.db",
            "taxonomy_namespace": f"taxonomy/{args.output_prefix}_*",
            "results_namespace": f"results/{args.output_prefix}/",
        },
        "execution_note": (
            "This command validates only. Before an Enamine production run, implement/review the source adapter "
            "and parameterize the builder output namespace; do not point dataset-specific pilot/full-ZINC builders "
            "at proprietary input."
        ),
    }
    print(json.dumps(plan, indent=2, sort_keys=True))
    raise SystemExit(1 if critical else 0)


if __name__ == "__main__":
    main()
