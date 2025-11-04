from tpds.cert_tools import cert_utils


def get_backend():
    return cert_utils.get_backend()


def get_org_name(name):
    return cert_utils.get_org_name(name)


def get_device_sn_cert(cert, find_value="0123"):
    return cert_utils.get_device_sn_cert(cert, find_value)


def get_ca_status(cert):
    return cert_utils.get_ca_status(cert)


def random_cert_sn(size):
    return cert_utils.random_cert_sn(size)


def pubkey_cert_sn(size, builder, use_extended_date: bool = False):
    return cert_utils.pubkey_cert_sn(size, builder, use_extended_date)


def is_key_file_password_protected(key_filename):
    return cert_utils.is_key_file_password_protected(key_filename)


def add_signer_extensions(builder, public_key=None, authority_cert=None):
    return cert_utils.add_signer_extensions(builder, public_key, authority_cert)


def get_device_sn_number(device_sn, prefix="sn"):
    return cert_utils.get_device_sn_number(device_sn, prefix)


def get_device_public_key(device_public_key):
    return cert_utils.get_device_public_key(device_public_key)


def get_certificate_thumbprint(cert):
    return cert_utils.get_certificate_thumbprint(cert)


def get_certificate_CN(cert):
    return cert_utils.get_certificate_CN(cert)


def get_certificate_issuer_CN(cert):
    return cert_utils.get_certificate_issuer_CN(cert)


def get_certificate_tbs(cert):
    return cert_utils.get_certificate_tbs(cert)


def get_cert_content(certificate):
    return cert_utils.get_cert_content(certificate)


def get_cert_print_bytes(cert):
    return cert_utils.get_cert_print_bytes(cert)


def is_signature_valid(certificate, public_key):
    return cert_utils.is_signature_valid(certificate, public_key)


__all__ = [
    "get_backend",
    "get_org_name",
    "get_device_sn_cert",
    "get_ca_status",
    "random_cert_sn",
    "pubkey_cert_sn",
    "is_key_file_password_protected",
    "add_signer_extensions",
    "get_device_sn_number",
    "get_device_public_key",
    "get_certificate_thumbprint",
    "get_certificate_CN",
    "get_certificate_issuer_CN",
    "get_certificate_tbs",
    "get_cert_content",
    "get_cert_print_bytes",
    "is_signature_valid",
]
