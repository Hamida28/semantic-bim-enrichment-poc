from dotenv import load_dotenv

from src.core.ifc_extract import extract_elements
from src.rag.rag_retriever import (
    build_element_query,
    chunk_specification,
    retrieve_relevant_chunks,
)
from src.core.requirement_classifier import (
    normalize_ifc_entity_family,
)

load_dotenv()

# =========================================================
# GROUND TRUTH DU RETRIEVAL
# =========================================================

TEST_CASES = [

    # PORTES
    {
        "case_id": "DOOR_1",
        "global_id": "1Oms875aH3Wg$9l65H2ZGw",
        "expected_requirement": "REQ-001",
    },
    {
        "case_id": "DOOR_2",
        "global_id": "0pGAjlJMP3ifYPATVF5xAR",
        "expected_requirement": "REQ-001",
    },

    # FENÊTRES
    {
        "case_id": "WINDOW_1",
        "global_id": "1srAI$R4T8ihLXSNHmUSET",
        "expected_requirement": "REQ-002",
    },
    {
        "case_id": "WINDOW_2",
        "global_id": "0B1RwEzzP3CfME5NR$Vqh5",
        "expected_requirement": "REQ-002",
    },

    # MURS
    {
        "case_id": "WALL_1",
        "global_id": "2XPyKWY018sA1ygZKgQPtU",
        "expected_requirement": "REQ-003",
    },
    {
        "case_id": "WALL_2",
        "global_id": "3PfS__Y_DBAfq5naM6zD2Z",
        "expected_requirement": "REQ-003",
    },

    # DALLES
    {
        "case_id": "SLAB_1",
        "global_id": "1pPHnf7cXCpPsNEnQf8_6B",
        "expected_requirement": "REQ-004",
    },
    {
        "case_id": "SLAB_2",
        "global_id": "2RGlQk4xH47RHK93zcTzUL",
        "expected_requirement": "REQ-004",
    },
]


# =========================================================
# CHARGEMENT
# =========================================================

ifc_data = extract_elements(
    "data/model.ifc",
    max_elements=100,
)


with open(
    "data/spec_stress.txt",
    "r",
    encoding="utf-8",
) as file:
    specification = file.read()


chunks = chunk_specification(specification)


# =========================================================
# TEST
# =========================================================

ranks = []


for case in TEST_CASES:

    element = next(
        element
        for element in ifc_data["elements"]
        if element["global_id"] == case["global_id"]
    )

    query = build_element_query(element)

    target_ifc_entity = normalize_ifc_entity_family(
        element["ifc_class"]
    )

    # On récupère toutes les exigences OBJECT
    retrieved = retrieve_relevant_chunks(
        query,
        chunks,
        top_k=9,
        target_ifc_entity=target_ifc_entity,
    )

    retrieved_ids = [
        item["chunk_id"]
        for item in retrieved
    ]

    expected = case["expected_requirement"]

    if expected in retrieved_ids:
        rank = retrieved_ids.index(expected) + 1
    else:
        rank = None

    ranks.append(rank)

    print("\n" + "=" * 70)
    print("TEST:", case["case_id"])
    print("OBJECT:", element["name"])
    print("STRUCTURAL FAMILY:", target_ifc_entity)
    print("EXPECTED:", expected)

    for position, item in enumerate(
        retrieved,
        start=1,
    ):
        print(
            position,
            item["chunk_id"],
            f"{item['similarity_score']:.3f}",
        )

    print("EXPECTED RANK:", rank)


# =========================================================
# RECALL @ K
# =========================================================

print("\n" + "=" * 70)
print("RETRIEVAL METRICS")
print("=" * 70)


for k in [1, 2, 3, 4]:

    found = sum(
        1
        for rank in ranks
        if rank is not None and rank <= k
    )

    total = len(ranks)

    recall = found / total if total else 0

    print(
        f"Recall@{k}: "
        f"{found}/{total} "
        f"({recall:.2%})"
    )