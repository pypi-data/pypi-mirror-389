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
from cryptoauthlib.device import Atecc608Config

import tpds.tp_utils

from .pubkey_validation import PubKeyValidation


class DevicePubkeyValidation(PubKeyValidation):
    def __init__(self, auth_pubkey_slot, pubkey_slot):
        super().__init__()
        self.__set_device_info(auth_pubkey_slot, pubkey_slot)

    def pubkey_invalidate(self, auth_key, public_key):
        """
        Method invalidate the public key present in the slot
        Inputs:
              auth_key          Authority private key to sign
                                the pubkey digest
              public_key        public key to be invalidated
        outputs:
            is_invalidated      True if invalidated else False
        """
        self.authorize_public_key(auth_key, public_key, True)
        assert cal.atcab_nonce(self.nonce) == cal.Status.ATCA_SUCCESS, "Loading Nonce failed"

        assert (
            cal.atcab_genkey_base(0x10, self.device_info.get("pubkey_slot"), other_data=b"\x00" * 3)
            == cal.Status.ATCA_SUCCESS
        ), "Genkey digest calculation on device failed"

        is_invalidated = cal.AtcaReference(False)
        assert (
            cal.atcab_verify_invalidate(
                self.device_info.get("pubkey_slot"),
                self.signature,
                self.sign_internal_other_data,
                is_invalidated,
            )
            == cal.Status.ATCA_SUCCESS
        ), "Slot verification for invalidate failed"

        assert bool(
            is_invalidated.value
        ), "Verify Invalidate command is success, \
            but invalidation failed"

    def pubkey_validate(self, auth_key, public_key):
        """
        Method validate the public key to use for the cryptographic function
        Inputs:
              auth_key        Authority validation private key
              public_key      public key to be validated
        Outputs:
              is_validated    True if validated else False
        """
        self.authorize_public_key(auth_key, public_key, False)
        assert cal.atcab_nonce(self.nonce) == cal.Status.ATCA_SUCCESS, "Loading Nonce failed"

        assert (
            cal.atcab_genkey_base(0x10, self.device_info.get("pubkey_slot"), other_data=b"\x00" * 3)
            == cal.Status.ATCA_SUCCESS
        ), "Genkey digest calculation on device failed"

        is_validated = cal.AtcaReference(False)
        assert (
            cal.atcab_verify_validate(
                self.device_info.get("pubkey_slot"),
                self.signature,
                self.sign_internal_other_data,
                is_validated,
            )
            == cal.Status.ATCA_SUCCESS
        ), "Slot verification for validate failed"

        assert bool(
            is_validated.value
        ), "Verify validate command is success, \
            but validation failed"

    def is_pubkey_validated(self):
        """
        Method check the public key validation state
        Inputs:
              pubkey_slot         public key slot
        Outputs:
              validation_state    True if public key is valid else False
        """
        public_key_control_bytes = bytearray(4)
        assert (
            cal.atcab_read_zone(
                0x02,
                self.device_info.get("pubkey_slot"),
                0,
                0,
                public_key_control_bytes,
                len(public_key_control_bytes),
            )
            == cal.Status.ATCA_SUCCESS
        ), "Reading public key validation state - failed"

        return public_key_control_bytes[0] == 0x50

    def __set_device_info(self, auth_pubkey_slot, pubkey_slot):
        """
        Method set the device information to perform public key validation
        Input:
            auth_pubkey_slot          authority public key slot
            pubkey_slot               public key slot for (in)validation
        """
        device_config = bytearray()
        assert (
            cal.atcab_read_config_zone(device_config) == cal.Status.ATCA_SUCCESS
        ), "Reading device configuration is failed"

        super().set_device_info(
            Atecc608Config.from_buffer(device_config), auth_pubkey_slot, pubkey_slot
        )

    def save_resources(self, auth_key, rotating_key, file="pubkey_rotation.h"):
        """Method saves the resource files.

        Input:
            auth_key                  Authority valid private key.
            rotating_key ([type]):    New rotating key
            file (str, optional):     File name to save the resources.
                                      Defaults to 'pubkey_rotation.h'.
        """
        auth_key = tpds.tp_utils.TPAsymmetricKey(auth_key)
        rotating_key = tpds.tp_utils.TPAsymmetricKey(rotating_key)

        with open(file, "w") as f:
            # Calculate invalidate signature and nonce to invalidate public key
            self.authorize_public_key(
                auth_key.get_private_key(), rotating_key.public_key_bytes, False
            )

            f.write("#ifndef _PUBKEY_ROTATION_H\n")
            f.write("#define _PUBKEY_ROTATION_H\n\n")
            f.write('#include "cryptoauthlib.h"\n\n')
            f.write("#ifdef __cplusplus\n")
            f.write('extern "C" {\n')
            f.write("#endif\n\n")

            f.write("uint8_t validated_nonce[] = {\n")
            f.write(tpds.tp_utils.get_c_hex_bytes(self.pubkey_info.get("auth_nonce")) + "};\n\n")

            f.write("uint8_t validated_signature[] = {\n")
            f.write(
                tpds.tp_utils.get_c_hex_bytes(self.pubkey_info.get("auth_signature")) + "};\n\n"
            )

            # calculate digest and signature to verify new rotating public key
            message_digest = os.urandom(32)
            signature = tpds.tp_utils.sign_on_host(message_digest, rotating_key.get_private_key())
            f.write("uint8_t rotating_digest[] = {\n")
            f.write(tpds.tp_utils.get_c_hex_bytes(message_digest) + "};\n\n")

            f.write("uint8_t rotating_signature[] = {\n")
            f.write(tpds.tp_utils.get_c_hex_bytes(signature) + "};\n\n")

            # Calculate invalidate signature and nonce to invalidate public key
            self.authorize_public_key(
                auth_key.get_private_key(), rotating_key.public_key_bytes, True
            )

            f.write("uint8_t invalidated_nonce[] = {\n")
            f.write(tpds.tp_utils.get_c_hex_bytes(self.pubkey_info.get("auth_nonce")) + "};\n\n")

            f.write("uint8_t invalidated_signature[] = {\n")
            f.write(
                tpds.tp_utils.get_c_hex_bytes(self.pubkey_info.get("auth_signature")) + "};\n\n"
            )

            f.write("uint8_t public_key[] = {\n")
            f.write(tpds.tp_utils.get_c_hex_bytes(self.pubkey_info.get("public_key")) + "};\n\n")

            rotating_key_slot = self.device_info.get("pubkey_slot")
            f.write(f"uint16_t rotating_pubkey_slot = {rotating_key_slot};\n")
            auth_key_slot = self.device_info.get("auth_pubkey_slot")
            f.write(f"uint16_t authority_pubkey_slot = {auth_key_slot};\n\n")
            f.write("#ifdef __cplusplus\n")
            f.write("}\n")
            f.write("#endif\n")
            f.write("#endif\n")
