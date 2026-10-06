from pathlib import Path

from dotenv import load_dotenv

from src.ifc_extract import extract_elements
from src.rag_retriever import (
    build_element_query,
    chunk_specification,
    retrieve_relevant_chunks,
)


load_dotenv()


# Porte que nous utilisons depuis le début
TARGET_GLOBAL_ID = "0pGAjlJMP3ifYPATVF5xAR"


# 1. Lire le fichier IFC
ifc_data = extract_elements("data/model.ifc")


# 2. Retrouver automatiquement notre porte
element = next(
    element
    for element in ifc_data["elements"]
    if element["global_id"] == TARGET_GLOBAL_ID
)


# 3. Construire automatiquement la query depuis l'IFC
query = build_element_query(element)


print("=== BIM OBJECT QUERY ===")
print(query)


# 4. Lire le cahier des charges
specification = Path("data/spec.txt").read_text(
    encoding="utf-8"
)


# 5. Découper le document
chunks = chunk_specification(specification)


# 6. Chercher les 2 passages les plus pertinents
results = retrieve_relevant_chunks(
    query=query,
    chunks=chunks,
    top_k=2,
)


print("\n=== RETRIEVAL RESULTS ===")

for result in results:
    print(
        f"""
{result["chunk_id"]}
Score: {result["similarity_score"]:.3f}
Text: {result["text"]}
"""
    )