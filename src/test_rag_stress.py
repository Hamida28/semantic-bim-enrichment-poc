import json

from dotenv import load_dotenv

from src.ifc_extract import extract_elements
from src.rag_enrich import rag_enrich_element


load_dotenv()


# =========================================================
# LOAD IFC
# =========================================================

ifc_data = extract_elements(
    "data/model.ifc",
    max_elements=100,
)


# =========================================================
# LOAD STRESS SPECIFICATION
# =========================================================

with open(
    "data/spec_stress.txt",
    "r",
    encoding="utf-8",
) as file:
    specification = file.read()


# =========================================================
# OBJECTS TO TEST
# =========================================================

TEST_OBJECTS = [

    {
        "case_id": "DOOR",
        "global_id": "0pGAjlJMP3ifYPATVF5xAR",
    },

    {
        "case_id": "WINDOW",
        "global_id": "1srAI$R4T8ihLXSNHmUSET",
    },

    {
        "case_id": "WALL",
        "global_id": "2XPyKWY018sA1ygZKgQPtU",
    },

    {
        "case_id": "SLAB",
        "global_id": "1pPHnf7cXCpPsNEnQf8_6B",
    },
]


# =========================================================
# END-TO-END TEST
# =========================================================

for test_case in TEST_OBJECTS:

    element = next(
        element
        for element in ifc_data["elements"]
        if element["global_id"] == test_case["global_id"]
    )

    print("\n" + "=" * 80)
    print("CASE:", test_case["case_id"])
    print("OBJECT:", element["name"])
    print("IFC CLASS:", element["ifc_class"])

    result = rag_enrich_element(
        element,
        specification,
        top_k=3,
    )

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )