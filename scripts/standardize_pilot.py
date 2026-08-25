#!/usr/bin/env python3
"""Standardize and deduplicate a tab-separated molecular dataset."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.standardize import StandardizationError, standardize_smiles  # noqa: E402


RESULT_FIELDS = [
    "canonical_smiles", "isomeric_smiles", "inchi", "inchikey",
    "molecular_formula", "molecular_weight", "formal_charge",
    "heavy_atom_count", "stereochemistry_status", "sanitisation_status",
    "fragment_count", "fragment_policy", "removed_fragments_smiles",
    "charge_normalisation", "tautomer_policy", "isotope_status",
    "deduplication_key",
]


def preserve_existing(paths: list[Path]) -> list[tuple[Path, Path]]:
    """Rename existing targets before a run; never truncate prior artifacts."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    renamed: list[tuple[Path, Path]] = []
    for path in paths:
        if path.exists():
            backup = path.with_name(f"{path.name}.old_{stamp}")
            if backup.exists():
                raise FileExistsError(f"refusing to overwrite backup: {backup}")
            path.rename(backup)
            renamed.append((path, backup))
    return renamed


def run(input_path: Path, output_path: Path, failed_path: Path, duplicate_path: Path, metrics_path: Path) -> dict:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    failed_path.parent.mkdir(parents=True, exist_ok=True)
    duplicate_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    preserve_existing([output_path, failed_path, duplicate_path, metrics_path])
    successes: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []
    duplicates: list[dict[str, str]] = []
    representatives: dict[str, str] = {}

    with input_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if not reader.fieldnames or "zinc_id" not in reader.fieldnames or "original_smiles" not in reader.fieldnames:
            raise ValueError("input must contain zinc_id and original_smiles columns")
        input_fields = list(reader.fieldnames)
        raw_count = 0
        for row in reader:
            raw_count += 1
            source_id = row["zinc_id"]
            try:
                standardized = standardize_smiles(row["original_smiles"])
            except StandardizationError as exc:
                failures.append({
                    "compound_id": source_id,
                    "original_smiles": row["original_smiles"],
                    "failure_stage": exc.stage,
                    "failure_reason": exc.reason,
                })
                continue
            result = {"source_compound_id": source_id, **row, **standardized.as_dict()}
            key = standardized.deduplication_key
            if key in representatives:
                duplicates.append({
                    "duplicate_source_compound_id": source_id,
                    "representative_source_compound_id": representatives[key],
                    "deduplication_key": key,
                    "duplicate_original_smiles": row["original_smiles"],
                    "reason": "identical standardized canonical isomeric SMILES",
                })
            else:
                representatives[key] = source_id
                successes.append(result)

    output_fields = ["source_compound_id", *input_fields, *RESULT_FIELDS]
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=output_fields)
        writer.writeheader()
        writer.writerows(successes)
    failure_fields = ["compound_id", "original_smiles", "failure_stage", "failure_reason"]
    with failed_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=failure_fields)
        writer.writeheader()
        writer.writerows(failures)
    duplicate_fields = [
        "duplicate_source_compound_id", "representative_source_compound_id",
        "deduplication_key", "duplicate_original_smiles", "reason",
    ]
    with duplicate_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=duplicate_fields)
        writer.writeheader()
        writer.writerows(duplicates)

    metrics = {
        "raw_count": raw_count,
        "successfully_parsed_and_standardized_count": raw_count - len(failures),
        "failed_count": len(failures),
        "duplicates_removed_count": len(duplicates),
        "final_unique_count": len(successes),
        "accounting_check": raw_count == len(failures) + len(duplicates) + len(successes),
    }
    metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/pilot/zinc_commercial_building_blocks_1000_raw.tsv"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/pilot_compounds_standardised.tsv"))
    parser.add_argument("--failed", type=Path, default=Path("data/processed/failed_compounds.tsv"))
    parser.add_argument("--duplicates", type=Path, default=Path("data/processed/pilot_duplicate_mapping.tsv"))
    parser.add_argument("--metrics", type=Path, default=Path("results/pilot/standardisation_metrics.json"))
    args = parser.parse_args()
    print(json.dumps(run(args.input, args.output, args.failed, args.duplicates, args.metrics), indent=2))


if __name__ == "__main__":
    main()
