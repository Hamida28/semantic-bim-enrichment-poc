import json

from dotenv import load_dotenv

from src.ifc_extract import extract_elements
from src.rag_enrich import rag_enrich_element


load_dotenv()


TEST_CASES = [

    {
        "case_id": "DOOR_APPLICABLE",
        "global_id": "0pGAjlJMP3ifYPATVF5xAR",
        "expected_requirement": "REQ-001",
        "expected_status": "applicable",

        "extra_context": {
            "protected_circulation_route": True,
            "door_on_protected_circulation_route": True,
            "evidence":
                "This door is explicitly documented as being "
                "on a protected circulation route."
        },
    },

    {
        "case_id": "WINDOW_APPLICABLE",
        "global_id": "1srAI$R4T8ihLXSNHmUSET",
        "expected_requirement": "REQ-002",
        "expected_status": "applicable",

        "extra_context": {
            "external_window": True,
            "acoustic_performance_required": True,
            "evidence":
                "This window is explicitly confirmed as an "
                "external window and acoustic performance "
                "is specified by the project requirements."
        },
    },

    {
        "case_id": "WALL_APPLICABLE",
        "global_id": "2XPyKWY018sA1ygZKgQPtU",
        "expected_requirement": "REQ-003",
        "expected_status": "applicable",

        "extra_context": {
            "separates_distinct_dwelling_units": True,
            "evidence":
                "This wall is explicitly documented as "
                "separating two distinct dwelling units."
        },
    },

    {
        "case_id": "SLAB_APPLICABLE",
        "global_id": "1pPHnf7cXCpPsNEnQf8_6B",
        "expected_requirement": "REQ-004",
        "expected_status": "applicable",

        "extra_context": {
            "technical_area": True,
            "fire_resistance_requirement_applicable": True,
            "evidence":
                "This slab is explicitly located in a "
                "technical area where a fire-resistance "
                "requirement applies."
        },
    },
]


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


for case in TEST_CASES:

    element = next(
        element
        for element in ifc_data["elements"]
        if element["global_id"] == case["global_id"]
    )

    print("\n" + "=" * 80)
    print("TEST CASE:", case["case_id"])
    print("OBJECT:", element["name"])

    print(
        "EXPECTED:",
        case["expected_requirement"],
        "→",
        case["expected_status"],
    )

    result = rag_enrich_element(
        element,
        specification,
        top_k=5,
        extra_context=case["extra_context"],
    )

    print("\nACTUAL RESULT:")

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )