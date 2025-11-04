# 2020 to present - Copyright Microchip Technology Inc. and its subsidiaries.

# Subject to your compliance with these terms, you may use Microchip software
# and any derivatives exclusively with Microchip products. It is your
# responsibility to comply with third party license terms applicable to your
# use of third party software (including open source software) that may
# accompany Microchip software.

# THIS SOFTWARE IS SUPPLIED BY MICROCHIP "AS IS". NO WARRANTIES, WHETHER
# EXPRESS, IMPLIED OR STATUTORY, APPLY TO THIS SOFTWARE, INCLUDING ANY IMPLIED
# WARRANTIES OF NON-INFRINGEMENT, MERCHANTABILITY, AND FITNESS FOR A PARTICULAR
# PURPOSE. IN NO EVENT WILL MICROCHIP BE LIABLE FOR ANY INDIRECT, SPECIAL,
# PUNITIVE, INCIDENTAL OR CONSEQUENTIAL LOSS, DAMAGE, COST OR EXPENSE OF ANY
# KIND WHATSOEVER RELATED TO THE SOFTWARE, HOWEVER CAUSED, EVEN IF MICROCHIP
# HAS BEEN ADVISED OF THE POSSIBILITY OR THE DAMAGES ARE FORESEEABLE. TO THE
# FULLEST EXTENT ALLOWED BY LAW, MICROCHIP'S TOTAL LIABILITY ON ALL CLAIMS IN
# ANY WAY RELATED TO THIS SOFTWARE WILL NOT EXCEED THE AMOUNT OF FEES, IF ANY,
# THAT YOU HAVE PAID DIRECTLY TO MICROCHIP FOR THIS SOFTWARE.

import asn1crypto.core
import asn1crypto.keys
import asn1crypto.x509


def diff_offset(base, diff):
    """Return the index where the two parameters differ."""
    base = base.dump()
    diff = diff.dump()
    if len(base) != len(diff):
        raise ValueError("len(base)=%d != len(diff)=%d" % (len(base), len(diff)))
    for i in range(0, len(base)):
        if base[i] != diff[i]:
            return i
    raise ValueError("base and diff are identical")


def sn_location(cert):
    cert_mod = cert.copy()
    sn = bytearray(cert_mod["tbs_certificate"]["serial_number"].contents)
    # Alter the serial number to find offset, but retain encoding size
    sn[0] = 0x01 if sn[0] != 0x01 else 0x02
    cert_mod["tbs_certificate"]["serial_number"] = asn1crypto.core.Integer(
        int().from_bytes(sn, byteorder="big", signed=True)
    )
    return (diff_offset(cert, cert_mod), len(cert["tbs_certificate"]["serial_number"].contents))


def validity_location(cert, name):
    cert_mod = cert.copy()
    time = cert["tbs_certificate"]["validity"][name]
    if time.chosen.tag == asn1crypto.core.UTCTime.tag:
        if time.chosen.native.year >= 2000 and time.chosen.native.year < 2010:
            new_time = time.chosen.native.replace(year=2010)
        else:
            new_time = time.chosen.native.replace(year=2000)
        cert_mod["tbs_certificate"]["validity"][name] = asn1crypto.x509.Time(
            name="utc_time", value=asn1crypto.core.UTCTime(new_time)
        )
    elif time.chosen.tag == asn1crypto.core.GeneralizedTime.tag:
        if time.chosen.native.year >= 2000 and time.chosen.native.year < 3000:
            new_time = time.chosen.native.replace(year=3000)
        else:
            new_time = time.chosen.native.replace(year=2000)
        cert_mod["tbs_certificate"]["validity"][name] = asn1crypto.x509.Time(
            name="general_time", value=asn1crypto.core.GeneralizedTime(new_time)
        )
    else:
        raise ValueError("Unexpected tag value ({}) for validity {}".format(time.chosen.tag, name))
    return (
        diff_offset(cert, cert_mod),
        len(cert["tbs_certificate"]["validity"][name].chosen.contents),
    )


