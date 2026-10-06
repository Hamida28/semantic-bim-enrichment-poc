from __future__ import annotations

import numpy as np
from openai import OpenAI

EMBEDDING_MODEL = "text-embedding-3-small"


def chunk_specification(text: str) -> list[dict]:
    chunks = []

    requirement_number = 1

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        if line.lower().startswith("technical specification"):
            continue

        chunks.append(
            {
                "chunk_id": f"REQ-{requirement_number:03d}",
                "text": line,
            }
        )

        requirement_number += 1

    return chunks


def embed_texts(texts: list[str]) -> list[list[float]]:
    client = OpenAI()

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )

    return [item.embedding for item in response.data]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    vector_a = np.array(a)
    vector_b = np.array(b)

    return float(
        np.dot(vector_a, vector_b)
        / (np.linalg.norm(vector_a) * np.linalg.norm(vector_b))
    )


def retrieve_relevant_chunks(
    query: str,
    chunks: list[dict],
    top_k: int = 2,
) -> list[dict]:

    chunk_embeddings = embed_texts(
        [chunk["text"] for chunk in chunks]
    )

    query_embedding = embed_texts([query])[0]

    scored_chunks = []

    for chunk, embedding in zip(chunks, chunk_embeddings):
        score = cosine_similarity(query_embedding, embedding)

        scored_chunks.append(
            {
                **chunk,
                "similarity_score": score,
            }
        )

    scored_chunks.sort(
        key=lambda item: item["similarity_score"],
        reverse=True,
    )

    return scored_chunks[:top_k]


def build_element_query(element: dict) -> str:
    """
    Construit une description concise de l'objet BIM
    avec uniquement les informations utiles au retrieval.
    """

    parts = [
        f"IFC class: {element.get('ifc_class')}",
        f"Name: {element.get('name')}",
    ]

    properties = element.get("properties", {})

    # Propriétés IFC standard intéressantes
    door_common = properties.get("Pset_DoorCommon", {})

    for property_name in [
        "FireExit",
        "FireRating",
        "IsExternal",
        "AcousticRating",
    ]:
        value = door_common.get(property_name)

        if value not in (None, ""):
            parts.append(
                f"Pset_DoorCommon.{property_name}: {value}"
            )

    # Quelques propriétés métier utiles provenant d'ArchiCAD
    archicad = properties.get("ArchiCADProperties", {})

    useful_properties = [
        "Raumname",
        "Typ",
        "Element-Klassifizierung",
        "Von Raum",
        "zu Raum",
        "Baustoff / Mehrschichtiger Aufbau / Profil / Schraffur",
    ]

    for property_name in useful_properties:
        value = archicad.get(property_name)

        if value not in (None, ""):
            parts.append(
                f"{property_name}: {value}"
            )

    return "\n".join(parts)