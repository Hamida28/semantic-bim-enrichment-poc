from dotenv import load_dotenv

from src.ifc_extract import extract_elements


load_dotenv()


# ---------------------------------------------------------
# Traduction pour l'AFFICHAGE uniquement.
# Les données originales de l'IFC ne sont jamais modifiées.
# ---------------------------------------------------------

GERMAN_TO_FRENCH = {
    # Pièces
    "Wohnen": "Séjour",
    "Flur": "Couloir",
    "Buero": "Bureau",
    "Büro": "Bureau",
    "Schlafzimmer": "Chambre",
    "Bad": "Salle de bain",
    "Küche": "Cuisine",
    "Kueche": "Cuisine",
    "Galerie": "Galerie",

    # Types / classifications
    "Wand": "Mur",
    "Tür": "Porte",
    "Tuer": "Porte",
    "Fenster": "Fenêtre",
    "Decke": "Dalle / plancher",
    "Dach": "Toiture",

    # Layers / catégories
    "Innenwände": "Murs intérieurs",
    "Innenwaende": "Murs intérieurs",
    "Außenwände": "Murs extérieurs",
    "Aussenwaende": "Murs extérieurs",
    "Decken": "Dalles / planchers",
    "Dächer": "Toitures",
    "Daecher": "Toitures",
}


def translate(value):
    """
    Retourne la valeur IFC originale + sa traduction française.
    """
    if value in (None, ""):
        return value

    french = GERMAN_TO_FRENCH.get(str(value))

    if french:
        return f"{value} [FR: {french}]"

    return value


def translate_name(name):
    """
    Ajoute une traduction indicative aux noms d'objets allemands.
    """
    if not name:
        return name

    if name.startswith("Wand-Int-ERDG"):
        return f"{name} [FR: Mur intérieur RDC]"

    if name.startswith("Innentuer"):
        return f"{name} [FR: Porte intérieure]"

    if name.startswith("EG-Fenster"):
        return f"{name} [FR: Fenêtre RDC]"

    if name == "Bodenplatte":
        return f"{name} [FR: Dalle de sol / dalle basse]"

    if name.startswith("Dach"):
        return f"{name} [FR: Toiture]"

    return name


ifc_data = extract_elements(
    "data/model.ifc",
    max_elements=100,
)

classes_to_show = {
    "IfcDoor",
    "IfcWindow",
    "IfcWall",
    "IfcWallStandardCase",
    "IfcSlab",
}

counts = {}


for element in ifc_data["elements"]:

    ifc_class = element["ifc_class"]

    if ifc_class not in classes_to_show:
        continue

    counts.setdefault(ifc_class, 0)

    # Maximum 3 objets de chaque classe
    if counts[ifc_class] >= 3:
        continue

    counts[ifc_class] += 1

    print("\n" + "=" * 70)

    print("GLOBAL ID:", element["global_id"])
    print("CLASS:", element["ifc_class"])
    print("NAME:", translate_name(element["name"]))

    properties = element.get("properties", {})

    archicad = properties.get(
        "ArchiCADProperties",
        {},
    )

    door_common = properties.get(
        "Pset_DoorCommon",
        {},
    )

    window_common = properties.get(
        "Pset_WindowCommon",
        {},
    )

    print("Room:", translate(archicad.get("Raumname")))
    print("From room:", translate(archicad.get("Von Raum")))
    print("To room:", translate(archicad.get("zu Raum")))

    print(
        "Classification:",
        translate(archicad.get("Element-Klassifizierung")),
    )

    print(
        "Layer:",
        translate(archicad.get("Ebene")),
    )

    print(
        "FireExit:",
        door_common.get("FireExit"),
    )

    print(
        "Door FireRating:",
        door_common.get("FireRating"),
    )

    print(
        "Window AcousticRating:",
        window_common.get("AcousticRating"),
    )