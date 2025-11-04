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

import json
import os
from pathlib import Path

import lxml.etree as ElementTree
from cryptography.hazmat.primitives import serialization

from tpds.certs.create_cert_defs import CertDef
from tpds.certs.tflex_certs import TFLEXCerts
from tpds.tp_utils.tp_utils import pretty_xml_hex_array


class TFLXTLSXMLUpdates:
    def __init__(self, base_xml="ECC608B_TFLXTLS.xml"):
        self.base_xml = base_xml

    def initialize(self, base_xml):
        curr_path = os.path.abspath(os.path.dirname(__file__))
        self.tree = ElementTree.parse(os.path.join(curr_path, base_xml))
        self.root = self.tree.getroot()
        self.config_zone = self.root.find("Device").find("ConfigurationZone")
        self.data_zone = self.root.find("Device").find("DataZone")
        self.comp_certs = self.root.find("CompressedCerts")
        self.cert_slots = {"device_crt": 10, "signer_crt": 12}

    def update_with_user_data(self, user_data):
        self.initialize(self.base_xml)
        self.user_data = json.loads(user_data)
        self.root.find("PartNumber").text = self.user_data.get("part_number")
        if "ECC608A" in self.user_data.get("part_number"):
            self.root.tag = "ATECC608A"
        elif "ECC608B" in self.user_data.get("part_number"):
            self.root.tag = "ATECC608B"
        else:
            self.root.tag = "ATECC608C"
        self.config_zone.find("SN8").text = self.user_data.get("man_id")
        if self.user_data.get("interface") == "swi":
            self.config_zone.find("I2CEnable").text = "00"
            self.config_zone.find("I2CAddress").text = "03"

        self.__process_slot_config()
        self.__process_slot_data()
        self.__process_certs_data()
        self.__process_otp_data()
        # self.dump(self.root)

    def __process_slot_config(self):
        if self.user_data.get("sboot_latch") == "enabled":
            key_config = self.config_zone.find("KeyConfigurations/KeyConfiguration[@Index='0']")
            key_config.text = key_config.text[:3] + "1" + key_config.text[4:]
            secure_boot = self.config_zone.find("SecureBoot")
            secure_boot.text = secure_boot.text[:1] + "B" + secure_boot.text[2:]

        slot_locked = [
            slot.get("slot_id")
            for slot in self.user_data.get("slot_info")
            if slot.get("slot_lock") == "enabled"
        ]
        for slot in slot_locked:
            slot_config = self.config_zone.find(
                f"SlotConfigurations/SlotConfiguration[@Index='{slot:X}']"
            )
            slot_config.text = slot_config.text[:3] + "8" + slot_config.text[4:]

    def __process_slot_data(self):
        public_key_slots = [13, 14, 15]
        slots_with_data = [
            slot.get("slot_id")
            for slot in self.user_data.get("slot_info")
            if slot.get("data") is not None
        ]

        for slot in slots_with_data:
            slot_details = self.user_data.get("slot_info")[slot]
            slot_element = self.data_zone.find(f"Slot[@Index='{slot:X}']")
            if slot_details.get("slot_type") == "secret":
                slot_element.set("Mode", "Secret")
                slot_data_element = ElementTree.SubElement(slot_element, "Data")
                if slot == 9:
                    slot_data_element.set("Size", "72")
                    data = pretty_xml_hex_array(
                        self.user_data.get("slot_info")[slot].get("data") + "0000000000000000"
                    )
                else:
                    slot_data_element.set("Size", "36")
                    data = pretty_xml_hex_array(
                        self.user_data.get("slot_info")[slot].get("data") + "00000000"
                    )
                slot_data_element.text = f"\n{data}"
                slot_element.append(slot_data_element)
            elif slot_details.get("slot_type") == "public":
                slot_data = self.user_data.get("slot_info")[slot].get("data")
                if slot in public_key_slots:
                    slot_data = f"00000000{slot_data[:64]}00000000{slot_data[-64:]}"
                data = pretty_xml_hex_array(slot_data)
                slot_element.find("Data").text = f"\n{data}"
                slot_element.find("Data").set("Size", "72")
            elif slot_details.get("slot_type") == "general":
                slot_data = self.user_data.get("slot_info")[slot].get("data")
                data = pretty_xml_hex_array(slot_data)
                slot_element.find("Data").text = f"\n{data}"

    def __process_certs_data(self):
        slot10_data = self.user_data.get("slot_info")[self.cert_slots.get("device_crt")]
        slot12_data = self.user_data.get("slot_info")[self.cert_slots.get("signer_crt")]

        self.tflex_certs = TFLEXCerts()
        if slot12_data.get("cert_type") == "MCHPCert":
            self.tflex_certs.build_root()
            self.tflex_certs.build_signer_csr()
            self.tflex_certs.build_signer()
            self.tflex_certs.build_device()
        else:
            self.tflex_certs.build_root(
                org_name=slot12_data.get("signer_ca_org"),
                common_name=slot12_data.get("signer_ca_cn"),
                validity=int(slot12_data.get("cert_expiry_years")),
                user_pub_key=bytes(slot12_data.get("signer_ca_pubkey"), "ascii"),
            )
            self.tflex_certs.build_signer_csr(
                org_name=slot12_data.get("cert_org"),
                common_name=slot12_data.get("cert_cn"),
                signer_id="FFFF",
            )
            self.tflex_certs.build_signer(validity=int(slot12_data.get("cert_expiry_years")))
            self.tflex_certs.build_device(
                device_sn=slot10_data.get("cert_cn"),
                org_name=slot10_data.get("cert_org"),
                validity=int(slot10_data.get("cert_expiry_years")),
            )

        certs_txt = (
            self.tflex_certs.root.get_certificate_in_text()
            + "\n\n"
            + self.tflex_certs.signer.get_certificate_in_text()
            + "\n\n"
            + self.tflex_certs.device.get_certificate_in_text()
        )
        Path("custom_certs.txt").write_text(certs_txt)
        Path("root.crt").write_bytes(self.tflex_certs.root.get_certificate_in_pem())
        Path("signer.crt").write_bytes(self.tflex_certs.signer.get_certificate_in_pem())
        Path("device.crt").write_bytes(self.tflex_certs.device.get_certificate_in_pem())

        self.__process_signer_cert(self.tflex_certs)
        self.__process_device_cert(self.tflex_certs)

    def __process_signer_cert(self, certs):
        cert_def = CertDef()
        cert_def.set_certificate(certs.signer.certificate, certs.root.certificate, 1)
        params = cert_def.get_cert_params()

        signer_comp_cert = self.comp_certs.find("CompressedCert[@ChainLevel='1']")
        signer_comp_cert.set("TemplateID", str(params.get("template_id")))
        signer_comp_cert.set("ChainID", str(params.get("chain_id")))
        signer_comp_cert.set("TbsSize", str(params.get("tbs_cert_loc").get("count")))
        signer_comp_cert.set("TbsLoc", str(params.get("tbs_cert_loc").get("offset")))
        signer_comp_cert.set("ValidYears", str(params.get("expire_years")))
        if self.user_data.get("single_signer"):
            signer_comp_cert.set("SingleSignerID", self.user_data.get("single_signer"))

        std_cert_elements = [
            "SubjectPublicKey",
            "Signature",
            "IssueDate",
            "ExpireDate",
            "SignerID",
            "SerialNumber",
            "AuthorityKeyId",
            "SubjectKeyId",
        ]
        for elem in std_cert_elements:
            element = params.get("std_cert_elements")[std_cert_elements.index(elem)]
            search_for = f"Element[@Name='{elem}']"
            signer_comp_cert.find(search_for).set("DataLoc", str(element.get("offset")))
            signer_comp_cert.find(search_for).set("NumBytes", str(element.get("count")))

        template_data = cert_def.cert.public_bytes(encoding=serialization.Encoding.DER)
        signer_comp_cert.find("TemplateData").set("Size", str(len(template_data)))
        data = pretty_xml_hex_array(template_data.hex().upper())
        signer_comp_cert.find("TemplateData").text = f"\n{data}"

        slot12_data = self.user_data.get("slot_info")[self.cert_slots.get("signer_crt")]
        if slot12_data.get("cert_type") != "MCHPCert":
            data = pretty_xml_hex_array(slot12_data.get("signer_ca_pubkey"))
            signer_comp_cert.find("CAPublicKey").text = f"\n{data}"
        cert_def.get_c_definition(True)

    def __process_device_cert(self, certs):
        cert_def = CertDef()
        cert_def.set_certificate(certs.device.certificate, certs.signer.certificate, 3)
        params = cert_def.get_cert_params()

        device_comp_cert = self.comp_certs.find("CompressedCert[@ChainLevel='0']")
        device_comp_cert.set("TemplateID", str(params.get("template_id")))
        device_comp_cert.set("ChainID", str(params.get("chain_id")))
        device_comp_cert.set("TbsSize", str(params.get("tbs_cert_loc").get("count")))
        device_comp_cert.set("TbsLoc", str(params.get("tbs_cert_loc").get("offset")))
        device_comp_cert.set("ValidYears", str(params.get("expire_years")))
        if self.user_data.get("single_signer"):
            device_comp_cert.set("SingleSignerID", self.user_data.get("single_signer"))

        std_cert_elements = [
            "SubjectPublicKey",
            "Signature",
            "IssueDate",
            "ExpireDate",
            "SignerID",
            "SerialNumber",
            "AuthorityKeyId",
            "SubjectKeyId",
        ]
        for elem in std_cert_elements:
            element = params.get("std_cert_elements")[std_cert_elements.index(elem)]
            search_for = f"Element[@Name='{elem}']"
            device_comp_cert.find(search_for).set("DataLoc", str(element.get("offset")))
            device_comp_cert.find(search_for).set("NumBytes", str(element.get("count")))

        slot10_data = self.user_data.get("slot_info")[self.cert_slots.get("device_crt")]
        if (slot10_data.get("cert_type") != "MCHPCert") and (
            "0123030405060708EE" not in slot10_data.get("cert_cn")
        ):
            device_comp_cert.remove(device_comp_cert.find("Element[@Name='SN03']"))
            device_comp_cert.remove(device_comp_cert.find("Element[@Name='SN48']"))
        else:
            SN_elements = ["SN03", "SN48"]
            cert_elements = cert_def.get_cert_elements()
            for element in cert_elements:
                if element.get("id") in SN_elements:
                    sn_data = cert_elements[SN_elements.index(element.get("id"))].get("cert_loc")
                    search_for = f"Element[@Name='{element.get('id')}']"
                    device_comp_cert.find(search_for).set("DataLoc", str(sn_data.get("offset")))
                    device_comp_cert.find(search_for).set("NumBytes", str(sn_data.get("count")))

        template_data = cert_def.cert.public_bytes(encoding=serialization.Encoding.DER)
        device_comp_cert.find("TemplateData").set("Size", str(len(template_data)))
        data = pretty_xml_hex_array(template_data.hex().upper())
        device_comp_cert.find("TemplateData").text = f"\n{data}"
        cert_def.get_c_definition(True)

    def __process_otp_data(self):
        otp_element = self.root.find("Device").find("OTPZone")
        data = pretty_xml_hex_array(self.user_data.get("otp_zone"))
        otp_element.find("Data").text = f"\n{data}"

    def save_root(self, dest_xml):
        tree = ElementTree.ElementTree(self.root)
        tree.write(dest_xml, xml_declaration=True, encoding="UTF-8")

    def dump(self, element):
        print(ElementTree.dump(element))


# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == "__main__":
    config_string = ' \
    {"base_xml":"ECC608B_TFLXTLS.xml","xml_type":"proto_xml","interface":"i2c","slot_info":[{"slot_id":0,"slot_type":"private","key_load_config":"noLoad","slot_lock":null},{"slot_id":1,"slot_type":"private","key_load_config":"noLoad","slot_lock":null},{"slot_id":2,"slot_type":"private","key_load_config":"noLoad","slot_lock":"disabled"},{"slot_id":3,"slot_type":"private","key_load_config":"noLoad","slot_lock":"disabled"},{"slot_id":4,"slot_type":"private","key_load_config":"noLoad","slot_lock":"disabled"},{"slot_id":5,"slot_type":"secret","key_load_config":"load","slot_lock":"disabled","data":null},{"slot_id":6,"slot_type":"secret","key_load_config":"load","slot_lock":"disabled","data":null},{"slot_id":7,"slot_type":"general","key_load_config":"noLoad","slot_lock":null},{"slot_id":8,"slot_type":"general","key_load_config":"load","slot_lock":"disabled","data":null},{"slot_id":9,"slot_type":"secret","key_load_config":"load","slot_lock":null,"data":null},{"slot_id":10,"slot_type":"cert","key_load_config":"cert","slot_lock":null,"cert_type":"custCert","cert_org":"dev org name","cert_cn":"sn0123030405060708EE","cert_expiry_years":"10"},{"slot_id":11,"slot_type":"cert","key_load_config":"noLoad","slot_lock":null},{"slot_id":12,"slot_type":"cert","key_load_config":"cert","slot_lock":null,"cert_type":"custCert","cert_org":"signer org","cert_cn":"signer cn","cert_expiry_years":"10","signer_ca_org":"root org","signer_ca_cn":"root cn","signer_ca_pubkey":"11111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111"},{"slot_id":13,"slot_type":"public","key_load_config":"load","slot_lock":"disabled","data":null},{"slot_id":14,"slot_type":"public","key_load_config":"load","slot_lock":null,"data":null},{"slot_id":15,"slot_type":"public","key_load_config":"load","slot_lock":"disabled","data":null}],"sboot_latch":"disabled","man_id":"01","part_number":"ATECC608B-MAHAA-T","otp_zone":"77644E78416A61650000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"}'
    xml = TFLXTLSXMLUpdates()
    xml.update_with_user_data(config_string)
    part_number = json.loads(config_string).get("part_number")
    xml.save_root(f"{part_number}.xml")
