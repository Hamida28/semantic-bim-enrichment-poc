def classify_requirement_ifc_entity(requirement_text: str):
    """
    Infer the IFC entity family explicitly targeted
    by a requirement.

    This is a deterministic baseline classifier.
    It does not use the evaluation ground truth.
    """

    text = requirement_text.lower()

    entity_keywords = {
        "IfcDoor": [
            "door",
            "doors",
        ],
        "IfcWindow": [
            "window",
            "windows",
        ],
        "IfcWall": [
            "wall",
            "walls",
        ],
        "IfcSlab": [
            "floor slab",
            "floor slabs",
            "slab",
            "slabs",
        ],
    }

    matches = []

    for ifc_entity, keywords in entity_keywords.items():
        if any(keyword in text for keyword in keywords):
            matches.append(ifc_entity)

    if len(matches) == 1:
        return matches[0]

    

    # No explicit entity found, or ambiguous requirement.
    return None

def normalize_ifc_entity_family(ifc_class: str):
    """
    Normalize concrete IFC classes into the entity families
    used by the requirement classifier.
    """

    mapping = {
        "IfcDoor": "IfcDoor",
        "IfcWindow": "IfcWindow",
        "IfcWall": "IfcWall",
        "IfcWallStandardCase": "IfcWall",
        "IfcSlab": "IfcSlab",
    }

    return mapping.get(ifc_class)