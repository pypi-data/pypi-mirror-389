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

import binascii
import os

from tpds.tp_utils.tp_settings import TPSettings


class CertsBackup:
    def __init__(self):
        pass

    def store_to_file(self, certs, file_path=None, device_sn=None):
        self.__set_file_path(file_path, device_sn)

        if not isinstance(certs, dict):
            raise ValueError("certs must be dict with keys as root, signer and device")

        with open(self.file_path, "w") as fp:
            fp.write(certs.get("device").get_certificate_in_pem().decode("utf-8")) if certs.get(
                "device"
            ) else None
            fp.write(certs.get("signer").get_certificate_in_pem().decode("utf-8")) if certs.get(
                "signer"
            ) else None
            fp.write(certs.get("root").get_certificate_in_pem().decode("utf-8")) if certs.get(
                "root"
            ) else None

    def fetch_from_file(self, file_path=None, device_sn=None):
        self.__set_file_path(file_path, device_sn)

        certs = dict()
        if os.path.exists(self.file_path):
            match_str = "-----BEGIN CERTIFICATE-----"
            with open(self.file_path, "r") as fp:
                file_content = fp.read()
                pem_certs = file_content.split(match_str)
                cert_names = ["device", "signer", "root"]
                index = 0
                for cert in pem_certs:
                    if "CERTIFICATE" in cert:
                        cert = match_str + cert
                        certs.update({cert_names[index]: cert})
                        index += 1

        return certs

    def __set_file_path(self, file_path, device_sn):
        if file_path is None and device_sn is None:
            raise ValueError("Either file_path or device_sn is must")

        self.file_path = file_path
        if file_path is None:
            tp_settings = TPSettings()
            base_path = os.path.join(tp_settings.get_base_folder(), "mchp_certs")
            if not os.path.exists(base_path):
                os.mkdir(base_path)

            if not isinstance(device_sn, bytearray):
                raise ValueError("device_sn must be byte array")

            device_sn = str(binascii.hexlify(device_sn), "utf-8").upper()
            self.file_path = os.path.join(base_path, f"{device_sn}.pem")


__all__ = ["CertsBackup"]
