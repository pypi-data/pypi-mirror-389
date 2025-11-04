import re

from .attr_common import (
    str_to_bin,
    get_handle_class,
    get_key_type,
    get_alg_mode,
    get_usage_key,
    get_write_key,
    get_read_key,
    get_usage_perm,
    get_write_perm,
    get_read_perm,
    get_delete_perm,
    get_use_count,
    get_reserved_58,
    get_exportable,
    get_lockable,
    get_access_limit,
    get_reserved_62,
)
from .attr_crl_property import get_crl_properties
from .attr_data_property import get_data_properties
from .attr_extractedcert_property import get_extracted_properties
from .attr_fca_property import get_fca_properties
from .attr_privkey_property import get_private_properties
from .attr_pubkey_property import get_public_properties
from .attr_symkey_property import get_symmetric_properties


_handle_property_map = {
    "crl": get_crl_properties,
    "data": get_data_properties,
    "extracted": get_extracted_properties,
    "fce": get_fca_properties,
    "fca": get_fca_properties,
    "private": get_private_properties,
    "public": get_public_properties,
    "symmetric": get_symmetric_properties,
}


def get_handle_property(value, d):
    """
    Function will invoke handle property api based on the handle class
    Ex :
    -->get_private_properties(value)
    -->get_public_properties(value)
    """
    func = _handle_property_map.get(d["handle_class"].split(" ")[0].lower(), None)
    if func is not None:
        return func(value)
    else:
        raise ValueError(f'Unable to part {d["handle_class"]} properties')


def decode_attribute(attr):
    # Dict hold the decoded attribute informations
    attr_info = {}
    # handle_properties holds the bit length info of attribute fields
    # Don't remove reserved fields in below list
    handle_properties = [
        ("handle_class", 3, get_handle_class),
        ("key_type", 4, get_key_type),
        ("alg_mode", 1, get_alg_mode),
        ("handle_property", 16, get_handle_property),
        ("usage_key", 8, get_usage_key),
        ("write_key", 8, get_write_key),
        ("read_key", 8, get_read_key),
        ("usage_perm", 2, get_usage_perm),
        ("write_perm", 2, get_write_perm),
        ("read_perm", 2, get_read_perm),
        ("delete_perm", 2, get_delete_perm),
        ("use_count", 2, get_use_count),
        ("reserved_58", 1, get_reserved_58),
        ("exportable", 1, get_exportable),
        ("lockable", 1, get_lockable),
        ("access_limit", 2, get_access_limit),
        ("reserved_62", 1, get_reserved_62),
    ]

    attr_bin = str_to_bin(attr)
    for name, bitlen, func in handle_properties:
        bits = attr_bin[-abs(bitlen) :]
        attr_bin = attr_bin[: -abs(bitlen)]
        # Alg mode and handle_property function need key type info
        if name == "alg_mode" or name == "handle_property":
            result = func(bits, attr_info)
        else:
            result = func(int(bits, 2))
        attr_info.update({name: result})

    return attr_info


def attribute_info(val):
    attr_info = decode_attribute(val)
    key_property = re.sub(r"[\[{}\]\']", "", str(attr_info.get("handle_property")))
    attr_list = []
    attr_list.append(
        f'{attr_info.get("handle_class")}, '
        f'{attr_info.get("key_type")}, '
        f'{attr_info.get("alg_mode")}, '
        f'Exportable:{attr_info.get("exportable")}, '
        f'Lockable:{attr_info.get("lockable")}, '
        f'Access limit:{attr_info.get("access_limit")}'
    )
    attr_list.append(
        f"Key Permission : "
        f' Usage:{attr_info.get("usage_perm")}, '
        f'Write:{attr_info.get("write_perm")}, '
        f' Read:{attr_info.get("read_perm")}, '
        f'Delete:{attr_info.get("delete_perm")}'
    )
    usage_key = ""
    if attr_info.get("usage_perm") == "Rights":
        usage_key = f'Usage Rights:{attr_info.get("usage_key")}, '
    elif attr_info.get("usage_perm") == "Auth":
        handle = hex(0x8000 | int(attr_info.get("usage_key"), base=16))
        usage_key = f"Usage Auth Handle:{handle}, "

    write_key = ""
    if attr_info.get("write_perm") == "Rights":
        write_key = f'Write Rights:{attr_info.get("write_key")}, '
    elif attr_info.get("write_perm") == "Auth":
        handle = hex(0x8000 | int(attr_info.get("write_key"), base=16))
        write_key = f"Write Auth Handle:{handle}, "

    read_key = ""
    if attr_info.get("read_perm") == "Rights":
        read_key = f'Read Rights:{attr_info.get("read_key")}, '
    elif attr_info.get("read_perm") == "Auth":
        handle = hex(0x8000 | int(attr_info.get("read_key"), base=16))
        read_key = f"Read Auth Handle:{handle}, "
    if usage_key != "" or read_key != "" or write_key != "":
        attr_list.append("Key Handles : " + usage_key + write_key + read_key)
    attr_list.append(f"{key_property}")

    return attr_list


__all__ = ["get_handle_property", "decode_attribute", "attribute_info"]
