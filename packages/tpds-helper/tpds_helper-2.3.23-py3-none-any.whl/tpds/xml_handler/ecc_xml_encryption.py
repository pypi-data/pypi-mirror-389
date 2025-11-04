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

from os.path import splitext
from shutil import copyfile

import lxml.etree as ElementTree

from tpds.tp_utils.tp_utils import pretty_xml_hex_array

from .ciphers import Ciphers


class ECCXMLEncryption:
    def __init__(self, xml_file, rsa_key_xml, xml_out_file=""):
        self.file = xml_out_file
        if self.file == "":
            self.file = splitext(xml_file)[0] + ".ENC.xml"
        self.rsa_key_xml = rsa_key_xml
        copyfile(xml_file, self.file)
        self.tree = ElementTree.parse(self.file)
        self.root = self.tree.getroot()
        # self.secure_element = self.root.tag
        # self.xml_version = self.root.find('XMLVersion').text
        # self.part_number = self.root.find('PartNumber').text
        self.config_zone = self.root.find("Device").find("ConfigurationZone")
        self.sn01 = self.config_zone.find("SN01")
        self.sn8 = self.config_zone.find("SN8")
        self.data_zone = self.root.find("Device").find("DataZone")
        self.otp_zone = self.root.find("Device").find("OTPZone")
        self.certs = self.root.find("CompressedCerts")
        self.qa_data_zone_info = []

    def get_slots_to_encrypt_by_mode(self):
        self.encrypt_modes = ["Derived", "Secret", "PrivWrite", "HKDF-Expand-SHA256"]
        slots_to_encrypt_by_mode = dict()
        for encrypt_modes in list(self.encrypt_modes):
            search_string = "[@Mode='{}']".format(encrypt_modes)
            slots_to_encrypt_by_mode[encrypt_modes] = []
            for element in list(self.data_zone):
                slot_element = element.findall(search_string)
                if slot_element:
                    slots_to_encrypt_by_mode[encrypt_modes].append(slot_element)

        return slots_to_encrypt_by_mode

    def encrypt_device_slot(self, by_mode):
        for slot in list(by_mode):
            slot_data = slot[0].find("Data")
            slot_data.tag = "EncryptedData"
            slot_info = dict(slot[0].items())

            slot_info_modes = [x for x in self.encrypt_modes if x != "PrivWrite"]
            if slot_info["Mode"] in slot_info_modes:
                self.qa_data_zone_info.append({"Index": slot_info["Index"], "Key": slot_data.text})
            data = self.cipher.encrypt_slot(bytes.fromhex(slot_data.text))
            data = pretty_xml_hex_array(str(data.hex().upper()))
            slot_data.text = f"\n{data}"

    def add_QA_tag(self):
        qa = None
        if self.qa_data_zone_info or self.otp_zone.get("Mode") == "Secret":
            qa = ElementTree.Element("QA")
            challenge = ElementTree.SubElement(qa, "Challenge")
            data = pretty_xml_hex_array(str(bytes(range(0, 32)).hex().upper()), bytes_per_line=64)
            challenge.text = f"\n{data}"

        if self.qa_data_zone_info:
            data_zone = ElementTree.SubElement(qa, "DataZone")
            data_zone.set("Size", str(len(self.qa_data_zone_info)))
            for info in self.qa_data_zone_info:
                data_response = ElementTree.SubElement(data_zone, "Response")
                data_response.set("Index", str(info["Index"]))
                data = self.__generate_slot_response(
                    bytes.fromhex(challenge.text), int(info["Index"]), bytes.fromhex(info["Key"])
                )
                data = pretty_xml_hex_array(str(data.hex().upper()), bytes_per_line=64)
                data_response.text = f"\n{data}"
                self.__generate_otp_response(bytes.fromhex(challenge.text))

        if self.otp_zone.get("Mode") == "Secret":
            otp_zone = ElementTree.SubElement(qa, "OTPZone")
            otp_response = ElementTree.SubElement(otp_zone, "Response")
            data = self.__generate_otp_response(bytes.fromhex(self.otp_zone.find("Data").text))
            data = pretty_xml_hex_array(str(data.hex().upper()))
            otp_response.text = f"\n{data}"

        if qa is not None:
            self.root.append(qa)

    def add_AESKey_tag(self):
        self.aes_key = ElementTree.Element("AESKey")
        data = pretty_xml_hex_array(str(self.cipher.encrypt_aes_key_iv().hex().upper()))
        self.aes_key.text = f"\n{data}"
        self.root.append(self.aes_key)

    def add_Digest_tag(self):
        # calculate digest of encrypted file without digest tag
        # calculate digest of secret bytes
        # append the Digest tag to final XML
        file_name = self.file
        self.tree.write(file_name, xml_declaration=True, encoding="UTF-8")

        parser = ElementTree.XMLParser(remove_blank_text=True)
        xml_doc = ElementTree.parse(file_name, parser)
        xml_doc.write(file_name, pretty_print=True, xml_declaration=True, encoding="UTF-8")

        with open(file_name, "rb") as f:
            data = f.read()
        self.cipher.sha256_init()
        self.cipher.sha256_update(data)

        digest = ElementTree.Element("Digest")
        data = pretty_xml_hex_array(str(self.cipher.sha256_hash().hex().upper()))
        digest.text = f"\n{data}"
        xml_doc.getroot().append(digest)
        xml_doc.write(file_name, pretty_print=True, xml_declaration=True, encoding="UTF-8")

    def perform_encryption(self):
        self.cipher = Ciphers(self.rsa_key_xml)
        slots_to_encrypt_by_mode = self.get_slots_to_encrypt_by_mode()
        for by_mode in slots_to_encrypt_by_mode.values():
            self.encrypt_device_slot(by_mode)
        self.add_QA_tag()
        self.add_AESKey_tag()
        self.add_Digest_tag()

    def get_dump(self, element):
        return ElementTree.dump(element)

    def __generate_slot_response(self, hex_challenge, slot_index, slot_data):
        data = bytearray()
        data.extend(slot_data[:32])
        data.extend(hex_challenge[:32])
        data.append(0x08)
        data.append(0x00)
        data.append(slot_index)
        data.extend([0 for i in range(11)])
        data.append(0x00)
        data.extend(bytes.fromhex(self.sn8.text))
        data.extend([0 for i in range(4)])
        data.extend(bytes.fromhex(self.sn01.text))
        data.extend([0 for i in range(2)])

        self.cipher.sha256_init()
        self.cipher.sha256_update(data)

        return self.cipher.sha256_hash()

    def __generate_otp_response(self, hex_challenge):
        data = bytearray()
        data.extend([0 for i in range(32)])
        data.extend(hex_challenge[:32])
        data.append(0x08)
        data.append(0x26)
        data.append(0x00)
        data.append(0x00)
        data.extend([0 for i in range(3)])
        data.extend([0 for i in range(4)])
        data.extend(bytes.fromhex(self.sn01.text))
        data.extend([0 for i in range(2)])

        self.cipher.sha256_init()
        self.cipher.sha256_update(data)

        return self.cipher.sha256_hash()

    def __pretty_print_hex(self, a):
        return "".join(["%02X " % y for y in a])


# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == "__main__":
    # xml_enc = ECCXMLEncryption(
    #                 'xml_handler/ATECC608B-MAHAA-T_0309170608.xml',
    #                 'xml_handler/test_RSA_Key.xml')
    # xml_enc.perform_encryption()
    pass
