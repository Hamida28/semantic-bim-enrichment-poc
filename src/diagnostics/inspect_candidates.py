from src.core.ifc_extract import extract_elements


TARGET_IDS = {
    # Portes
    "1Oms875aH3Wg$9l65H2ZGw",
    "0pGAjlJMP3ifYPATVF5xAR",

    # FenÃªtres
    "1srAI$R4T8ihLXSNHmUSET",
    "0B1RwEzzP3CfME5NR$Vqh5",

    # Murs
    "2XPyKWY018sA1ygZKgQPtU",
    "3PfS__Y_DBAfq5naM6zD2Z",

    # Dalles
    "1pPHnf7cXCpPsNEnQf8_6B",
    "2RGlQk4xH47RHK93zcTzUL",
}


TRANSLATIONS = {
    # PiÃ¨ces
    "Wohnen": "SÃ©jour",
    "Flur": "Couloir",
    "Buero": "Bureau",
    "BÃ¼ro": "Bureau",
    "Schlafzimmer": "Chambre",
    "Bad": "Salle de bain",
    "KÃ¼che": "Cuisine",
    "Galerie": "Galerie",

    # Ã‰tages
    "Erdgeschoss": "Rez-de-chaussÃ©e",
    "Dachgeschoss": "Ã‰tage sous toiture",

    # CatÃ©gories
    "InnenwÃ¤nde": "Murs intÃ©rieurs",
    "AuÃŸenwÃ¤nde": "Murs extÃ©rieurs",
    "Decken": "Dalles / planchers",
    "DÃ¤cher": "Toitures",

    # Types
    "Wand": "Mur",
    "TÃ¼r": "Porte",
    "Fenster": "FenÃªtre",
    "Decke": "Dalle / plancher",
    "Dach": "Toiture",

    # Autres
    "Nicht definiert": "Non dÃ©fini",
    "Bestand": "Existant",
    "Einfach": "Simple",
    "Stahlbeton": "BÃ©ton armÃ©",
}


def fr(value):
    if value in (None, ""):
        return "Non renseignÃ©"

    return TRANSLATIONS.get(str(value), value)


def show(label, value):
    print(f"{label}: {fr(value)}")


ifc_data = extract_elements(
    "data/model.ifc",
    max_elements=100,
)


for element in ifc_data["elements"]:

    if element["global_id"] not in TARGET_IDS:
        continue

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

    wall_common = properties.get(
        "Pset_WallCommon",
        {},
    )

    slab_common = properties.get(
        "Pset_SlabCommon",
        {},
    )

    print("\n" + "=" * 70)

    print("OBJET:", element["name"])
    print("CLASSE IFC:", element["ifc_class"])
    print("GLOBAL ID:", element["global_id"])

    print("\n--- CONTEXTE BIM ---")

    show(
        "Ã‰tage",
        archicad.get("Ursprungsgeschoss"),
    )

    show(
        "PiÃ¨ce",
        archicad.get("Raumname"),
    )

    show(
        "Depuis la piÃ¨ce",
        archicad.get("Von Raum"),
    )

    show(
        "Vers la piÃ¨ce",
        archicad.get("zu Raum"),
    )

    show(
        "CatÃ©gorie / couche",
        archicad.get("Ebene"),
    )

    show(
        "Type Archicad",
        archicad.get("Typ"),
    )

    show(
        "Classification",
        archicad.get("Element-Klassifizierung"),
    )

    show(
        "ProtÃ©gÃ©",
        archicad.get("GeschÃ¼tzt"),
    )

    show(
        "Fonction porteuse",
        archicad.get("Tragende Funktion"),
    )

    show(
        "Localisation / position",
        archicad.get("Lage"),
    )

    show(
        "MatÃ©riau / composition",
        archicad.get(
            "Baustoff / Mehrschichtiger Aufbau / Profil / Schraffur"
        ),
    )

    print("\n--- PROPRIÃ‰TÃ‰S IFC UTILES ---")

    if element["ifc_class"] == "IfcDoor":

        show(
            "Issue de secours",
            door_common.get("FireExit"),
        )

        show(
            "RÃ©sistance au feu",
            door_common.get("FireRating"),
        )

        show(
            "Porte extÃ©rieure",
            door_common.get("IsExternal"),
        )

        show(
            "Performance acoustique",
            door_common.get("AcousticRating"),
        )

    elif element["ifc_class"] == "IfcWindow":

        show(
            "FenÃªtre extÃ©rieure",
            window_common.get("IsExternal"),
        )

        show(
            "Performance acoustique",
            window_common.get("AcousticRating"),
        )

        show(
            "Transmission thermique",
            window_common.get("ThermalTransmittance"),
        )

    elif element["ifc_class"] in {
        "IfcWall",
        "IfcWallStandardCase",
    }:

        show(
            "Performance acoustique",
            wall_common.get("AcousticRating"),
        )

        show(
            "RÃ©sistance au feu",
            wall_common.get("FireRating"),
        )

        show(
            "Transmission thermique",
            wall_common.get("ThermalTransmittance"),
        )

    elif element["ifc_class"] == "IfcSlab":

        show(
            "RÃ©sistance au feu",
            slab_common.get("FireRating"),
        )

        show(
            "Transmission thermique",
            slab_common.get("ThermalTransmittance"),
        )

