from src.rag_retriever import chunk_specification
from src.requirement_classifier import (
    classify_requirement_ifc_entity,
)


# =========================================================
# GROUND TRUTH
# =========================================================

GROUND_TRUTH = {
    "REQ-001": "IfcDoor",
    "REQ-002": "IfcWindow",
    "REQ-003": "IfcWall",
    "REQ-004": "IfcSlab",

    # REQ-005 = PROCESS, therefore no IFC entity

    "REQ-006": "IfcDoor",
    "REQ-007": "IfcDoor",
    "REQ-008": "IfcWindow",
    "REQ-009": "IfcWall",
    "REQ-010": "IfcSlab",
}


# =========================================================
# LOAD REQUIREMENTS
# =========================================================

with open(
    "data/spec_stress.txt",
    "r",
    encoding="utf-8",
) as file:
    specification = file.read()


chunks = chunk_specification(specification)


# =========================================================
# EVALUATION
# =========================================================

results = []


for chunk in chunks:

    if chunk.get("scope") != "object":
        continue

    requirement_id = chunk["chunk_id"]
    requirement_text = chunk["text"]

    expected = GROUND_TRUTH.get(requirement_id)

    actual = classify_requirement_ifc_entity(
        requirement_text
    )

    passed = actual == expected

    results.append(passed)

    print("\n" + "=" * 70)
    print("REQUIREMENT:", requirement_id)
    print("TEXT:", requirement_text)
    print("EXPECTED:", expected)
    print("ACTUAL:", actual)
    print("RESULT:", "PASS" if passed else "FAIL")


# =========================================================
# METRICS
# =========================================================

total = len(results)

passed = sum(results)

accuracy = passed / total if total else 0


print("\n" + "=" * 70)
print("CLASSIFIER METRICS")
print("=" * 70)

print("Total:", total)
print("PASS:", passed)
print("FAIL:", total - passed)
print(f"Accuracy: {accuracy:.2%}")