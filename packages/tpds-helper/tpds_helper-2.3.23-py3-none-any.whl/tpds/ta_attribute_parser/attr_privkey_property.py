from tpds.ta_attribute_parser import get_bool


def get_pub_key(value):
    return hex(0x8000 + value)


def get_session(value):
    return get_bool(value)


def get_key_gen(value):
    return get_bool(value)


def get_sign_use(value):
    sign_use_details = {0: "None", 1: "All", 2: "Message_Only", 3: "Internal_Only"}
    return sign_use_details.get(value, "Unknown")


def get_agree_use(value):
    agree_use_details = {0: "None", 1: "Any_Target", 2: "RW_Never", 3: "Usage_Key"}
    return agree_use_details.get(value, "Unknown")


def get_private_properties(value):
    property_fields = {
        "Private Key": [
            ("Pub_Key", 8),
            ("Session", 1),
            ("Key_Gen", 1),
            ("Sign_Use", 2),
            ("Agree_Use", 2),
        ]
    }

    # List to hold the private key property field with value
    property_info_l = []

    for field in property_fields["Private Key"]:
        bits = value[-abs(field[1]) :]
        value = value[: -abs(field[1])]
        property_field_value = int(bits, 2)
        if field[0] == "Pub_Key":
            t_d = {"Pub_Key": get_pub_key(property_field_value)}
        elif field[0] == "Session":
            t_d = {"Session": get_session(property_field_value)}
        elif field[0] == "Key_Gen":
            t_d = {"Key_Gen": get_key_gen(property_field_value)}
        elif field[0] == "Sign_Use":
            t_d = {"Sign_Use": get_sign_use(property_field_value)}
        elif field[0] == "Agree_Use":
            t_d = {"Agree_Use": get_agree_use(property_field_value)}

        property_info_l.append(t_d)

    return property_info_l


__all__ = [
    "get_pub_key",
    "get_session",
    "get_key_gen",
    "get_sign_use",
    "get_agree_use",
    "get_private_properties",
]
