from src.core.ifc_property_validator import (
    validate_ifc_property_path,
)


TESTS = [
    (
        "IfcDoor",
        "Pset_DoorCommon.FireRating",
    ),
    (
        "IfcWallStandardCase",
        "Pset_WallCommon.AcousticRating",
    ),
    (
        "IfcWallStandardCase",
        "Pset_WallCommon.FireRating",
    ),
    (
        "IfcSlab",
        "Pset_SlabCommon.FireRating",
    ),

    # Important:
    # le LLM pourrait proposer ceci un jour.
    # On veut savoir si cela existe vraiment.
    (
        "IfcSlab",
        "Pset_SlabCommon.AcousticRating",
    ),

    # Faux volontaire
    (
        "IfcDoor",
        "Pset_DoorCommon.MadeUpRating",
    ),
]


for ifc_class, property_path in TESTS:

    print("\n" + "=" * 70)
    print("IFC CLASS:", ifc_class)
    print("SUGGESTION:", property_path)

    result = validate_ifc_property_path(
        property_path,
        ifc_class,
    )

    for key, value in result.items():
        print(f"{key}: {value}")

