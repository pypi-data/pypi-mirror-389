def get_num_digest(value):
    return value


def get_crl_properties(value):
    property_fields = {"CRL": [("Num_Digests", 8)]}
    # List to hold the crl property field with value
    property_info_l = []

    for field in property_fields["CRL"]:
        bits = value[-abs(field[1]) :]
        value = value[: -abs(field[1])]
        property_field_value = int(bits, 2)
        if field[0] == "Num_Digests":
            t_d = {"Num_Digests": get_num_digest(property_field_value)}

        property_info_l.append(t_d)

    return property_info_l


__all__ = ["get_num_digest", "get_crl_properties"]
