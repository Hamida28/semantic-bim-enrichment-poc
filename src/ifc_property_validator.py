import ifcopenshell.util.pset


def validate_ifc_property_path(
    property_path: str | None,
    ifc_class: str,
    schema: str = "IFC4",
) -> dict:

    if not property_path:
        return {
            "property_path": property_path,
            "valid": False,
            "reason": "No property suggested.",
        }

    if "." not in property_path:
        return {
            "property_path": property_path,
            "valid": False,
            "reason": "Invalid property path format.",
        }

    pset_name, property_name = property_path.split(".", 1)

    templates = ifcopenshell.util.pset.PsetQto(schema)

    # Does this standard Pset exist?
    pset_template = templates.get_by_name(pset_name)

    if pset_template is None:
        return {
            "property_path": property_path,
            "valid": False,
            "reason": f"{pset_name} is not a standard {schema} property set.",
        }

    # Is this Pset applicable to this IFC class?
    applicable_psets = templates.get_applicable_names(
        ifc_class,
        pset_only=True,
    )

    pset_applicable = pset_name in applicable_psets

    # Does the property actually exist inside the Pset?
    property_names = {
        prop.Name
        for prop in (pset_template.HasPropertyTemplates or [])
    }

    property_exists = property_name in property_names

    valid = pset_applicable and property_exists

    if not property_exists:
        reason = (
            f"{property_name} does not exist "
            f"in {pset_name}."
        )

    elif not pset_applicable:
        reason = (
            f"{pset_name} exists but is not applicable "
            f"to {ifc_class}."
        )

    else:
        reason = (
            f"{property_path} is a valid standard "
            f"{schema} property for {ifc_class}."
        )

    return {
        "property_path": property_path,
        "ifc_class": ifc_class,
        "pset_exists": True,
        "pset_applicable": pset_applicable,
        "property_exists": property_exists,
        "valid": valid,
        "reason": reason,
    }