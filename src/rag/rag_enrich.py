from __future__ import annotations

import json
import os
import re

from src.core.ifc_property_validator import (
    validate_ifc_property_path,
)

from src.core.requirement_classifier import (
    normalize_ifc_entity_family,
)

from openai import OpenAI

from src.rag.rag_retriever import (
    build_element_query,
    build_reasoning_context,
    chunk_specification,
    retrieve_relevant_chunks,
)


def _extract_json(text: str):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def rag_enrich_element(
    element,
    specification,
    top_k=2,
    extra_context=None,
) -> dict:

    # 1A. Représentation enrichie destinée au retrieval
    retrieval_query = build_element_query(
        element,
        extra_context=extra_context,
    )

    # 1B. Données utilisées comme preuves par le LLM
    reasoning_context = build_reasoning_context(
        element,
        extra_context=extra_context,
    )

    # 2. Découper le document
    chunks = chunk_specification(specification)

    # 2 bis. Identifier la famille IFC
    target_ifc_entity = normalize_ifc_entity_family(
        element["ifc_class"]
    )

    # 3. Retrieval
    retrieved_chunks = retrieve_relevant_chunks(
        query=retrieval_query,
        chunks=chunks,
        top_k=top_k,
        target_ifc_entity=target_ifc_entity,
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
- "missing_context" contains ONLY facts needed to determine
  whether the requirement applies to the BIM object.

- "missing_required_data" contains information, target values,
  ratings, criteria, or properties required to assess or satisfy
  the requirement once its applicability conditions are met.

- Do not put the same missing information in both fields.

- A missing target value, rating, performance level, or required
  property belongs in "missing_required_data", not "missing_context".
- Always identify the source chunk used.
- Return valid JSON only.

- If you suggest a BIM property, use an actual IFC property path
  such as "Pset_DoorCommon.FireRating" when you are confident
  that the standard property exists.
- If you do not know the appropriate IFC property, return null.
- Do not invent generic property names.

BIM OBJECT:

{reasoning_context}

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
      "missing_required_data": [],
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

    # 5. Validate every IFC property suggested by the LLM
    for analysis_item in result.get("analysis", []):

        suggested_property = analysis_item.get(
            "suggested_property"
        )

        if suggested_property:

            validation = validate_ifc_property_path(
                suggested_property,
                element["ifc_class"],
                schema="IFC4",
            )

            analysis_item[
                "suggested_property_validation"
            ] = validation

        else:
            analysis_item[
                "suggested_property_validation"
            ] = None

    # On conserve aussi les passages réellement récupérés
    result["retrieved_sources"] = sources

    return result