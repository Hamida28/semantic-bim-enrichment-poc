from __future__ import annotations

from typing import Any
import ifcopenshell
import ifcopenshell.util.element


TARGET_CLASSES = ["IfcWall", "IfcDoor", "IfcWindow", "IfcSlab"]


def _safe(value: Any) -> Any:
    """Convert IFC values to JSON-friendly values."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe(v) for v in value]
    return str(value)


def extract_elements(ifc_path: str, max_elements: int = 40) -> dict:
    model = ifcopenshell.open(ifc_path)

    elements = []
    for ifc_class in TARGET_CLASSES:
        for element in model.by_type(ifc_class):
            psets = ifcopenshell.util.element.get_psets(element)
            elements.append(
                {
                    "global_id": getattr(element, "GlobalId", None),
                    "ifc_class": element.is_a(),
                    "name": getattr(element, "Name", None),
                    "description": getattr(element, "Description", None),
                    "object_type": getattr(element, "ObjectType", None),
                    "properties": _safe(psets),
                }
            )
            if len(elements) >= max_elements:
                return {"schema": model.schema, "elements": elements}

    return {"schema": model.schema, "elements": elements}
