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
import struct
from hashlib import sha256

from cryptoauthlib.library import ctypes_to_bytes

import tpds.tp_utils


class PubKeyValidation:
    def __init__(self):
        pass

    def set_device_info(self, device_config, auth_pubkey_slot, pubkey_slot):
        """
        Method set the Tempkey flags, tempkey slot configuration and
        tempkey key configuration
        Inputs:
              device_config        device configuration
              auth_pubkey_slot     authority public key slot
              pubkey_slot          public key slot
        """
        self.device_info = dict()
        self.device_info.update(
            {
                "serial_num": ctypes_to_bytes(device_config.SN03)
                + ctypes_to_bytes(device_config.SN48)
            }
        )
        self.device_info.update({"auth_pubkey_slot": auth_pubkey_slot})
        self.device_info.update({"pubkey_slot": pubkey_slot})
        self.device_info.update(
            {"pubkey_slot_config": ctypes_to_bytes(device_config.SlotConfig[pubkey_slot])}
        )
        self.device_info.update(
            {"pubkey_key_config": ctypes_to_bytes(device_config.KeyConfig[pubkey_slot])}
        )
        self.device_info.update({"pubkey_slot_lock": device_config.SlotLocked & (1 << pubkey_slot)})

        # Default values set
        self.device_info.update({"sign_internal_mode": 0})
        self.device_info.update({"include_full_sn": False})
        self.device_info.update({"temp_key_source_flag": True})
        self.device_info.update({"temp_key_gendig_data": False})
        self.device_info.update({"temp_key_genkey_data": True})
        self.device_info.update({"temp_key_no_mac": False})

    def authorize_public_key(self, auth_key, public_key, pubkey_valid=False):
        """
        Method calculate public key digest and sign the same using authority
        private key
        Inputs:
             auth_key      Authority private key
             public_key    key to used to calc pubkey digest
             pubkey_valid  public key validation state
        outputs:
             pubkey_info   dictionary contains calculated nonce,
                           signature and public key
        """
        asym_auth_key = tpds.tp_utils.TPAsymmetricKey(auth_key)

        asym_key = tpds.tp_utils.TPAsymmetricKey()
        asym_key.set_public_key(public_key)
        self.public_key = asym_key.public_key_bytes

        self.__calc_nonce()
        self.__calc_genkey_digest()
        self.__calc_sign_internal_digest(pubkey_valid)
        self.signature = tpds.tp_utils.sign_on_host(
            self.sign_internal_digest, asym_auth_key.get_private_key()
        )

        self.pubkey_info = dict()
        self.pubkey_info.update({"auth_nonce": self.nonce})
        self.pubkey_info.update({"auth_signature": self.signature})
        self.pubkey_info.update({"public_key": self.public_key})

    def __calc_nonce(self):
        """
        Calculate host nonce
        """
        self.numin = os.urandom(32)
        self.nonce = self.numin

    def __calc_genkey_digest(self):
        """
        Calculate public key digest using genkey command
        """
        msg = b""
        msg += self.nonce  # value loaded to Tempkey
        msg += b"\x40"  # GenKey Opcode
        msg += b"\x00" * 3  # other data
        msg += self.device_info.get("serial_num")[8:9]
        msg += self.device_info.get("serial_num")[0:2]
        msg += b"\x00" * 25
        msg += self.public_key
        self.pubkey_digest = sha256(msg).digest()

    def __calc_sign_internal_digest(self, pubkey_valid=False):
        """
        Calculate sign internal message digest
        Inputs:
              pubkey_valid        True if public key valid else False
        """
        msg = b""
        msg += self.pubkey_digest
        msg += b"\x41"  # Sign Opcode
        msg += struct.pack("B", self.device_info.get("sign_internal_mode"))
        msg += struct.pack("<H", self.device_info.get("auth_pubkey_slot"))
        msg += self.device_info.get("pubkey_slot_config")
        msg += self.device_info.get("pubkey_key_config")

        temp_key_flags = self.device_info.get("pubkey_slot")
        temp_key_flags += (1 << 4) if self.device_info.get("temp_key_source_flag") else 0
        temp_key_flags += (1 << 5) if self.device_info.get("temp_key_gendig_data") else 0
        temp_key_flags += (1 << 6) if self.device_info.get("temp_key_genkey_data") else 0
        temp_key_flags += (1 << 7) if self.device_info.get("temp_key_no_mac") else 0
        msg += struct.pack("B", temp_key_flags)

        msg += b"\x00" * 2
        msg += self.device_info.get("serial_num")[8:9]
        msg += (
            self.device_info.get("serial_num")[4:8]
            if self.device_info.get("include_full_sn")
            else b"\x00" * 4
        )
        msg += self.device_info.get("serial_num")[0:2]
        msg += (
            self.device_info.get("serial_num")[2:4]
            if self.device_info.get("include_full_sn")
            else b"\x00" * 2
        )
        msg += b"\x01" if self.device_info.get("pubkey_slot_lock") else b"\x00"
        msg += b"\x01" if pubkey_valid else b"\x00"
        msg += b"\x00"
        other_data = bytearray()
        other_data.extend(msg[33:43])
        other_data.extend(msg[44:48])
        other_data.extend(msg[50:55])
        self.sign_internal_digest = sha256(msg).digest()
        self.sign_internal_other_data = other_data
