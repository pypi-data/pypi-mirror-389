from tpds.ta_attribute_parser import get_bool


def get_granted_right(value):
    return value


def get_sys_usage(value):
    sym_usage_details = {0: "MAC", 1: "ENC", 2: "ANY", 3: "KDF_SHA"}
    return sym_usage_details.get(value, "Unknown")


def get_session_use(value):
    session_use_details = {
        0: {
            "Use_For_Auth": "Never",
            "Encrypted_Session": "NA",
            "Session_Random_Nonce": "NA",
            "Use_For_Transfer": "No",
        },
        1: {
            "Use_For_Auth": "Either",
            "Encrypted_Session": "Optional",
            "Session_Random_Nonce": "Optional",
            "Use_For_Transfer": "No",
        },
        2: {
            "Use_For_Auth": "Either",
            "Encrypted_Session": "Optional",
            "Session_Random_Nonce": "Mandatory",
            "Use_For_Transfer": "No",
        },
        3: {
            "Use_For_Auth": "Either",
            "Encrypted_Session": "Mandatory",
            "Session_Random_Nonce": "Mandatory",
            "Use_For_Transfer": "No",
        },
        4: {
            "Use_For_Auth": "Only",
            "Encrypted_Session": "Mandatory",
            "Session_Random_Nonce": "Mandatory",
            "Use_For_Transfer": "Only",
        },
        5: {
            "Use_For_Auth": "Only",
            "Encrypted_Session": "Optional",
            "Session_Random_Nonce": "Optional",
            "Use_For_Transfer": "No",
        },
        6: {
            "Use_For_Auth": "Only",
            "Encrypted_Session": "Optional",
            "Session_Random_Nonce": "Mandatory",
            "Use_For_Transfer": "No",
        },
        7: {
            "Use_For_Auth": "Only",
            "Encrypted_Session": "Mandatory",
            "Session_Random_Nonce": "Mandatory",
            "Use_For_Transfer": "No",
        },
    }

    return session_use_details.get(value, "Unknown")


def get_key_group_ok(value):
    return get_bool(value)


def get_symmetric_properties(value):
    property_fields = {
        "Symmetric Key": [
            ("Granted_Rights", 8),
            ("Sym_Usage", 2),
            ("Session_Use", 3),
            ("Key_Group_OK", 1),
        ],
    }

    # List to hold the symmetric key property field with value----#
    property_info_l = []
    for field in property_fields["Symmetric Key"]:
        bits = value[-abs(field[1]) :]
        value = value[: -abs(field[1])]
        property_field_value = int(bits, 2)
        if field[0] == "Granted_Rights":
            t_d = {"Granted_Rights": get_granted_right(property_field_value)}
        elif field[0] == "Sym_Usage":
            t_d = {"Sym_Usage": get_sys_usage(property_field_value)}
        elif field[0] == "Session_Use":
            t_d = {"Session_Use": get_session_use(property_field_value)}
        elif field[0] == "Key_Group_OK":
            t_d = {"Sign_Use": get_key_group_ok(property_field_value)}

        property_info_l.append(t_d)

    return property_info_l


__all__ = [
    "get_granted_right",
    "get_sys_usage",
    "get_session_use",
    "get_key_group_ok",
    "get_symmetric_properties",
]
