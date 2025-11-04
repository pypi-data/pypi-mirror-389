# -*- coding: utf-8 -*-
# 2019 to present - Copyright Microchip Technology Inc. and its subsidiaries.

# Subject to your compliance with these terms, you may use Microchip software
# and any derivatives exclusively with Microchip products. It is your
# responsibility to comply with third party license terms applicable to your
# use of third party software (including open source software) that may
# accompany Microchip software.

import cryptoauthlib as cal
from tpds.helper import log

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
import tpds.secure_element
from tpds.secure_element.constants import Constants


class ECCProvision:
    def __init__(self, cfg=cal.cfg_ateccx08a_kithid_default()):
        self.element = tpds.secure_element.CAElement()
        self.element.connect(cfg)

    def perform_genkey(self, slot):
        log(f"Performing Genkey for {slot}")
        slot_public_key = bytearray(64)
        status = cal.atcab_genkey(slot, slot_public_key)
        assert status == cal.Status.ATCA_SUCCESS, "Genkey failed"

    def perform_slot_write(self, slot, data, encryption_slot=None, encryption_data=None):
        if encryption_slot and encryption_data:
            log((f"Performing Slot Enc Write for {slot}" f" with {encryption_slot}"))
            status = cal.atcab_write_enc(slot, 0, data, encryption_data, encryption_slot)
        else:
            log(f"Performing Slot Write for {slot}")
            status = cal.atcab_write_bytes_zone(Constants.ATCA_DATA_ZONE, slot, 0, data, len(data))
        assert status == cal.Status.ATCA_SUCCESS, "Slot Write failed"


# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == "__main__":
    pass
