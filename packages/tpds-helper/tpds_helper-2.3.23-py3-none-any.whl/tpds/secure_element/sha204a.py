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

import os

import cryptoauthlib as cal
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes

from .ca_element import CAElement
from .constants import Constants


class SHA204A(CAElement):
    def __init__(self, interface="i2c", address=0xC8, cfg=cal.cfg_atsha20xa_kithid_default()):
        self.cfg = cfg
        if interface == "i2c":
            self.cfg.cfg.atcahid.dev_interface = int(cal.ATCAKitType.ATCA_KIT_I2C_IFACE)
            self.cfg.cfg.atcahid.dev_identity = address
        else:
            self.cfg.cfg.atcahid.dev_interface = int(cal.ATCAKitType.ATCA_KIT_SWI_IFACE)
            self.cfg.cfg.atcahid.dev_identity = address
        self.cfg.devtype = cal.get_device_type_id("ATSHA204A")
        super().connect(self.cfg)

    def get_mac_response(self, slot, challenge=None):
        """
        Calculates mac on the device...
        """
        response = bytearray()
        if challenge is None:
            challenge = os.urandom(32)

        assert (
            cal.atcab_mac(Constants.ATCA_SHA204A_MAC_MODE, slot, challenge, response)
            == cal.Status.ATCA_SUCCESS
        ), "Response generation failed"

        return {"challenge": challenge[0:32], "response": response}

    def host_calc_mac_resp(self, slot, symm_key, challenge=None):
        """
        Calculates mac on the host...
        """
        response = bytearray()
        ser_num = self.get_device_serial_number()

        if challenge is None:
            challenge = os.urandom(32)

        response.extend(symm_key[0:32])  # symmetric key
        response.extend(challenge[0:32])
        response.append(Constants.ATCA_SHA204A_MAC_OPCODE)
        response.append(Constants.ATCA_SHA204A_MAC_MODE)
        response.append(slot)
        response.append(0)
        response.extend([0 for i in range(11)])
        response.append(ser_num[8])
        response.extend([0 for i in range(4)])
        response.append(ser_num[0])
        response.append(ser_num[1])
        response.extend([0 for i in range(2)])
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(bytes(response))
        response = digest.finalize()

        return {"challenge": challenge[0:32], "response": response}


# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == "__main__":
    pass
