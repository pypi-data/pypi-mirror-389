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

import os

import cryptoauthlib as cal
from cryptography import x509

from tpds.certs.cert import Cert
from tpds.certs.cert_utils import get_backend
from tpds.manifest.tng_manifest import TNGTLSManifest


class TNGManifest:
    def __init__(self):
        pass

    def generate_manifest(self, file=""):
        """
        Method encode the trustngo manifest data and generate
        securesigned element by signing manifest data and
        store it in manifest file

        Args:
            file (str): manifest JSON filename
        """
        tng_cert = self.__get_tng_certs_from_device()
        if not tng_cert:
            raise ValueError("Device doesn't contain correct certificates!!")

        if not file:
            file = "TNGTLS_devices_manifest.json"

        manifest_ca_key = "manifest_ca.key"
        manifest_ca_cert = "manifest_ca.crt"

        manifest = TNGTLSManifest()
        manifest.load_manifest_uniqueid_and_keys()
        manifest.set_provisioning_time(tng_cert.get("device").certificate.not_valid_before)
        manifest.set_certs(
            tng_cert.get("signer").certificate, tng_cert.get("device").certificate, kid="0"
        )
        if os.path.exists(manifest_ca_cert) and os.path.exists(manifest_ca_key):
            signed_se = manifest.encode_manifest(manifest_ca_key, manifest_ca_cert)
        else:
            signed_se = manifest.encode_manifest()
        manifest.write_signed_se_into_file(signed_se.get("signed_se"), file)

    def __get_tng_certs_from_device(self):
        """
        Function check for certificate present in device

        Return:
            return certificate read from device
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


# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == "__main__":
    pass
