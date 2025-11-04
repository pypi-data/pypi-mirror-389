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

from .sha204a import SHA204A


class SHA206A(SHA204A):
    def __init__(self, interface="swi", address=0x00, cfg=cal.cfg_atsha20xa_kithid_default()):
        self.cfg = cfg
        self.cfg.cfg.atcahid.dev_interface = int(cal.ATCAKitType.ATCA_KIT_SWI_IFACE)
        self.cfg.cfg.atcahid.dev_identity = 0

        # Should be using get_device_type_id('ATSHA206A')
        # but get_device_type_id yet
        self.cfg.devtype = 4

        super().connect(self.cfg)

    def get_use_counts(self):
        read_count = bytearray(20)
        assert (
            cal.atcab_read_bytes_zone(0, 0, 64, read_count, 20) == cal.Status.ATCA_SUCCESS
        ), "Reading UseFlags from device failed"

        dk_count = bin(read_count[2]).count("1")
        pk_count = bin(int.from_bytes(read_count[4:], byteorder="big")).strip("0b").count("1")
        consump_count = (pk_count * 8) - (8 - dk_count)

        return {"dk_useflag": dk_count, "pk_useflag": pk_count, "consump_count": consump_count}


# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == "__main__":
    pass
