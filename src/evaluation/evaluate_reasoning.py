import csv
import os

from dotenv import load_dotenv

from src.core.ifc_extract import extract_elements
from src.rag.rag_enrich import rag_enrich_element


load_dotenv()


# =========================================================
# GROUND TRUTH
# =========================================================

TEST_CASES = [

    # -----------------------------------------------------
    # CAS RÃ‰ELS â†’ applicabilitÃ© incertaine
    # -----------------------------------------------------

    {
        "case_id": "DOOR_REAL",
        "global_id": "0pGAjlJMP3ifYPATVF5xAR",
        "extra_context": None,
        "expected": {
            "REQ-001": "uncertain",
            "REQ-002": "not_applicable",
            "REQ-003": "not_applicable",
            "REQ-004": "not_applicable",
        },
    },

    {
        "case_id": "WINDOW_REAL",
        "global_id": "1srAI$R4T8ihLXSNHmUSET",
        "extra_context": None,
        "expected": {
            "REQ-001": "not_applicable",
            "REQ-002": "uncertain",
            "REQ-003": "not_applicable",
            "REQ-004": "not_applicable",
        },
    },

    {
        "case_id": "WALL_REAL",
        "global_id": "2XPyKWY018sA1ygZKgQPtU",
        "extra_context": None,
        "expected": {
            "REQ-001": "not_applicable",
            "REQ-002": "not_applicable",
            "REQ-003": "uncertain",
            "REQ-004": "not_applicable",
        },
    },

    {
        "case_id": "SLAB_REAL",
        "global_id": "1pPHnf7cXCpPsNEnQf8_6B",
        "extra_context": None,
        "expected": {
            "REQ-001": "not_applicable",
            "REQ-002": "not_applicable",
            "REQ-003": "not_applicable",
            "REQ-004": "uncertain",
        },
    },

    # -----------------------------------------------------
    # CAS SYNTHÃ‰TIQUES â†’ applicabilitÃ© confirmÃ©e
    # -----------------------------------------------------

    {
        "case_id": "DOOR_APPLICABLE",
        "global_id": "0pGAjlJMP3ifYPATVF5xAR",

        "extra_context": {
            "protected_circulation_route": True,
            "door_on_protected_circulation_route": True,
            "evidence":
                "This door is explicitly documented as being "
                "on a protected circulation route."
        },

        "expected": {
            "REQ-001": "applicable",
            "REQ-002": "not_applicable",
            "REQ-003": "not_applicable",
            "REQ-004": "not_applicable",
        },
    },

    {
        "case_id": "WINDOW_APPLICABLE",
        "global_id": "1srAI$R4T8ihLXSNHmUSET",

        "extra_context": {
            "external_window": True,
            "acoustic_performance_required": True,
            "evidence":
                "This window is explicitly confirmed as an "
                "external window and acoustic performance "
                "is specified by the project requirements."
        },

        "expected": {
            "REQ-001": "not_applicable",
            "REQ-002": "applicable",
            "REQ-003": "not_applicable",
            "REQ-004": "not_applicable",
        },
    },

    {
        "case_id": "WALL_APPLICABLE",
        "global_id": "2XPyKWY018sA1ygZKgQPtU",

        "extra_context": {
            "separates_distinct_dwelling_units": True,
            "evidence":
                "This wall is explicitly documented as "
                "separating two distinct dwelling units."
        },

        "expected": {
            "REQ-001": "not_applicable",
            "REQ-002": "not_applicable",
            "REQ-003": "applicable",
            "REQ-004": "not_applicable",
        },
    },

    {
        "case_id": "SLAB_APPLICABLE",
        "global_id": "1pPHnf7cXCpPsNEnQf8_6B",

        "extra_context": {
            "technical_area": True,
            "fire_resistance_requirement_applicable": True,
            "evidence":
                "This slab is explicitly located in a "
                "technical area where a fire-resistance "
                "requirement applies."
        },

        "expected": {
            "REQ-001": "not_applicable",
            "REQ-002": "not_applicable",
            "REQ-003": "not_applicable",
            "REQ-004": "applicable",
        },
    },
]


# =========================================================
# CHARGEMENT DES DONNÃ‰ES
# =========================================================

ifc_data = extract_elements(
    "data/model.ifc",
    max_elements=100,
)


with open(
    "data/spec.txt",
    "r",
    encoding="utf-8",
) as file:
    specification = file.read()


results = []


# =========================================================
# EXÃ‰CUTION DES TESTS
# =========================================================

for case in TEST_CASES:

    element = next(
        element
        for element in ifc_data["elements"]
        if element["global_id"] == case["global_id"]
    )

    print("\n" + "=" * 80)
    print("TEST:", case["case_id"])
    print("OBJECT:", element["name"])

    rag_result = rag_enrich_element(
        element,
        specification,

        # IMPORTANT :
        # on fournit toutes les exigences OBJECT.
        # Ici on teste le raisonnement, pas le retrieval.
        top_k=4,

        extra_context=case["extra_context"],
    )

    actual_by_requirement = {
        item["source_chunk_id"]: item
        for item in rag_result["analysis"]
    }

    for requirement_id, expected_status in case["expected"].items():

        actual_item = actual_by_requirement.get(
            requirement_id
        )

        if actual_item:
            actual_status = actual_item.get("status")
        else:
            actual_status = "missing"

        passed = actual_status == expected_status

        print(
            requirement_id,
            "| expected:",
            expected_status,
            "| actual:",
            actual_status,
            "|",
            "PASS" if passed else "FAIL",
        )

        results.append(
            {
                "case_id": case["case_id"],
                "object_name": element["name"],
                "requirement_id": requirement_id,
                "expected_status": expected_status,
                "actual_status": actual_status,
                "result": "PASS" if passed else "FAIL",
            }
        )


# =========================================================
# MÃ‰TRIQUES
# =========================================================

total = len(results)

passed = sum(
    1
    for result in results
    if result["result"] == "PASS"
)

failed = total - passed

accuracy = passed / total if total else 0


print("\n" + "=" * 80)
print("FINAL RESULTS")
print("=" * 80)

print("Total decisions:", total)
print("PASS:", passed)
print("FAIL:", failed)
print(f"Accuracy: {accuracy:.2%}")


# =========================================================
# RÃ‰SULTATS PAR STATUT
# =========================================================

for status in [
    "applicable",
    "uncertain",
    "not_applicable",
]:

    status_results = [
        result
        for result in results
        if result["expected_status"] == status
    ]

    status_passed = sum(
        1
        for result in status_results
        if result["result"] == "PASS"
    )

    status_total = len(status_results)

    status_accuracy = (
        status_passed / status_total
        if status_total
        else 0
    )

    print(
        f"{status}: "
        f"{status_passed}/{status_total} "
        f"({status_accuracy:.2%})"
    )


# =========================================================
# EXPORT CSV
# =========================================================

os.makedirs(
    "output",
    exist_ok=True,
)

output_file = "output/reasoning_evaluation.csv"


with open(
    output_file,
    "w",
    newline="",
    encoding="utf-8",
) as csvfile:

    fieldnames = [
        "case_id",
        "object_name",
        "requirement_id",
        "expected_status",
        "actual_status",
        "result",
    ]

    writer = csv.DictWriter(
        csvfile,
        fieldnames=fieldnames,
    )

    writer.writeheader()
    writer.writerows(results)


print("\nCSV saved to:", output_file)
