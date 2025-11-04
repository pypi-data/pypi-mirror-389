from tpds.ta_attribute_parser import get_bool


def get_size(value):
    return value


def get_template(value):
    return get_bool(value)


def get_data_properties(value):
    property_fields = {"Data": [("Size", 12), ("Template", 1)]}
    # List to hold the data property field with value
    property_info_l = []

    for field in property_fields["Data"]:
        bits = value[-abs(field[1]) :]
        value = value[: -abs(field[1])]
        property_field_value = int(bits, 2)
        if field[0] == "Size":
            t_d = {"Size": get_size(property_field_value)}
        elif field[0] == "Template":
            t_d = {"Template": get_template(property_field_value)}

        property_info_l.append(t_d)

    return property_info_l


__all__ = ["get_size", "get_template", "get_data_properties"]
