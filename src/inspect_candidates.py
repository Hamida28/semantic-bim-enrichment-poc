from src.ifc_extract import extract_elements


TARGET_IDS = {
    # Portes
    "1Oms875aH3Wg$9l65H2ZGw",
    "0pGAjlJMP3ifYPATVF5xAR",

    # Fenêtres
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
    # Pièces
    "Wohnen": "Séjour",
    "Flur": "Couloir",
    "Buero": "Bureau",
    "Büro": "Bureau",
    "Schlafzimmer": "Chambre",
    "Bad": "Salle de bain",
    "Küche": "Cuisine",
    "Galerie": "Galerie",

    # Étages
    "Erdgeschoss": "Rez-de-chaussée",
    "Dachgeschoss": "Étage sous toiture",

    # Catégories
    "Innenwände": "Murs intérieurs",
    "Außenwände": "Murs extérieurs",
    "Decken": "Dalles / planchers",
    "Dächer": "Toitures",

    # Types
    "Wand": "Mur",
    "Tür": "Porte",
    "Fenster": "Fenêtre",
    "Decke": "Dalle / plancher",
    "Dach": "Toiture",

    # Autres
    "Nicht definiert": "Non défini",
    "Bestand": "Existant",
    "Einfach": "Simple",
    "Stahlbeton": "Béton armé",
}


def fr(value):
    if value in (None, ""):
        return "Non renseigné"

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
        "Étage",
        archicad.get("Ursprungsgeschoss"),
    )

    show(
        "Pièce",
        archicad.get("Raumname"),
    )

    show(
        "Depuis la pièce",
        archicad.get("Von Raum"),
    )

    show(
        "Vers la pièce",
        archicad.get("zu Raum"),
    )

    show(
        "Catégorie / couche",
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
        "Protégé",
        archicad.get("Geschützt"),
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
        "Matériau / composition",
        archicad.get(
            "Baustoff / Mehrschichtiger Aufbau / Profil / Schraffur"
        ),
    )

    print("\n--- PROPRIÉTÉS IFC UTILES ---")

    if element["ifc_class"] == "IfcDoor":

        show(
            "Issue de secours",
            door_common.get("FireExit"),
        )

        show(
            "Résistance au feu",
            door_common.get("FireRating"),
        )

        show(
            "Porte extérieure",
            door_common.get("IsExternal"),
        )

        show(
            "Performance acoustique",
            door_common.get("AcousticRating"),
        )

    elif element["ifc_class"] == "IfcWindow":

        show(
            "Fenêtre extérieure",
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
            "Résistance au feu",
            wall_common.get("FireRating"),
        )

        show(
            "Transmission thermique",
            wall_common.get("ThermalTransmittance"),
        )

    elif element["ifc_class"] == "IfcSlab":

        show(
            "Résistance au feu",
            slab_common.get("FireRating"),
        )

        show(
            "Transmission thermique",
            slab_common.get("ThermalTransmittance"),
        )