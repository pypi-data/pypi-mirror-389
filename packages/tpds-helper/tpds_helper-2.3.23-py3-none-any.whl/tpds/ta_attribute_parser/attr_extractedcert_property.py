from tpds.ta_attribute_parser import get_bool


def get_granted_rights(value):
    return value


def get_secure_boot(value):
    return get_bool(value)


def get_ca_ok(value):
    return get_bool(value)


def get_ca_parent(value):
    return get_bool(value)


def get_crl_sign(value):
    return get_bool(value)


def get_special_only(value):
    return get_bool(value)


def get_extracted_properties(value):
    property_fields = {
        "Extracted Certificate": [
            ("Granted_Rights", 8),
            ("Secure_Boot", 1),
            ("CA_OK", 1),
            ("CA_Parent", 1),
            ("CRL_Sign", 1),
            ("Special_Only", 1),
        ]
    }

    # List to hold extracted property field with value----#
    property_info_l = []

    for field in property_fields["Extracted Certificate"]:
        bits = value[-abs(field[1]) :]
        value = value[: -abs(field[1])]
        property_field_value = int(bits, 2)
        if field[0] == "Granted_Rights":
            t_d = {"Granted_Rights": get_granted_rights(property_field_value)}
        elif field[0] == "Secure_Boot":
            t_d = {"Secure_Boot": get_secure_boot(property_field_value)}
        elif field[0] == "CA_OK":
            t_d = {"CA_OK": get_ca_ok(property_field_value)}
        elif field[0] == "CA_Parent":
            t_d = {"CA_Parent": get_ca_parent(property_field_value)}
        elif field[0] == "CRL_Sign":
            t_d = {"CRL_Sign": get_crl_sign(property_field_value)}
        elif field[0] == "Special_Only":
            t_d = {"Special_Only": get_special_only(property_field_value)}

        property_info_l.append(t_d)

    return property_info_l


__all__ = [
    "get_granted_rights",
    "get_secure_boot",
    "get_ca_ok",
    "get_ca_parent",
    "get_crl_sign",
    "get_special_only",
    "get_extracted_properties",
]
