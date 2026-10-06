from __future__ import annotations

import json
import os
import re

from openai import OpenAI

from src.rag_retriever import (
    build_element_query,
    chunk_specification,
    retrieve_relevant_chunks,
)


def _extract_json(text: str):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def rag_enrich_element(
    element: dict,
    specification: str,
    top_k: int = 2,
) -> dict:

    # 1. Construire automatiquement la requête BIM
    query = build_element_query(element)

    # 2. Découper le document
    chunks = chunk_specification(specification)

    # 3. Retrouver seulement les passages pertinents
    retrieved_chunks = retrieve_relevant_chunks(
        query=query,
        chunks=chunks,
        top_k=top_k,
    )

    # 4. Préparer les sources pour le LLM
    sources = [
        {
            "chunk_id": chunk["chunk_id"],
            "text": chunk["text"],
            "similarity_score": chunk["similarity_score"],
        }
        for chunk in retrieved_chunks
    ]

    client = OpenAI()

    model = os.getenv(
        "OPENAI_MODEL",
        "gpt-6-luna",
    )

    prompt = f"""
You are analysing one BIM object.

Your task is to determine whether any of the retrieved
technical requirements may apply to this object.

IMPORTANT:
- Use ONLY the retrieved requirements below.
- Do not invent missing BIM information.
- A retrieved passage is only a candidate, not automatically applicable.
- Classify each requirement using exactly one status:

  "applicable":
  the available BIM evidence supports the requirement's conditions.

  "not_applicable":
  the available BIM evidence clearly shows that the requirement does not concern this object.

  "uncertain":
  the requirement may concern this object, but some necessary information is missing.

- If information is missing, use "uncertain", NOT "not_applicable".
- Always identify the source chunk used.
- Return valid JSON only.

- If you suggest a BIM property, use an actual IFC property path
  such as "Pset_DoorCommon.FireRating" when you are confident
  that the standard property exists.
- If you do not know the appropriate IFC property, return null.
- Do not invent generic property names.

BIM OBJECT:

{query}

RETRIEVED REQUIREMENTS:

{json.dumps(sources, ensure_ascii=False, indent=2)}

Return:

{{
  "global_id": "{element.get('global_id')}",
  "ifc_class": "{element.get('ifc_class')}",
  "analysis": [
    {{
      "source_chunk_id": "...",
      "requirement": "...",
      "status": "applicable|not_applicable|uncertain",
      "reason": "...",
      "missing_context": [],
      "missing_required_data": []
      "confidence": "low|medium|high",
      "suggested_property": null,
      "suggested_value": null
    }}
  ]
}}
"""

    response = client.responses.create(
        model=model,
        input=prompt,
    )

    result = _extract_json(response.output_text)

    # On conserve aussi les passages réellement récupérés
    result["retrieved_sources"] = sources

    return result