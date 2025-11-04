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

# import os, sys
# sys.path.append(os.path.normpath( os.path.join(os.getcwd(), *([".."] * 3), 'tpds_helper')))
# sys.path.append(os.path.normpath( os.path.join(os.getcwd(), *([".."] * 3), 'tpds_core')))
import struct
from datetime import datetime, timezone
from pathlib import Path
import cryptoauthlib as cal
import lxml.etree as ET
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding

from tpds.certs import Cert, WPCCertDef
from tpds.certs.cert_utils import get_backend, get_device_public_key, pubkey_cert_sn, random_cert_sn
from tpds.certs.ext_builder import TimeFormat
from tpds.proto_provision.ecc_provision import ECCProvision
from tpds.secure_element.constants import Constants
from tpds.tp_utils.tp_keys import TPAsymmetricKey


class TFLXWPCProvision(ECCProvision):
    def __init__(self, xml_file):
        self.root = ET.parse(xml_file).getroot()

        if "ECC" not in self.root.find("PartNumber").text:
            raise ValueError("Unsupported Part Number in XML")
        interface = self.root.find("Device").find("ConfigurationZone").find("I2CEnable").text
        address = self.root.find("Device").find("ConfigurationZone").find("I2CAddress").text

        cfg = cal.cfg_ateccx08a_kithid_default()
        if interface == "01":
            cfg.cfg.atcahid.dev_interface = int(cal.ATCAKitType.ATCA_KIT_I2C_IFACE)
        else:
            cfg.cfg.atcahid.dev_interface = int(cal.ATCAKitType.ATCA_KIT_SWI_IFACE)

        cfg.cfg.atcahid.dev_identity = int(address, base=16)
        super().__init__(cfg)

        if not self.element.is_config_zone_locked():
            raise ValueError("TFLXWPC cannot have unlocked config zone")
        if not self.element.is_data_zone_locked():
            raise ValueError("TFLXWPC cannot have unlocked data zone")

    def provision_non_cert_slots(self):
        self.data_zone = self.root.find("Device").find("DataZone")
        slot_config = self.root.find("Device").find("ConfigurationZone").find("SlotConfigurations")
        self.slot_config = {}
        for index, element in enumerate(slot_config.iter("SlotConfiguration")):
            self.slot_config.update({index: element.text.replace(" ", "")})
        self.slot_modes = ["GenKey", "Secret", "Random", "Public"]
        for element in list(self.data_zone):
            if element.attrib.get("Mode") == "GenKey":
                slot_index = int(element.attrib.get("Index"), base=16)
                slot_config = self.slot_config.get(slot_index)
                if slot_config[2:3] == "2":
                    self.perform_genkey(slot_index)
            elif element.attrib.get("Mode") == "Secret":
                slot_index = int(element.attrib.get("Index"), base=16)
                slot_data = bytearray.fromhex(element.find("Data").text)
                slot_config = self.slot_config.get(slot_index)
                encrypting_slot = encrypting_slot_data = None
                if slot_config[2:3] == "4":
                    encrypting_slot = int(slot_config[3:4], base=16)
                    encrypting_element = list(self.data_zone)[encrypting_slot]
                    slot_data_attr = encrypting_element.find("Data")
                    encrypting_slot_data = bytearray.fromhex(slot_data_attr.text)
                    if slot_data_attr.attrib.get("Size") == "36":
                        encrypting_slot_data = encrypting_slot_data[:32]
                    elif slot_data_attr.attrib.get("Size") == "72":
                        encrypting_slot_data = encrypting_slot_data[:64]
                    self.perform_slot_write(encrypting_slot, encrypting_slot_data)

                slot_data_attr = element.find("Data")
                if slot_data_attr.attrib.get("Size") == "36":
                    slot_data = slot_data[:32]
                elif slot_data_attr.attrib.get("Size") == "72":
                    slot_data = slot_data[:64]
                self.perform_slot_write(
                    slot_index, slot_data, encrypting_slot, encrypting_slot_data
                )
            elif element.attrib.get("Mode") == "Random":
                slot_index = element.attrib.get("Index")
            elif element.attrib.get("Mode") == "Public":
                slot_index = int(element.attrib.get("Index"), base=16)
                slot_config = self.slot_config.get(slot_index)
                slot_data = bytearray.fromhex(element.find("Data").text)
                public_key_control_bytes = bytearray(4)
                if slot_config[2:3] == "1":
                    assert (
                        cal.atcab_read_zone(
                            Constants.ATCA_DATA_ZONE,
                            slot_index,
                            0,
                            0,
                            public_key_control_bytes,
                            len(public_key_control_bytes),
                        )
                        == cal.Status.ATCA_SUCCESS
                    ), "Reading public key validation state - failed"
                if public_key_control_bytes[0] == 0x00:
                    self.perform_slot_write(slot_index, slot_data)
                else:
                    print("Validated Public key encountered, skipping the slot!")

    def provision_cert_slots(
        self, signer_ca=None, signer_ca_key=None, device_ca=None, device_ca_key=None
    ):
        signer_ca_key = TPAsymmetricKey(signer_ca_key)
        device_ca_key = TPAsymmetricKey(device_ca_key)

        self.comp_certs = self.root.find("CompressedCerts")
        device_cert_element = self.comp_certs.find("""CompressedCert[@ChainLevel='0']""")
        signer_cert_element = self.comp_certs.find("""CompressedCert[@ChainLevel='1']""")
        single_signer_id = device_cert_element.attrib.get("SingleSignerID")
        ptmc_seq = f"{single_signer_id[7:11]}-{single_signer_id[-2:]}"
        for element in device_cert_element.findall("Element"):
            if element.attrib.get("Name") == "RSID":
                rsid = element.attrib.get("CounterStart")
        for element in signer_cert_element.findall("Element"):
            if element.attrib.get("Name") == "qiPolicy":
                qi_policy_slot = int("".join(filter(str.isdigit, element.attrib.get("DeviceLoc"))))
                qi_policy_slot_offset = int(
                    "".join(filter(str.isdigit, element.attrib.get("Offset")))
                )
        qi_policy_bytes = bytearray.fromhex(list(self.data_zone)[qi_policy_slot].find("Data").text)[
            qi_policy_slot_offset : qi_policy_slot_offset + 4
        ]
        device_template = Cert()
        device_template.set_certificate(
            x509.load_der_x509_certificate(
                bytes.fromhex(device_cert_element.find("TemplateData").text), backend=get_backend
            )
        )

        new_root = Cert()
        if signer_ca is not None:
            new_root.set_certificate(signer_ca)
        else:
            new_root.builder = new_root.builder.subject_name(
                x509.Name([x509.NameAttribute(x509.oid.NameOID.COMMON_NAME, "WPCCA1")])
            )
            new_root.builder = new_root.builder.issuer_name(
                x509.Name([x509.NameAttribute(x509.oid.NameOID.COMMON_NAME, "WPCCA1")])
            )
            new_root.builder = new_root.builder.not_valid_before(
                datetime(2021, 3, 3, 16, 4, 1, tzinfo=timezone.utc)
            )
            new_root.builder = new_root.builder.not_valid_after(
                datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
            )
            new_root.builder = new_root.builder.public_key(signer_ca_key.get_public_key())
            new_root.builder = new_root.builder.serial_number(random_cert_sn(8))
            new_root.builder = new_root.builder.add_extension(
                x509.BasicConstraints(ca=True, path_length=None), critical=True
            )
            new_root.sign_builder(signer_ca_key.private_key)

        new_signer = Cert()
        if device_ca is not None:
            new_signer.set_certificate(device_ca)
        else:
            new_signer.builder = new_signer.builder.issuer_name(new_root.certificate.subject)
            new_signer.builder = new_signer.builder.subject_name(
                x509.Name([x509.NameAttribute(x509.oid.NameOID.COMMON_NAME, ptmc_seq)])
            )
            new_signer.builder = new_signer.builder.not_valid_before(datetime.utcnow())
            new_signer.builder = new_signer.builder.not_valid_after(
                datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
                format=TimeFormat.GENERALIZED_TIME,
            )
            new_signer.builder = new_signer.builder.public_key(device_ca_key.get_public_key())
            new_signer.builder = new_signer.builder.serial_number(random_cert_sn(8))
            new_signer.builder = new_signer.builder.add_extension(
                x509.BasicConstraints(ca=True, path_length=None), critical=True
            )
            wpc_qi_policy_extension_value = bytes([0x04, len(qi_policy_bytes)]) + qi_policy_bytes
            new_signer.builder = new_signer.builder.add_extension(
                x509.UnrecognizedExtension(
                    x509.ObjectIdentifier("2.23.148.1.1"), wpc_qi_policy_extension_value
                ),
                critical=True,
            )
            new_signer.sign_builder(signer_ca_key.private_key)

        device_pubkey = bytearray(64)
        status = cal.atcab_get_pubkey(0, device_pubkey)
        assert status == cal.Status.ATCA_SUCCESS, "atcab_get_pubkey failed"
        device_pubkey = get_device_public_key(device_pubkey)
        device_pubkey = ec.EllipticCurvePublicNumbers(
            x=int(device_pubkey[:64], 16), y=int(device_pubkey[64:], 16), curve=ec.SECP256R1()
        ).public_key(get_backend())

        new_device = Cert()
        new_device.builder = new_device.builder.issuer_name(new_signer.certificate.subject)
        new_device.builder = new_device.builder.not_valid_before(
            datetime.utcnow().replace(tzinfo=timezone.utc, minute=0, second=0),
            format=TimeFormat.GENERALIZED_TIME,
        )
        new_device.builder = new_device.builder.not_valid_after(
            datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
            format=TimeFormat.GENERALIZED_TIME,
        )
        new_device.builder = new_device.builder.subject_name(device_template.certificate.subject)
        new_device.builder = new_device.builder.public_key(device_pubkey)
        new_device.builder = new_device.builder.serial_number(pubkey_cert_sn(8, new_device.builder))

        rsid_bytes = int(rsid, 16).to_bytes(9, byteorder="big", signed=False)
        rsid_extension_value = bytes([0x04, len(rsid_bytes)]) + rsid_bytes
        new_device.builder = new_device.builder.add_extension(
            x509.UnrecognizedExtension(x509.ObjectIdentifier("2.23.148.1.2"), rsid_extension_value),
            critical=True,
        )
        new_device.sign_builder(device_ca_key.private_key)

        # Verify new cert chain
        assert (
            new_root.is_signature_valid(signer_ca_key.get_public_key())
            and new_signer.is_signature_valid(signer_ca_key.get_public_key())
            and new_device.is_signature_valid(device_ca_key.get_public_key())
        ), "Certificate chain verification failed"

        # Store keys and certs to files
        signer_ca_key.get_private_pem(Path('root.key'))
        device_ca_key.get_private_pem(Path('signer.key'))
        certs_txt = new_root.get_certificate_in_text()\
            + '\n\n' + new_signer.get_certificate_in_text()\
            + '\n\n' + new_device.get_certificate_in_text()
        Path('certificates.txt').write_text(certs_txt)
        Path('root.crt').write_bytes(
            new_root.get_certificate_in_pem())
        Path('signer.crt').write_bytes(
            new_signer.get_certificate_in_pem())
        Path('device.crt').write_bytes(
            new_device.get_certificate_in_pem())

        root_bytes = new_root.certificate.public_bytes(encoding=Encoding.DER)
        mfg_bytes = new_signer.certificate.public_bytes(encoding=Encoding.DER)
        puc_bytes = new_device.certificate.public_bytes(encoding=Encoding.DER)

        # Setup hash engine for root cert digest
        root_hash = hashes.Hash(hashes.SHA256(), backend=default_backend())
        root_hash.update(root_bytes)
        root_digest = root_hash.finalize()[:32]

        length = 2 + len(root_digest) + len(mfg_bytes) + len(puc_bytes)
        cert_chain = b""
        cert_chain += struct.pack(">H", length)
        cert_chain += root_digest
        cert_chain += mfg_bytes
        cert_chain += puc_bytes

        chain_hash = hashes.Hash(hashes.SHA256(), backend=default_backend())
        chain_hash.update(cert_chain)
        chain_digest = chain_hash.finalize()[:32]

        # Write compressed certs to device
        crt_template = dict()
        cert_def = WPCCertDef()
        cert_def.set_certificate(new_signer.certificate, new_root.certificate, template_id=1)
        crt_template.update({"signer": cert_def.get_py_definition()})
        cert_def.get_c_definition(True)
        cert_def = WPCCertDef()
        cert_def.set_certificate(new_device.certificate, new_signer.certificate, template_id=2)
        crt_template.update({"device": cert_def.get_py_definition()})
        cert_def.get_c_definition(True)

        assert (
            cal.atcacert_write_cert(crt_template["signer"], mfg_bytes, len(mfg_bytes))
            == cal.Status.ATCA_SUCCESS
        ), "Loading MFG certificate into slot failed"
        assert (
            cal.atcacert_write_cert(crt_template["device"], puc_bytes, len(puc_bytes))
            == cal.Status.ATCA_SUCCESS
        ), "Loading PUC certificate into slot failed"
        assert (
            cal.atcab_write_bytes_zone(
                Constants.ATCA_DATA_ZONE, 3, 0, chain_digest, len(chain_digest)
            )
            == cal.Status.ATCA_SUCCESS
        ), "Loading Cert chain digest into slot failed"

        # print(f'Chain digest: {chain_digest.hex().upper()}')
        # read_data = [
        #     {'slot':3, 'size': 36},     {'slot':4, 'size': 36},     {'slot':5, 'size': 36},
        #     {'slot':9, 'size': 72},     {'slot':13, 'size': 72},     {'slot':14, 'size': 72},
        # ]
        # for slot_info in read_data:
        #     slot_id = slot_info.get('slot')
        #     slot_size = slot_info.get('size')
        #     buffer = bytearray(slot_size)
        #     assert cal.atcab_read_bytes_zone(
        #         Constants.ATCA_DATA_ZONE, slot_id, 0,
        #         buffer, len(buffer)) \
        #         == cal.Status.ATCA_SUCCESS, \
        #         "Reading Chain digest from slot failed"
        #     print(f'Data from Slot{slot_id} with size {slot_size} is {buffer.hex().upper()}')


# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == "__main__":
    test_prov = TFLXWPCProvision("ATECC608A-xxxxxx-T.xml")
    print(test_prov.element.get_device_details())
    test_prov.provision_non_cert_slots()
    test_prov.provision_cert_slots()
    pass
