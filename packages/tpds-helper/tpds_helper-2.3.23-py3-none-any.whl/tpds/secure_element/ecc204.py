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

import struct
from ctypes import byref, c_uint8, c_void_p, cast

import cryptoauthlib as cal

from .ca_element import CAElement
from .constants import Constants


class ECC204(CAElement):
    def __init__(self, interface="i2c", address=0x33, cfg=cal.cfg_ateccx08a_kithid_default()):
        self.cfg = cfg
        if interface == "i2c":
            self.cfg.cfg.atcahid.dev_interface = int(cal.ATCAKitType.ATCA_KIT_I2C_IFACE)
            self.cfg.cfg.atcahid.dev_identity = address
        else:
            self.cfg.cfg.atcahid.dev_interface = int(cal.ATCAKitType.ATCA_KIT_SWI_IFACE)
            self.cfg.cfg.atcahid.dev_identity = address

        self.cfg.devtype = cal.get_device_type_id("ECC204")

        super().connect(self.cfg)

    def is_config_slot_locked(self, slot_number):
        _device = cast(cal.atcab_get_device(), c_void_p)
        is_locked = c_uint8()
        assert (
            cal.get_cryptoauthlib().calib_info_lock_status(
                _device, (slot_number << 1) | Constants.ATCA_ECC204_ZONE_CONFIG, byref(is_locked)
            )
            == cal.Status.ATCA_SUCCESS
        ), "Reading Config Slot lock status is failed"
        return is_locked.value == 1

    def is_data_slot_locked(self, slot_number):
        _device = cast(cal.atcab_get_device(), c_void_p)
        is_locked = c_uint8()
        assert (
            cal.get_cryptoauthlib().calib_info_lock_status(
                _device, (slot_number << 1) | Constants.ATCA_ECC204_ZONE_DATA, byref(is_locked)
            )
            == cal.Status.ATCA_SUCCESS
        ), "Reading Data Slot lock status is failed"
        return is_locked.value == 1

    def load_config_zone(self, config_data):
        """
        Loads configuration data to config zone
        """
        assert self.is_config_zone_locked() is False, "Device config zone is already locked."

        # Write configuration
        assert (
            cal.atcab_write_config_zone(config_data) == cal.Status.ATCA_SUCCESS
        ), "Writing Config zone failed"

        # Verify Config Zone
        config_qa = bytearray(len(config_data))
        assert (
            cal.atcab_read_config_zone(config_qa) == cal.Status.ATCA_SUCCESS
        ), "Reading Config zone failed"

        assert config_data == config_qa, "Configuration read does not match"

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

        if self.is_data_slot_locked(0) is False:
            public_key = bytearray(64)
            assert (
                cal.atcab_genkey(0, public_key) == cal.Status.ATCA_SUCCESS
            ), "Slot0 key generation is failed"
            assert (
                cal.get_cryptoauthlib().atcab_lock_data_slot(0) == cal.Status.ATCA_SUCCESS
            ), "Data zone Slot0 lock is failed"

    def get_device_details(self):
        """
        Returns device basic information like Revision, Serial No,
        Config status etc..,
        """
        device_info = dict()
        device_info["revision"] = self.get_device_revision().hex()
        device_info["serial_number"] = self.get_device_serial_number().hex().upper()
        device_info["lock_status"] = [
            tuple(self.is_config_slot_locked(i) for i in range(0, 4)),
            tuple(self.is_data_slot_locked(i) for i in range(0, 4)),
        ]

        return device_info

    def int_to_binary_linear(self, value):
        """
        convert decimal value into monotonic counter value
        """
        l1 = list(struct.pack(">q", 0xFFFFFFFFFFFF >> (value % 96)))[2:]
        b1 = list(struct.pack(">H", value // 96))
        l2, b2 = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF], [0x00, 0x00]
        if value > 48:
            l2 = list(struct.pack(">q", 0xFFFFFFFFFFFF >> ((value - 48) % 96)))[2:]
            b2 = list(struct.pack(">H", (value - 48) // 96))
        value = b1 + b2 + l1 + l2
        return value
