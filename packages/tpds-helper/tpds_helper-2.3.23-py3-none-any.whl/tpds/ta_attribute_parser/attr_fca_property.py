from tpds.ta_attribute_parser import get_bool


def get_num_key(value):
    return value


def get_handles(value):
    return get_bool(value)


def get_fca_properties(value):
    property_fields = {"Fast Crypto Key Group": [("Num_Keys", 5), ("Handles", 1)]}
    # List to hold the Fca property field with value----#
    property_info_l = []

    for field in property_fields["Fast Crypto Key Group"]:
        bits = value[-abs(field[1]) :]
        value = value[: -abs(field[1])]
        property_field_value = int(bits, 2)
        if field[0] == "Num_Keys":
            t_d = {"Num_Keys": get_num_key(property_field_value)}
        elif field[0] == "Handles":
            t_d = {"Handles": get_handles(property_field_value)}

        property_info_l.append(t_d)

    return property_info_l


__all__ = ["get_num_key", "get_handles", "get_fca_properties"]
