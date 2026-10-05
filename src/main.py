from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from dotenv import load_dotenv

from .ifc_extract import extract_elements
from .baseline_enrich import baseline_enrich
from .llm_enrich import llm_enrich


def write_baseline_csv(result: dict, path: Path):
    rows = []
    for element in result["elements"]:
        enrichment = element["semantic_enrichment"]
        rows.append(
            {
                "global_id": element["global_id"],
                "ifc_class": element["ifc_class"],
                "name": element["name"],
                "matched_requirements": " | ".join(
                    enrichment["matched_requirements"]
                ),
                "method": enrichment["method"],
            }
        )

    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys() if rows else [
            "global_id", "ifc_class", "name", "matched_requirements", "method"
        ])
        writer.writeheader()
        writer.writerows(rows)


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Semantic BIM enrichment proof of concept"
    )
    parser.add_argument("--ifc", required=True, help="Path to IFC model")
    parser.add_argument("--spec", required=True, help="Path to technical specification .txt")
    parser.add_argument(
        "--mode",
        choices=["baseline", "llm"],
        default="baseline",
        help="baseline = deterministic mapping, llm = AI enrichment",
    )
    args = parser.parse_args()

    spec_text = Path(args.spec).read_text(encoding="utf-8")
    ifc_data = extract_elements(args.ifc)

    print(
        f"IFC schema: {ifc_data['schema']} | "
        f"Extracted elements: {len(ifc_data['elements'])}"
    )

    if args.mode == "baseline":
        result = baseline_enrich(ifc_data, spec_text)
    else:
        result = llm_enrich(ifc_data, spec_text)

    out_dir = Path("output")
    out_dir.mkdir(exist_ok=True)
    json_path = out_dir / f"enriched_{args.mode}.json"
    json_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )

    if args.mode == "baseline":
        csv_path = out_dir / "enriched_baseline.csv"
        write_baseline_csv(result, csv_path)
        print(f"CSV written to: {csv_path}")

    print(f"JSON written to: {json_path}")


if __name__ == "__main__":
    main()
