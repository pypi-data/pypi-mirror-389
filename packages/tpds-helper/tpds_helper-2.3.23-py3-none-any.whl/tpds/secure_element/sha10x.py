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

from .ecc204 import ECC204
import cryptoauthlib as cal
from .constants import Constants
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


class SHA104(ECC204):
    def __init__(self, interface="i2c", address=0x31, device_name="SHA104", cfg=cal.cfg_ateccx08a_kithid_default()):
        self.cfg = cfg
        if interface == "i2c":
            self.cfg.cfg.atcahid.dev_interface = int(cal.ATCAKitType.ATCA_KIT_I2C_IFACE)
            self.cfg.cfg.atcahid.dev_identity = address
        else:
            self.cfg.cfg.atcahid.dev_interface = int(cal.ATCAKitType.ATCA_KIT_SWI_IFACE)
            self.cfg.cfg.atcahid.dev_identity = address
        self.cfg.devtype = cal.get_device_type_id(device_name)
        super().connect(self.cfg)

    def load_tflx_test_config(self, test_config):
        assert len(test_config) == 64, "Test Config is not of 64 bytes in size."
        for subzone in [1, 2, 3]:
            if self.is_config_slot_locked(subzone) is False:
                assert (
                    cal.get_cryptoauthlib().atcab_write_zone(
                        Constants.ATCA_CONFIG_ZONE,
                        subzone,
                        0,
                        0,
                        test_config[(subzone * 16) : ((subzone + 1) * 16)],
                        16,
                    )
                    == cal.Status.ATCA_SUCCESS
                ), f"Config Subzone{subzone} write is failed"
        assert (
            cal.atcab_lock_config_zone() == cal.Status.ATCA_SUCCESS
        ), "Config zone lock has failed"

    @staticmethod
    def get_diversified_key(parent_key, other_data, sn801, fixed_input):
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(bytes(parent_key))
        digest.update(bytes(other_data))
        digest.update(bytes(sn801))
        digest.update(bytes([0 for i in range(25)]))
        digest.update(bytes(fixed_input))
        return digest.finalize()


class SHA106(SHA104):
    def __init__(self, interface="swi", address=0x31):
        super().__init__(interface, address, device_name="SHA106")


class SHA105(SHA104):
    def __init__(self, interface="i2c", address=0x32):
        super().__init__(interface, address, device_name="SHA105")

    @staticmethod
    def build_checkmac_other_data(mac_mode, accessory_sn):
        checkmac_other_data = bytearray()
        checkmac_other_data.append(0x08)
        checkmac_other_data.append(mac_mode)
        checkmac_other_data.append(3)  # Key_slot is fixed on this device
        checkmac_other_data.append(0)
        checkmac_other_data.extend([0 for i in range(3)])
        checkmac_other_data.extend(accessory_sn[4:8])
        checkmac_other_data.extend(accessory_sn[2:4])
        return checkmac_other_data
