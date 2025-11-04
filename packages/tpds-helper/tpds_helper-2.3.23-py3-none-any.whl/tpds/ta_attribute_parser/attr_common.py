import re


def get_handle_class(value):
    class_details = {
        0: "Public Key",
        1: "Private Key",
        2: "Symmetric Key",
        3: "Data",
        4: "Extracted Certificate",
        5: "Reserved",
        6: "FCA Group",
        7: "CRL",
    }
    return class_details.get(value, "Unknown")


def get_key_type(value):
    key_type_details = {
        0: "ECC P256",
        1: "ECC P224",
        2: "ECC P384",
        4: "RSA 1024",
        5: "RSA 2048",
        6: "RSA 3072",
        8: "HMAC-SHA256",
        9: "SECP256K1",
        10: "Brainpool 256_R1",
        12: "AES-128",
    }
    return key_type_details.get(value, "Unknown")


def get_alg_mode(value, d):
    alg_mode_details = {
        "ECC": {0: "ECDSA", 1: "ECDH"},
        "RSA": {0: "SSA_1_5", 1: "SSA_PSS"},
        "AES": {0: "CMAC", 1: "GCM"},
        "HMAC": {0: "DIGEST", 1: "HMAC"},
    }
    key_str = re.split(r"\W+", d["key_type"])
    ret_value = alg_mode_details.get(key_str[0], "Unknown")
    if ret_value != "Unknown":
        return alg_mode_details[key_str[0]][int(value, 2)]
    else:
        return ret_value


def get_bool(value):
    bool_details = {0: "Disabled", 1: "Enabled"}
    return bool_details.get(value, "Unknown")


def get_perm(value):
    perm_details = {0: "Never", 1: "Always", 2: "Auth", 3: "Rights"}
    return perm_details.get(value, "Unknown")


def get_usage_perm(value):
    return get_perm(value)


def get_read_perm(value):
    return get_perm(value)


def get_write_perm(value):
    return get_perm(value)


def get_delete_perm(value):
    return get_perm(value)


def get_key(value):
    return hex(value)


def get_usage_key(value):
    return get_key(value)


def get_read_key(value):
    return get_key(value)


def get_write_key(value):
    return get_key(value)


def get_use_count(value):
    use_count_details = {0: "False", 1: "Counter1", 2: "Counter2", 3: "Counter3"}
    return use_count_details.get(value, "Unknown")


def get_exportable(value):
    exportable_details = {0: "False", 1: "True"}
    return exportable_details.get(value, "Unknown")


def get_lockable(value):
    lockable_details = {0: "False", 1: "True"}
    return lockable_details.get(value, "Unknown")


def get_access_limit(value):
    access_limit_details = {0: "Always", 1: "Secure_Boot", 2: "One_Time_Clear", 3: "One_Time_Set"}
    return access_limit_details.get(value, "Unknown")


def get_reserved_58(value):
    pass


def get_reserved_62(value):
    pass


def str_to_bin(attr):
    """
    Convert 8 byte attribute string to bin string
    """
    attr_b = list(bytearray.fromhex(attr))
    bin_byte_l = []
    for byte in attr_b:
        bin_byte_l.append(bin(byte).replace("0b", "").zfill(8))
    bin_byte_l.reverse()
    attr_bin_value = "".join([str(elem) for elem in bin_byte_l])
    return attr_bin_value


__all__ = [
    "get_handle_class",
    "get_key_type",
    "get_alg_mode",
    "get_bool",
    "get_perm",
    "get_usage_perm",
    "get_read_perm",
    "get_write_perm",
    "get_delete_perm",
    "get_key",
    "get_usage_key",
    "get_read_key",
    "get_write_key",
    "get_use_count",
    "get_exportable",
    "get_lockable",
    "get_access_limit",
    "get_reserved_58",
    "get_reserved_62",
    "str_to_bin",
]
