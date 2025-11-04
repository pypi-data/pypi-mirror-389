# -*- coding: utf-8 -*-
# 2023 to present - Copyright Microchip Technology Inc. and its subsidiaries.

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
from tpds.secure_element import SHA104, SHA105, SHA106
from tpds.secure_element.constants import Constants


class SHA10xProvision:
    def __init__(self, device_cls=SHA104, interface="i2c", address=0x31):
        self.element = device_cls(interface, address)

    def perform_slot_write(self, slot, data):
        if slot == 0:
            """
            Atcab_write_bytes_zone does not support SLOT 0 Write,
            so we are using atcab_write_zone instead.
            """
            status = cal.atcab_write_zone(
                Constants.ATCA_DATA_ZONE,
                0,
                0,
                0,
                data,
                len(data),
            )
        else:
            status = cal.atcab_write_bytes_zone(Constants.ATCA_DATA_ZONE, slot, 0, data, len(data))

        assert status == cal.Status.ATCA_SUCCESS, f"Slot Write has failed with {status: 02X}"

    def int_to_binary_linear(self, value):
        """
        wrapper function for converting decimal value into monotonic counter
        """
        return self.element.int_to_binary_linear(value)


class SHA104Provision(SHA10xProvision):
    def __init__(self, interface="i2c", address=0x31):
        super().__init__(SHA104, interface, address)


class SHA106Provision(SHA10xProvision):
    def __init__(self, interface="swi", address=0x31):
        super().__init__(SHA106, "swi", address)


class SHA105Provision(SHA10xProvision):
    def __init__(self, interface="i2c", address=0x32):
        super().__init__(SHA105, interface, address)
