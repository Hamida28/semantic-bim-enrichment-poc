from pathlib import Path
import json

from dotenv import load_dotenv

from src.ifc_extract import extract_elements
from src.rag_enrich import rag_enrich_element


load_dotenv()


TARGET_GLOBAL_ID = "0pGAjlJMP3ifYPATVF5xAR"


# 1. Lire la maquette IFC
ifc_data = extract_elements("data/model.ifc")


# 2. Retrouver notre porte
element = next(
    element
    for element in ifc_data["elements"]
    if element["global_id"] == TARGET_GLOBAL_ID
)


# 3. Lire les exigences techniques
specification = Path("data/spec.txt").read_text(
    encoding="utf-8"
)


# 4. Lancer le pipeline RAG
result = rag_enrich_element(
    element=element,
    specification=specification,
    top_k=2,
)


# 5. Afficher le résultat
print(
    json.dumps(
        result,
        ensure_ascii=False,
        indent=2,
    )
)


# 6. Sauvegarder le résultat
output_path = Path("output/rag_door.json")

output_path.write_text(
    json.dumps(
        result,
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)

print(f"\nResult saved to: {output_path}")