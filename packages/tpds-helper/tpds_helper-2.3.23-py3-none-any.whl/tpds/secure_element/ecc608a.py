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

import ctypes
import struct
from hashlib import sha256

import cryptoauthlib as cal

from .ca_element import CAElement
from .constants import Constants


class ECC608A(CAElement):
    def __init__(self, interface="i2c", address=0xC0, cfg=cal.cfg_ateccx08a_kithid_default()):
        self.cfg = cfg
        if interface == "i2c":
            self.cfg.cfg.atcahid.dev_interface = int(cal.ATCAKitType.ATCA_KIT_I2C_IFACE)
            self.cfg.cfg.atcahid.dev_identity = address
        else:
            self.cfg.cfg.atcahid.dev_interface = int(cal.ATCAKitType.ATCA_KIT_SWI_IFACE)
            self.cfg.cfg.atcahid.dev_identity = 0

        self.cfg.devtype = cal.get_device_type_id("ATECC608A")

        super().connect(self.cfg)

    def host_calc_mac_resp(self, symm_key, challenge, mode=0x41, slot=5):
        """
        Calculates mac on the host...
        """
        if not isinstance(symm_key, (bytearray, bytes)):
            raise ValueError("Unknown symmetric key format!")
        if not isinstance(challenge, (bytearray, bytes)):
            raise ValueError("Unknown tempkey or challenge format!")

        ser_num = self.get_device_serial_number()

        is_sn_include = False
        if mode & 0x40:
            is_sn_include = True

        response = b""
        response += symm_key[0:32]
        response += challenge[0:32]
        response += struct.pack("B", Constants.ATCA_ECC608_MAC_OPCODE)
        response += struct.pack("B", mode)
        response += struct.pack("<H", slot)
        response += b"\x00" * 11
        response += ser_num[8:9]
        response += ser_num[4:8] if is_sn_include else b"\x00" * 4
        response += ser_num[0:2]
        response += ser_num[2:4] if is_sn_include else b"\x00" * 2

        response = sha256(response).digest()

        return {"challenge": challenge, "response": response}

    def host_calc_nonce(self, num_in, rand_out, mode=0x00):
        """
        Calculate Host nonce
        """
        if not isinstance(num_in, (bytearray, bytes)):
            raise ValueError("Unknown NumIn format!")
        if not isinstance(rand_out, (bytearray, bytes)):
            raise ValueError("Unknown Random number format!")

        nonce = b""
        nonce += rand_out[0:32]
        nonce += num_in[0:20]
        nonce += struct.pack("B", Constants.ATCA_ECC608_NONCE_OPCODE)
        nonce += struct.pack("B", mode)
        nonce += b"\x00"

        nonce = sha256(nonce).digest()

        return {
            "num_in": num_in,
            "rand_out": rand_out,
            "nonce": nonce,
        }

    def get_device_mac_response(self, slot=5, challenge=0, mode=0x41):
        """
        Calculates mac on the device...
        """
        if not mode & 0x01:
            if challenge == 0:
                raise ValueError("For given mode challenge is required!")

        response = bytearray(32)
        assert (
            cal.atcab_mac(mode, slot, challenge, response) == cal.Status.ATCA_SUCCESS
        ), "MAC Response generation failed"

        return response

    def get_device_random_nonce(self, num_in):
        """
        Get random number from device for given num_in
        """
        rand_out = bytearray(32)
        assert (
            cal.atcab_nonce_rand(num_in, rand_out) == cal.Status.ATCA_SUCCESS
        ), "Nonce generation failed"

        return {"num_in": num_in, "rand_out": rand_out}


class ECC608B(CAElement):
    def __init__(self, address, port):
        self.cfg = cal.ATCAIfaceCfg()
        self.cfg.iface_type = int(cal.ATCAIfaceType.ATCA_UART_IFACE)
        self.cfg.devtype = int(cal.ATCADeviceType.ATECC608B)
        self.cfg.wake_delay = 1500
        self.cfg.rx_retries = 10

        self.cfg.cfg.atcauart.dev_interface = int(cal.ATCAKitType.ATCA_KIT_I2C_IFACE)
        self.cfg.cfg.atcauart.dev_identity = address
        if isinstance(port, str):
            self.cfg.cfg.cfg_data = ctypes.c_char_p(port.encode("ascii"))
        else:
            self.cfg.cfg.atcauart.port = port
        self.cfg.cfg.atcauart.baud = 115200
        self.cfg.cfg.atcauart.wordsize = 8
        self.cfg.cfg.atcauart.parity = 2
        self.cfg.cfg.atcauart.stopbits = 1
        self.port = port
        super().connect(self.cfg)


__all__ = ["ECC608A", "ECC608B"]

# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == "__main__":
    pass
