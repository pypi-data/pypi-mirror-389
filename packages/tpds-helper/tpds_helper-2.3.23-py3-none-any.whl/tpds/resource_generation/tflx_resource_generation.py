# -*- coding: utf-8 -*-
# 2018 to present - Copyright Microchip Technology Inc. and its subsidiaries.

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

import binascii
import os
from base64 import b16encode
from dataclasses import dataclass
from pathlib import Path

import cryptoauthlib as cal
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import PublicFormat

from tpds.certs.cert import Cert
from tpds.certs.cert_utils import get_backend, get_cert_print_bytes, get_org_name
from tpds.certs.certs_backup import CertsBackup
from tpds.certs.tflex_certs import TFLEXCerts
from tpds.manifest.tflx_manifest import TFLXTLSManifest
from tpds.pubkey_validation import DevicePubkeyValidation
from tpds.resource_generation import ResourceGeneration
from tpds.tp_utils.tp_keys import TPAsymmetricKey


@dataclass(frozen=True)
class TFLXSlotConfig:
    tflex_slot_config = {
        0: {
            "type": "private",
            "generate_resource": False,
            "description": "Permanent Private key, no generation is allowed",
        },
        1: {
            "type": "private",
            "generate_resource": False,
            "description": "Permanent Private key, no generation is allowed",
        },
        2: {
            "type": "private",
            "generate_resource": True,
            "description": "Private key and key is generated internally",
        },
        3: {
            "type": "private",
            "generate_resource": True,
            "description": "Private key and key is generated internally",
        },
        4: {
            "type": "private",
            "generate_resource": True,
            "description": "Private key and key is generated internally",
        },
        6: {
            "type": "secret",
            "generate_resource": True,
            "description": "Secret key and key is generated and programmed",
        },
        5: {
            "type": "secret",
            "generate_resource": True,
            "enc_key": int(6),
            "description": "Secret key with writes using encrypted key",
        },
        7: {
            "type": "secureboot digest",
            "generate_resource": False,
            "description": "Secureboot digest and no key generation allowed",
        },
        8: {
            "type": "reserved",
            "generate_resource": False,
            "description": "Reserved and no key generation allowed",
        },
        9: {
            "type": "secret",
            "generate_resource": True,
            "description": "Secret key and key is generated and programmed",
        },
        10: {
            "type": "certificate",
            "generate_resource": False,
            "description": "Certificate slot and no key generation is allowed",
        },
        11: {
            "type": "certificate",
            "generate_resource": False,
            "description": "Certificate slot and no key generation is allowed",
        },
        12: {
            "type": "certificate",
            "generate_resource": False,
            "description": "Certificate slot and no key generation is allowed",
        },
        13: {
            "type": "public",
            "generate_resource": True,
            "description": "Public key and key is generated and programmed",
        },
        14: {
            "type": "public",
            "pubinvalid": True,
            "auth_key": 13,
            "generate_resource": True,
            "description": "Public key and key is generated and programmed",
        },
        15: {
            "type": "public",
            "generate_resource": True,
            "description": "Public key and key is generated and programmed",
        },
    }


