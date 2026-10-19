import sys

from dotenv import load_dotenv

from src.core.ifc_extract import extract_elements
from src.rag.rag_enrich import rag_enrich_element


load_dotenv()


# =========================================================
# GROUND TRUTH â€” CURRENT V1 ARCHITECTURE
# =========================================================

TEST_CASES = [

    {
        "case_id": "DOOR",
        "global_id": "0pGAjlJMP3ifYPATVF5xAR",

        # Requirements that should survive structural filtering
        "expected_requirements": {
            "REQ-001": "uncertain",
            "REQ-006": "uncertain",
            "REQ-007": "not_applicable",
        },
    },

    {
        "case_id": "WINDOW",
        "global_id": "1srAI$R4T8ihLXSNHmUSET",

        "expected_requirements": {
            "REQ-002": "uncertain",
            "REQ-008": "not_applicable",
        },
    },

    {
        "case_id": "WALL",
        "global_id": "2XPyKWY018sA1ygZKgQPtU",

        "expected_requirements": {
            "REQ-003": "uncertain",
            "REQ-009": "uncertain",
        },
    },

    {
        "case_id": "SLAB",
        "global_id": "1pPHnf7cXCpPsNEnQf8_6B",

        "expected_requirements": {
            "REQ-004": "uncertain",
            "REQ-010": "uncertain",
        },
    },
]


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
# HELPERS
# =========================================================

results = []


def record_check(
    case_id,
    check_name,
    passed,
    details="",
):
    results.append(
        {
            "case_id": case_id,
            "check": check_name,
            "passed": passed,
            "details": details,
        }
    )

    print(
        "PASS" if passed else "FAIL",
        "|",
        check_name,
        "|",
        details,
    )


# =========================================================
# END-TO-END REGRESSION
# =========================================================

for case in TEST_CASES:

    element = next(
        element
        for element in ifc_data["elements"]
        if element["global_id"] == case["global_id"]
    )

    print("\n" + "=" * 80)
    print("CASE:", case["case_id"])
    print("OBJECT:", element["name"])
    print("IFC CLASS:", element["ifc_class"])
    print("=" * 80)

    result = rag_enrich_element(
        element,
        specification,
        top_k=3,
    )

    expected = case["expected_requirements"]

    expected_ids = set(expected.keys())

    retrieved_ids = {
        source["chunk_id"]
        for source in result.get(
            "retrieved_sources",
            [],
        )
    }

    analysis_by_id = {
        item["source_chunk_id"]: item
        for item in result.get(
            "analysis",
            []
        )
    }

    analysis_ids = set(
        analysis_by_id.keys()
    )

    # -----------------------------------------------------
    # 1. STRUCTURAL RETRIEVAL
    # -----------------------------------------------------

    record_check(
        case["case_id"],
        "retrieved requirement set",
        retrieved_ids == expected_ids,
        (
            f"expected={sorted(expected_ids)} "
            f"actual={sorted(retrieved_ids)}"
        ),
    )

    # -----------------------------------------------------
    # 2. LLM ANALYSES THE SAME REQUIREMENTS
    # -----------------------------------------------------

    record_check(
        case["case_id"],
        "analysis requirement set",
        analysis_ids == expected_ids,
        (
            f"expected={sorted(expected_ids)} "
            f"actual={sorted(analysis_ids)}"
        ),
    )

    # -----------------------------------------------------
    # 3. EXPECTED STATUS
    # -----------------------------------------------------

    for requirement_id, expected_status in expected.items():

        item = analysis_by_id.get(
            requirement_id
        )

        if item is None:

            record_check(
                case["case_id"],
                f"{requirement_id} status",
                False,
                "requirement missing from analysis",
            )

            continue

        actual_status = item.get("status")

        record_check(
            case["case_id"],
            f"{requirement_id} status",
            actual_status == expected_status,
            (
                f"expected={expected_status} "
                f"actual={actual_status}"
            ),
        )

        # -------------------------------------------------
        # 4. PROPERTY VALIDATION
        # -------------------------------------------------

        suggested_property = item.get(
            "suggested_property"
        )

        property_validation = item.get(
            "suggested_property_validation"
        )

        # The LLM is allowed to return no suggestion.
        # But if it proposes an IFC property,
        # deterministic validation must approve it.
        if suggested_property:

            validation_ok = (
                property_validation is not None
                and property_validation.get("valid")
                is True
            )

            record_check(
                case["case_id"],
                f"{requirement_id} property validation",
                validation_ok,
                (
                    f"suggested={suggested_property} "
                    f"validation={property_validation}"
                ),
            )

        else:

            record_check(
                case["case_id"],
                f"{requirement_id} property validation",
                property_validation is None,
                "no IFC property suggested",
            )


# =========================================================
# FINAL METRICS
# =========================================================

print("\n" + "=" * 80)
print("PIPELINE REGRESSION RESULTS")
print("=" * 80)


total = len(results)

passed = sum(
    1
    for result in results
    if result["passed"]
)

failed = total - passed


print("Total checks:", total)
print("PASS:", passed)
print("FAIL:", failed)

if total:
    print(
        f"Success rate: "
        f"{passed / total:.2%}"
    )


# =========================================================
# FAIL THE PROCESS IF REGRESSION EXISTS
# =========================================================

if failed:

    print("\nREGRESSION DETECTED")

    print("\nFailed checks:")

    for result in results:

        if not result["passed"]:
            print(
                "-",
                result["case_id"],
                "|",
                result["check"],
                "|",
                result["details"],
            )

    sys.exit(1)


print("\nNO REGRESSION DETECTED")