def public_key_location(cert):
    cert_mod = cert.copy()
    public_key = bytearray(cert["tbs_certificate"]["subject_public_key_info"]["public_key"].native)
    # Change the first byte of the public key skipping the key-compression byte
    public_key[1] ^= 0xFF
    cert_mod["tbs_certificate"]["subject_public_key_info"][
        "public_key"
    ] = asn1crypto.keys.ECPointBitString(bytes(public_key))
    return (
        diff_offset(cert, cert_mod),
        len(cert["tbs_certificate"]["subject_public_key_info"]["public_key"].native) - 1,
    )


def name_search_location(cert, name, search):
    cert_mod = cert.copy()
    # Change the first character of the search text for the replacement text
    search = search.encode()
    replace = (b"F" if search[0] != ord(b"F") else b"0") + search[1:]
    name_der = cert["tbs_certificate"][name].dump()
    if search not in name_der:
        raise ValueError('Could not find "{}" in certificate {} name.'.format(search, name))
    cert_mod["tbs_certificate"][name] = asn1crypto.x509.Name().load(
        name_der.replace(search, replace)
    )
    return (diff_offset(cert, cert_mod), len(search))


def name_search_location_last(cert, name, search):
    # Gives offset and length information of certain search string, searched from
    # right to left and finds the first instance.
    cert_mod = cert.copy()
    # Change the first character of the search text for the replacement text
    search = search.encode()
    replace = (b"F" if search[0] != ord(b"F") else b"0") + search[1:]
    name_der = cert["tbs_certificate"][name].dump()
    if search not in name_der:
        raise ValueError('Could not find "{}" in certificate {} name.'.format(search, name))
    cert_mod["tbs_certificate"][name] = asn1crypto.x509.Name().load(
        replace.join(name_der.rsplit(search, 1))
    )
    return (diff_offset(cert, cert_mod), len(search))


def auth_key_id_location(cert):
    cert_mod = cert.copy()
    oid = asn1crypto.x509.ExtensionId("authority_key_identifier")
    is_found = False
    for extension in cert_mod["tbs_certificate"]["extensions"]:
        if extension["extn_id"] == oid:
            is_found = True
            break
    if not is_found:
        return (0, 0)

    # Modify the first byte of the key ID value
    mod_key_id = bytearray(extension["extn_value"].parsed["key_identifier"].native)
    mod_key_id[0] ^= 0xFF
    mod_auth_key_id = extension["extn_value"].parsed.copy()
    mod_auth_key_id["key_identifier"] = asn1crypto.core.OctetString(bytes(mod_key_id))
    extension["extn_value"] = mod_auth_key_id

    return (diff_offset(cert, cert_mod), len(mod_key_id))


def subj_key_id_location(cert):
    cert_mod = cert.copy()
    oid = asn1crypto.x509.ExtensionId("key_identifier")
    is_found = False
    for extension in cert_mod["tbs_certificate"]["extensions"]:
        if extension["extn_id"] == oid:
            is_found = True
            break
    if not is_found:
        return (0, 0)

    # Modify the first byte of the key ID value
    mod_key_id = bytearray(extension["extn_value"].parsed.native)
    mod_key_id[0] ^= 0xFF
    mod_auth_key_id = asn1crypto.core.OctetString(bytes(mod_key_id))
    extension["extn_value"] = mod_auth_key_id

    return (diff_offset(cert, cert_mod), len(mod_key_id))


def signature_location(cert):
    signature_der = cert["signature_value"].dump()
    return (cert.dump().find(signature_der), 64)
    #     len(signature_der))


def tbs_location(cert):
    tbs_der = cert["tbs_certificate"].dump()
    return (cert.dump().find(tbs_der), len(tbs_der))


def cert_search(cert, search):
    return (cert.dump().find(search), len(search))
