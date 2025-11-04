# -*- coding: utf-8 -*-
# 2019 to present - Copyright Microchip Technology Inc. and its subsidiaries.

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

import cryptoauthlib as cal
from cryptography.hazmat.primitives.serialization import Encoding

from tpds.certs.cert_utils import is_signature_valid
from tpds.certs.tflex_certs import TFLEXCerts
from tpds.secure_element import ECC204
from tpds.secure_element.constants import Constants
from tpds.tp_utils import calculate_wpc_digests


class ECC204Provision:
    def __init__(self, interface="i2c", address=0x33):
        self.element = ECC204(interface, address)

    def perform_genkey(self, slot):
        slot_public_key = bytearray(64)
        status = cal.atcab_genkey(slot, slot_public_key)
        assert status == cal.Status.ATCA_SUCCESS, "Genkey failed"
        return slot_public_key

    def perform_slot_write(self, slot, data):
        status = cal.atcab_write_bytes_zone(Constants.ATCA_DATA_ZONE, slot, 0, data, len(data))
        assert status == cal.Status.ATCA_SUCCESS, "Slot Write failed"

    def provision_cert_slot(self, root_cert, signer_cert, device_cert):
        certs = TFLEXCerts("ECC204")
        certs.set_tflex_certificates(root_cert, signer_cert, device_cert)
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

    def provision_wpc_slots(self, root_cert, mfg_cert, puc_cert):
        assert is_signature_valid(
            root_cert, root_cert.public_key()
        ), "Root certificate signature verification failed"
        assert is_signature_valid(
            mfg_cert, root_cert.public_key()
        ), "MFG certificate signature verification failed"
        assert is_signature_valid(
            puc_cert, mfg_cert.public_key()
        ), "PUC certificate signature verification failed"

        root_bytes = root_cert.public_bytes(encoding=Encoding.DER)
        mfg_bytes = mfg_cert.public_bytes(encoding=Encoding.DER)
        puc_bytes = puc_cert.public_bytes(encoding=Encoding.DER)
        wpc_digests = calculate_wpc_digests(root_bytes, mfg_bytes, puc_bytes)

        # Write Slot1 and Slot2 data to device
        # Adjust to Slot1 size (320)
        puc_slot_data = puc_bytes + bytearray(b"\0" * (320 - len(puc_bytes)))
        self.perform_slot_write(1, puc_slot_data)
        self.perform_slot_write(2, wpc_digests.get("chain_digest"))

        return {
            "root_cert": root_bytes,
            "root_digest": wpc_digests.get("root_digest"),
            "mfg_cert": mfg_bytes,
            "puc_cert": puc_bytes,
        }

    def int_to_binary_linear(self, value):
        """
        wrapper function for converting decimal value into monotonic counter
        """
        return self.element.int_to_binary_linear(value)
