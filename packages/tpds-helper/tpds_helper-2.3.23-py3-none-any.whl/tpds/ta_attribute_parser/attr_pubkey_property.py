from tpds.ta_attribute_parser import get_bool


def get_path_length(value):
    path_length_details = {255: "Unrestricted"}
    return path_length_details.get(value, value)


def get_secure_boot(value):
    return get_bool(value)


def get_crl_sign(value):
    return get_bool(value)


def get_special_only(value):
    return get_bool(value)


def get_root_str(value):
    root_str_details = {0: "False", 3: "True"}
    return root_str_details.get(value, "Unknown")


def get_public_properties(value):
    property_fields = {
        "Public Key": [
            ("Path_Length", 8),
            ("Secure_Boot", 1),
            ("Root", 2),
            ("CRL_Sign", 1),
            ("Special_Only", 1),
        ],
    }

    # List to hold the public key property field with value
    property_info_l = []

    # ----field ex --> ('Path_Length',8)
    for field in property_fields["Public Key"]:
        bits = value[-abs(field[1]) :]
        value = value[: -abs(field[1])]
        property_field_value = int(bits, 2)
        if field[0] == "Path_Length":
            if property_field_value == 255:
                t_d = {"Path_Length": get_path_length(property_field_value)}
            else:
                t_d = {"Path_Length": get_path_length(property_field_value)}
        elif field[0] == "Secure_Boot":
            t_d = {"Secure_Boot": get_secure_boot(property_field_value)}

        elif field[0] == "Root":
            t_d = {"Root": get_root_str(property_field_value)}

        elif field[0] == "CRL_Sign":
            t_d = {"CRL_Sign": get_crl_sign(property_field_value)}

        elif field[0] == "Special_Only":
            t_d = {"Special_Only": get_special_only(property_field_value)}

        property_info_l.append(t_d)

    return property_info_l


__all__ = [
    "get_path_length",
    "get_secure_boot",
    "get_crl_sign",
    "get_special_only",
    "get_root_str",
    "get_public_properties",
]
