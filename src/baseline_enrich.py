from __future__ import annotations

import re


KEYWORDS = {
    "IfcDoor": ["door", "doors", "porte", "portes"],
    "IfcWindow": ["window", "windows", "fenêtre", "fenêtres"],
    "IfcWall": ["wall", "walls", "mur", "murs", "cloison", "cloisons"],
    "IfcWallStandardCase": ["wall", "walls", "mur", "murs", "cloison", "cloisons"],
    "IfcSlab": ["slab", "slabs", "dalle", "dalles", "plancher", "planchers"],
}


def _split_requirements(text: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [chunk.strip(" -\t") for chunk in chunks if chunk.strip()]


def baseline_enrich(ifc_data: dict, specification: str) -> dict:
    """
    Simple deterministic baseline:
    associates requirement sentences with IFC object classes using keywords.
    This is intentionally NOT the AI part. It proves the data pipeline first.
    """
    requirements = _split_requirements(specification)
    enriched = []

    for element in ifc_data["elements"]:
        cls = element["ifc_class"]
        keywords = KEYWORDS.get(cls, [])
        matches = [
            req for req in requirements
            if any(word.lower() in req.lower() for word in keywords)
        ]

        enriched.append(
            {
                **element,
                "semantic_enrichment": {
                    "matched_requirements": matches,
                    "method": "deterministic_baseline",
                },
            }
        )

    return {
        "ifc_schema": ifc_data["schema"],
        "method": "deterministic_baseline",
        "elements": enriched,
    }
