from __future__ import annotations
from src.requirement_classifier import (
    classify_requirement_ifc_entity,
)

import numpy as np
from openai import OpenAI

EMBEDDING_MODEL = "text-embedding-3-small"

LAYER_SEMANTIC_NORMALIZATION = {
    "Außenwände": "external walls",
    "Aussenwaende": "external walls",

    "Innenwände": "internal walls",
    "Innenwaende": "internal walls",

    "Decken": "floor slabs",
    "Dächer": "roofs",
    "Daecher": "roofs",
}

def chunk_specification(text: str) -> list[dict]:
    chunks = []
    requirement_number = 1

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        if line.lower().startswith("technical specification"):
            continue

        if line.startswith("[OBJECT]"):
            scope = "object"
            clean_text = line.replace("[OBJECT]", "", 1).strip()

        elif line.startswith("[PROCESS]"):
            scope = "process"
            clean_text = line.replace("[PROCESS]", "", 1).strip()

        else:
            scope = "unknown"
            clean_text = line

        chunks.append(
            {
                "chunk_id": f"REQ-{requirement_number:03d}",
                "scope": scope,
                "text": clean_text,
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
    target_ifc_entity=None,
) -> list[dict]:

    # 1. Garder uniquement les exigences OBJECT
    chunks = [
        chunk
        for chunk in chunks
        if chunk.get("scope") == "object"
    ]

    # 2. Filtrage structurel selon la famille IFC
    if target_ifc_entity:

        compatible_chunks = []

        for chunk in chunks:

            requirement_entity = (
                classify_requirement_ifc_entity(
                    chunk["text"]
                )
            )

            # Si la règle est compatible avec l'objet,
            # on la garde.
            #
            # Si le classifier n'arrive pas à déterminer
            # sa classe, on la garde aussi par sécurité.
            if (
                requirement_entity is None
                or requirement_entity == target_ifc_entity
            ):
                compatible_chunks.append(chunk)

        chunks = compatible_chunks

    # 3. Embeddings uniquement sur les règles restantes
    chunk_embeddings = embed_texts(
        [chunk["text"] for chunk in chunks]
    )

    query_embedding = embed_texts([query])[0]

    scored_chunks = []

    for chunk, embedding in zip(chunks, chunk_embeddings):
        score = cosine_similarity(
            query_embedding,
            embedding,
        )

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


def build_element_query(
    element: dict,
    extra_context: dict | None = None,
) -> str:
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
        "Ebene",
    ]

    for property_name in useful_properties:
        value = archicad.get(property_name)

        if value not in (None, ""):
            parts.append(
                f"{property_name}: {value}"
            )
            if property_name == "Ebene":
                semantic_value = LAYER_SEMANTIC_NORMALIZATION.get(
                    str(value)
                )

                if semantic_value:
                    parts.append(
                        f"Semantic layer meaning: {semantic_value}"
                    )

    if extra_context:
        parts.append("")
        parts.append("CONTROLLED TEST CONTEXT:")

        for key, value in extra_context.items():
            parts.append(f"{key}: {value}")

    return "\n".join(parts)

def build_reasoning_context(
    element: dict,
    extra_context: dict | None = None,
) -> str:
    """
    Build the evidence given to the LLM for reasoning.

    Important:
    This context contains source BIM information only.
    It does NOT contain semantic normalization added
    specifically for retrieval.
    """

    parts = [
        f"IFC class: {element.get('ifc_class')}",
        f"Name: {element.get('name')}",
    ]

    properties = element.get("properties", {})

    # Standard IFC property sets
    useful_psets = [
        "Pset_DoorCommon",
        "Pset_WindowCommon",
        "Pset_WallCommon",
        "Pset_SlabCommon",
    ]

    for pset_name in useful_psets:
        pset = properties.get(pset_name, {})

        for property_name, value in pset.items():
            if value not in (None, ""):
                parts.append(
                    f"{pset_name}.{property_name}: {value}"
                )

    # Raw ArchiCAD properties only
    # No semantic translation here.
    archicad = properties.get(
        "ArchiCADProperties",
        {},
    )

    useful_properties = [
        "Raumname",
        "Typ",
        "Element-Klassifizierung",
        "Ebene",
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

    # Controlled context is explicit evidence
    # intentionally added by our synthetic tests.
    if extra_context:
        parts.append("")
        parts.append("CONTROLLED TEST CONTEXT:")

        for key, value in extra_context.items():
            parts.append(
                f"{key}: {value}"
            )

    return "\n".join(parts)