class TFLXResources(ResourceGeneration):
    """Class generates all the TrustFLEX resources.

    Args:
        ResourceGeneration: Base class.
    """

    def __init__(self):
        self.serial_number = bytearray()
        assert (
            cal.atcab_read_serial_number(self.serial_number) == cal.Status.ATCA_SUCCESS
        ), "Reading Serial number is failed"

    def generate_all(self):
        """Method to generate all the TrustFLEX resources."""
        for slot, tflex_slot_config in TFLXSlotConfig().tflex_slot_config.items():
            if tflex_slot_config["generate_resource"]:
                if tflex_slot_config.get("type") == "secret":
                    # Check for encryption key if any
                    enc_slot = tflex_slot_config.get("enc_key", None)
                    enc_key = Path("slot_{}_secret_key.pem".format(enc_slot)) if enc_slot else None

                    # Get the file to retain
                    secret_key = Path("slot_{}_secret_key.pem".format(slot))

                    assert (
                        self.load_secret_key(slot, secret_key, enc_slot, enc_key)
                        == cal.Status.ATCA_SUCCESS
                    ), "Loading secret key into slot{} failed".format(slot)

                elif tflex_slot_config.get("type") == "private":
                    assert (
                        self.generate_private_key(slot) == cal.Status.ATCA_SUCCESS
                    ), "Generating private key for slot{} failed".format(slot)

                elif tflex_slot_config.get("type") == "public":
                    if "pubinvalid" in tflex_slot_config:
                        self.process_pubinvalid_slot(tflex_slot_config.get("auth_key"), slot)
                    else:
                        # Get the file to retain
                        public_key = Path("slot_{}_ecc_public_key.pem".format(slot))
                        if not os.path.exists(public_key):
                            public_key = None

                        assert (
                            self.load_public_key(slot, public_key) == cal.Status.ATCA_SUCCESS
                        ), "Loading public key into slot{} failed".format(slot)

            print("Slot {}: {}".format(slot, tflex_slot_config["description"]))

    def process_pubinvalid_slot(self, auth_key_slot, pub_key_slot):
        """Method generates public key into corresponding slot.

        Args:
            auth_key_slot (int): Authority private key slot.
            pub_key_slot (int): Public key slot
        """
        auth_key = Path("slot_{}_ecc_private_key.pem".format(auth_key_slot))
        key_invalidation = DevicePubkeyValidation(auth_key_slot, pub_key_slot)
        if key_invalidation.is_pubkey_validated():
            # invalidate first if it is in validated state
            slot_pub_key = bytearray(64)
            assert (
                cal.atcab_read_pubkey(pub_key_slot, slot_pub_key) == cal.Status.ATCA_SUCCESS
            ), "Reading public key from slot {} failed".format(pub_key_slot)
            key_invalidation.pubkey_invalidate(auth_key, slot_pub_key)

        # Generate new rotating key pair
        private_key = Path("slot_{}_ecc_private_key.pem".format(pub_key_slot))
        public_key = Path("slot_{}_ecc_public_key.pem".format(pub_key_slot))
        asym_key = TPAsymmetricKey()
        asym_key.get_private_pem(private_key)
        asym_key.get_public_pem(public_key)

        # write key into slot
        assert (
            self.load_public_key(pub_key_slot, public_key) == cal.Status.ATCA_SUCCESS
        ), "Loading public key into slot{} failed".format(pub_key_slot)

        # Generate variables required for public key rotation embbeded project
        key_rotation = DevicePubkeyValidation(auth_key_slot, pub_key_slot)
        pubkey_info_file = "slot_{}_public_key_rotation.h".format(pub_key_slot)
        key_rotation.save_resources(auth_key, private_key, pubkey_info_file)

    def backup_mchp_certs(self, mchp_certs):
        """Check if the device contains MCHP certificates,
        and check if they are valid or not.
        """
        if mchp_certs is not None:
            root = mchp_certs.get("root")
            signer = mchp_certs.get("signer")
            device = mchp_certs.get("device")

            print("Verify cert chain...", end="")
            is_chain_valid = (
                root.is_signature_valid(root.certificate.public_key())
                and signer.is_signature_valid(root.certificate.public_key())
                and device.is_signature_valid(signer.certificate.public_key())
            )
            if is_chain_valid:
                print("Valid")
                print("Device contain MCHP certificates")
                print("Take MCHP certs backup...", end="")
                backup_certs = CertsBackup()
                backup_certs.store_to_file(mchp_certs, device_sn=self.serial_number)
                print("OK")
            else:
                print("Invalid")
        else:
            print("Device doesn't contain MCHP certificates")

    def restore_mchp_certs(self):
        """This method loads the root, signer and device certificates after checking,
        else shows an error in loading certificates.
        """
        print("Restoring MCHP certificates...", end="")
        mchp_certs = self.get_mchp_backup_certs()
        if mchp_certs:
            certs = TFLEXCerts()
            certs.set_tflex_certificates(
                root_cert=mchp_certs.get("root"),
                signer_cert=mchp_certs.get("signer"),
                device_cert=mchp_certs.get("device"),
            )

            # write signer and device cert into device
            template = certs.get_tflex_py_definitions()
            assert (
                cal.atcacert_write_cert(
                    template.get("signer"),
                    certs.signer.get_certificate_in_der(),
                    len(certs.signer.get_certificate_in_der()),
                )
                == cal.Status.ATCA_SUCCESS
            ), "Loading signer certificate into slot failed"
            assert (
                cal.atcacert_write_cert(
                    template.get("device"),
                    certs.device.get_certificate_in_der(),
                    len(certs.device.get_certificate_in_der()),
                )
                == cal.Status.ATCA_SUCCESS
            ), "Loading device certificate into slot failed"
            print("OK")

            # print the certificates
            print(
                get_cert_print_bytes(
                    certs.root.certificate.public_bytes(encoding=serialization.Encoding.PEM)
                )
            )
            print(
                get_cert_print_bytes(
                    certs.signer.certificate.public_bytes(encoding=serialization.Encoding.PEM)
                )
            )
            print(
                get_cert_print_bytes(
                    certs.device.certificate.public_bytes(encoding=serialization.Encoding.PEM)
                )
            )
        else:
            print("MCHP backup certs are not found")

    def generate_custom_pki(self, org_name, prepend_sn=None):
        """Methos builds all the required certificates(i.e. root, signer, device).

        Args:
            org_name (str): Organization Namee
        """
        certs = TFLEXCerts()
        root_crt_file = "root_crt.crt"
        root_key_file = "root_key.key"
        if os.path.exists(root_crt_file) and os.path.exists(root_key_file):
            root_crt = Cert()
            root_crt.set_certificate(root_crt_file)
            root_key = TPAsymmetricKey(root_key_file)
            is_root_valid = (
                root_crt.is_signature_valid(root_key.get_public_key())
                and get_org_name(root_crt.certificate.subject) == org_name
            )
        else:
            is_root_valid = False

        if is_root_valid:
            certs.set_tflex_certificates(root_cert=root_crt_file)
            certs.root.key.set_private_key(root_key_file)
        else:
            certs.build_root(org_name=org_name)
            certs.root.key.get_private_pem(root_key_file)
            Path(root_crt_file).write_bytes(certs.root.get_certificate_in_pem())

        signer_crt_file = "signer_FFFF.crt"
        signer_key_file = "signer_FFFF.key"
        if os.path.exists(signer_crt_file) and os.path.exists(signer_key_file) and is_root_valid:
            signer_crt = Cert()
            signer_crt.set_certificate(signer_crt_file)
            signer_key = TPAsymmetricKey(signer_key_file)

            crt_pubkey = signer_crt.certificate.public_key().public_bytes(
                format=PublicFormat.SubjectPublicKeyInfo, encoding=serialization.Encoding.DER
            )
            signer_pubkey = (
                signer_key.get_private_key()
                .public_key()
                .public_bytes(
                    format=PublicFormat.SubjectPublicKeyInfo, encoding=serialization.Encoding.DER
                )
            )
            is_signer_valid = (
                (crt_pubkey == signer_pubkey)
                and (
                    get_org_name(signer_crt.certificate.subject)
                    == get_org_name(root_crt.certificate.subject)
                )
                and (signer_crt.is_signature_valid(root_key.get_public_key()))
            )
        else:
            is_signer_valid = False

        if is_signer_valid:
            certs.set_tflex_certificates(signer_cert=signer_crt_file)
            certs.signer.key.set_private_key(signer_key_file)
        else:
            certs.build_signer_csr(org_name=org_name)
            certs.build_signer()
            certs.signer.key.get_private_pem(signer_key_file)
            Path(signer_crt_file).write_bytes(certs.signer.get_certificate_in_pem())

        # read serial number and device public key
        device_pubkey = bytearray()
        assert (
            cal.atcab_get_pubkey(0, device_pubkey) == cal.Status.ATCA_SUCCESS
        ), "Reading device public key is failed"
        device_crt_file = "device_{}.crt".format(
            str(binascii.hexlify(self.serial_number), "utf-8").upper()
        )

        sn = ""
        if prepend_sn is not None:
            sn = prepend_sn + "-" + b16encode(self.serial_number).decode("ascii")
        else:
            sn = self.serial_number
        certs.build_device(device_sn=sn, device_public_key=device_pubkey, org_name=org_name)
        Path(device_crt_file).write_bytes(certs.device.get_certificate_in_pem())

        # Validate and write the certificate chain
        if certs.is_certificate_chain_valid():
            crt_template = certs.get_tflex_py_definitions()
            certs.save_tflex_c_definitions()
            assert (
                cal.atcacert_write_cert(
                    crt_template["signer"],
                    certs.signer.get_certificate_in_der(),
                    len(certs.signer.get_certificate_in_der()),
                )
                == cal.Status.ATCA_SUCCESS
            ), "Loading signer certificate into slot failed"
            assert (
                cal.atcacert_write_cert(
                    crt_template["device"],
                    certs.device.get_certificate_in_der(),
                    len(certs.device.get_certificate_in_der()),
                )
                == cal.Status.ATCA_SUCCESS
            ), "Loading device certificate into slot failed"

            # print the certificates
            print(
                get_cert_print_bytes(
                    certs.root.certificate.public_bytes(encoding=serialization.Encoding.PEM)
                )
            )
            print(
                get_cert_print_bytes(
                    certs.signer.certificate.public_bytes(encoding=serialization.Encoding.PEM)
                )
            )
            print(
                get_cert_print_bytes(
                    certs.device.certificate.public_bytes(encoding=serialization.Encoding.PEM)
                )
            )

    def get_mchp_backup_certs(self):
        """Method checks for the certificate files exists or not.

        Returns:
        """
        backup_certs = CertsBackup()
        mchp_certs = backup_certs.fetch_from_file(device_sn=self.serial_number)
        return mchp_certs

    def get_mchp_backup_file_names(self):
        """Method returns the certificates file names.

        Returns:
            dict: Dictionary containing the root, signer, device certificate
                  file names.
        """
        root_crt_file = "{}_root.crt".format(
            str(binascii.hexlify(self.serial_number), "utf-8").upper()
        )
        signer_crt_file = "{}_signer.crt".format(
            str(binascii.hexlify(self.serial_number), "utf-8").upper()
        )
        device_crt_file = "{}_device.crt".format(
            str(binascii.hexlify(self.serial_number), "utf-8").upper()
        )

        return {"root": root_crt_file, "signer": signer_crt_file, "device": device_crt_file}

    def get_mchp_certs_from_device(self):
        """
        Function check for MCHP certificate
        If found in device, take backup to system folder
        If found in system folder, restore certificate to device

        Inputs:
            restore     restore the MCHP certificate to device
        """
        try:
            root_cert_der_size = cal.AtcaReference(0)
            assert cal.tng_atcacert_root_cert_size(root_cert_der_size) == cal.Status.ATCA_SUCCESS
            root_cert_der = bytearray(root_cert_der_size.value)
            assert (
                cal.tng_atcacert_root_cert(root_cert_der, root_cert_der_size)
                == cal.Status.ATCA_SUCCESS
            )
            root_cert = x509.load_der_x509_certificate(bytes(root_cert_der), get_backend())

            signer_cert_der_size = cal.AtcaReference(0)
            assert (
                cal.tng_atcacert_max_signer_cert_size(signer_cert_der_size)
                == cal.Status.ATCA_SUCCESS
            )
            signer_cert_der = bytearray(signer_cert_der_size.value)
            assert (
                cal.tng_atcacert_read_signer_cert(signer_cert_der, signer_cert_der_size)
                == cal.Status.ATCA_SUCCESS
            )
            signer_cert = x509.load_der_x509_certificate(bytes(signer_cert_der), get_backend())

            device_cert_der_size = cal.AtcaReference(0)
            assert (
                cal.tng_atcacert_max_device_cert_size(device_cert_der_size)
                == cal.Status.ATCA_SUCCESS
            )
            device_cert_der = bytearray(device_cert_der_size.value)
            assert (
                cal.tng_atcacert_read_device_cert(device_cert_der, device_cert_der_size)
                == cal.Status.ATCA_SUCCESS
            )
            device_cert = x509.load_der_x509_certificate(bytes(device_cert_der), get_backend())

            root = Cert()
            signer = Cert()
            device = Cert()
            root.set_certificate(root_cert)
            signer.set_certificate(signer_cert)
            device.set_certificate(device_cert)

            return {"root": root, "signer": signer, "device": device}

        except Exception as err:
            print(err)
            return None

    def generate_manifest(self, signer_cert, device_cert, file=""):
        """
        Method encode the trustflex manifest data and generate
        securesigned element by signing manifest data and
        store it in manifest file

        Args:
            signer_cert (str): path to signer certificate
            device_cert (str): path to device certificate
            file (str): manifest JSON filename
        """
        if not signer_cert and not device_cert:
            raise ValueError("Signer and device certificate is req to gen manifest")

        signer = Cert()
        device = Cert()
        signer.set_certificate(signer_cert)
        device.set_certificate(device_cert)

        if not file:
            file = "TFLXTLS_devices_manifest.json"

        manifest_ca_key = "manifest_ca.key"
        manifest_ca_cert = "manifest_ca.crt"

        manifest = TFLXTLSManifest()
        manifest.load_manifest_uniqueid_and_keys()
        manifest.set_provisioning_time(device.certificate.not_valid_before)
        manifest.set_certs(signer.certificate, device.certificate, kid="0")
        if os.path.exists(manifest_ca_cert) and os.path.exists(manifest_ca_key):
            signed_se = manifest.encode_manifest(manifest_ca_key, manifest_ca_cert)
        else:
            signed_se = manifest.encode_manifest()
        manifest.write_signed_se_into_file(signed_se.get("signed_se"), file)


__all__ = ["TFLXSlotConfig", "TFLXResources"]

# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == "__main__":
    pass
