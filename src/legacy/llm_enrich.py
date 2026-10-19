from __future__ import annotations

import json
import os
import re
from openai import OpenAI


def _extract_json(text: str):
    text = text.strip()
    # Remove optional Markdown fences.
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def llm_enrich(ifc_data: dict, specification: str) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Copy .env.example to .env and add your key."
        )

    model = os.getenv("OPENAI_MODEL", "gpt-6-luna")
    client = OpenAI(api_key=api_key)

    # Keep the demo intentionally small and auditable.
    compact_elements = [
        {
            "global_id": e["global_id"],
            "ifc_class": e["ifc_class"],
            "name": e["name"],
            "description": e["description"],
            "object_type": e["object_type"],
            "properties": e["properties"],
        }
        for e in ifc_data["elements"][:20]
    ]

    prompt = f"""
You are assisting with a BIM semantic-enrichment proof of concept.

GOAL
Given:
1. a small set of IFC elements extracted from a BIM model;
2. a short technical specification;

identify which written requirements may apply to each IFC element.

IMPORTANT RULES
- Do not invent facts not present in the IFC data or specification.
- A requirement may be linked to multiple elements.
- If the evidence is weak, use confidence "low".
- This is a suggestion layer, not an automatic compliance decision.
- Return valid JSON only. No Markdown.

RETURN THIS SHAPE:
{{
  "elements": [
    {{
      "global_id": "...",
      "ifc_class": "...",
      "applicable_requirements": [
        {{
          "requirement": "exact or concise requirement text",
          "reason": "why it may apply",
          "confidence": "low|medium|high",
          "suggested_property": "optional BIM property name or null",
          "suggested_value": "optional value or null"
        }}
      ]
    }}
  ]
}}

TECHNICAL SPECIFICATION
{specification}

IFC ELEMENTS
{json.dumps(compact_elements, ensure_ascii=False, default=str)}
""".strip()

    response = client.responses.create(
        model=model,
        input=prompt,
    )

    result = _extract_json(response.output_text)
    result["ifc_schema"] = ifc_data["schema"]
    result["method"] = f"llm:{model}"
    return result
