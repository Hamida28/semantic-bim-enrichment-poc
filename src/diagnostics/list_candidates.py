from dotenv import load_dotenv

from src.core.ifc_extract import extract_elements


load_dotenv()


# ---------------------------------------------------------
# Traduction pour l'AFFICHAGE uniquement.
# Les donnÃ©es originales de l'IFC ne sont jamais modifiÃ©es.
# ---------------------------------------------------------

GERMAN_TO_FRENCH = {
    # PiÃ¨ces
    "Wohnen": "SÃ©jour",
    "Flur": "Couloir",
    "Buero": "Bureau",
    "BÃ¼ro": "Bureau",
    "Schlafzimmer": "Chambre",
    "Bad": "Salle de bain",
    "KÃ¼che": "Cuisine",
    "Kueche": "Cuisine",
    "Galerie": "Galerie",

    # Types / classifications
    "Wand": "Mur",
    "TÃ¼r": "Porte",
    "Tuer": "Porte",
    "Fenster": "FenÃªtre",
    "Decke": "Dalle / plancher",
    "Dach": "Toiture",

    # Layers / catÃ©gories
    "InnenwÃ¤nde": "Murs intÃ©rieurs",
    "Innenwaende": "Murs intÃ©rieurs",
    "AuÃŸenwÃ¤nde": "Murs extÃ©rieurs",
    "Aussenwaende": "Murs extÃ©rieurs",
    "Decken": "Dalles / planchers",
    "DÃ¤cher": "Toitures",
    "Daecher": "Toitures",
}


def translate(value):
    """
    Retourne la valeur IFC originale + sa traduction franÃ§aise.
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
        return f"{name} [FR: Mur intÃ©rieur RDC]"

    if name.startswith("Innentuer"):
        return f"{name} [FR: Porte intÃ©rieure]"

    if name.startswith("EG-Fenster"):
        return f"{name} [FR: FenÃªtre RDC]"

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

