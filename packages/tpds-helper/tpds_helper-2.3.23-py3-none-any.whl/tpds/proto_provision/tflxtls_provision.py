# -*- coding: utf-8 -*-
# 2019 to present - Copyright Microchip Technology Inc. and its subsidiaries.

# Subject to your compliance with these terms, you may use Microchip software
# and any derivatives exclusively with Microchip products. It is your
# responsibility to comply with third party license terms applicable to your
# use of third party software (including open source software) that may
# accompany Microchip software.

from datetime import datetime, timezone
from pathlib import Path

import cryptoauthlib as cal
import lxml.etree as ET
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import ec

from tpds.certs import Cert, TFLEXCerts
from tpds.certs.cert_utils import (
    get_backend,
    get_device_public_key,
    get_device_sn_number,
    pubkey_cert_sn,
)
from tpds.certs.ext_builder import TimeFormat
from tpds.secure_element.constants import Constants
from tpds.tp_utils.tp_keys import TPAsymmetricKey

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
from .ecc_provision import ECCProvision


class TFLXTLSProvision(ECCProvision):
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
            raise ValueError("TFLXTLS cannot have unlocked config zone")
        if not self.element.is_data_zone_locked():
            raise ValueError("TFLXTLS cannot have unlocked data zone")

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
                slot_data = element.find("Data").text
                if slot_data is None:
                    continue
                slot_data = bytearray.fromhex(slot_data)
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
        self, signer_ca=None, signer_ca_key=None, device_ca=None, device_ca_key=None, use_extended_date: bool = True
    ):
        signer_ca_key = TPAsymmetricKey(signer_ca_key)
        device_ca_key = TPAsymmetricKey(device_ca_key)

        self.comp_certs = self.root.find("CompressedCerts")
        signer_cert_element = self.comp_certs.find("""CompressedCert[@ChainLevel='1']""")
        signer_template = bytearray.fromhex(signer_cert_element.find("TemplateData").text)
        signer_template = x509.load_der_x509_certificate(bytes(signer_template), get_backend())
        validity = int(signer_cert_element.attrib.get("ValidYears"))

        new_root = Cert()
        if signer_ca is not None:
            new_root.set_certificate(signer_ca)
        else:
            new_root.builder = new_root.builder.subject_name(signer_template.issuer)
            new_root.builder = new_root.builder.issuer_name(signer_template.issuer)
            new_root.builder = new_root.builder.not_valid_before(
                datetime.utcnow().replace(minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
            )
            new_root.builder = new_root.builder.not_valid_after(
                new_root.builder._not_valid_before.replace(
                    year=new_root.builder._not_valid_before.year + 40
                )
            )
            new_root.builder = new_root.builder.public_key(signer_ca_key.get_public_key())
            new_root.builder = new_root.builder.serial_number(
                pubkey_cert_sn(16, new_root.builder, use_extended_date)
            )
            new_root.builder = new_root.builder.add_extension(
                x509.SubjectKeyIdentifier.from_public_key(signer_ca_key.get_public_key()),
                critical=False,
            )
            new_root.builder = new_root.builder.add_extension(
                x509.AuthorityKeyIdentifier.from_issuer_public_key(signer_ca_key.get_public_key()),
                critical=False,
            )
            new_root.builder = new_root.builder.add_extension(
                x509.BasicConstraints(ca=True, path_length=None), critical=True
            )
            new_root.sign_builder(signer_ca_key.private_key)

        new_signer = Cert()
        if device_ca is not None:
            new_signer.set_certificate(device_ca)
        else:
            new_signer.builder = new_signer.builder.subject_name(signer_template.subject)
            new_signer.builder = new_signer.builder.issuer_name(signer_template.issuer)
            new_signer.builder = new_signer.builder.not_valid_before(
                datetime.utcnow().replace(minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
            )
            if validity == 0:
                new_signer.builder = new_signer.builder.not_valid_after(
                    datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
                    format=TimeFormat.GENERALIZED_TIME,
                )
            else:
                new_signer.builder = new_signer.builder.not_valid_after(
                    new_signer.builder._not_valid_before.replace(
                        year=new_signer.builder._not_valid_before.year + validity
                    ),
                    format=TimeFormat.GENERALIZED_TIME,
                )
            new_signer.builder = new_signer.builder.public_key(device_ca_key.get_public_key())
            new_signer.builder = new_signer.builder.serial_number(
                pubkey_cert_sn(16, new_signer.builder, use_extended_date)
            )
            for extn in signer_template.extensions:
                if extn.oid._name == "subjectKeyIdentifier":
                    new_signer.builder = new_signer.builder.add_extension(
                        x509.SubjectKeyIdentifier.from_public_key(device_ca_key.get_public_key()),
                        extn.critical,
                    )
                elif extn.oid._name == "authorityKeyIdentifier":
                    new_signer.builder = new_signer.builder.add_extension(
                        x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(
                            new_root.certificate.extensions.get_extension_for_class(
                                x509.SubjectKeyIdentifier
                            ).value
                        ),
                        extn.critical,
                    )
                else:
                    new_signer.builder = new_signer.builder.add_extension(extn.value, extn.critical)
            new_signer.sign_builder(signer_ca_key.private_key)

        device_cert_element = self.comp_certs.find("""CompressedCert[@ChainLevel='0']""")
        device_template = bytearray.fromhex(device_cert_element.find("TemplateData").text)
        device_template = x509.load_der_x509_certificate(bytes(device_template), get_backend())
        validity = int(device_cert_element.attrib.get("ValidYears"))

        updated_subject = device_template.subject
        for element in device_cert_element.findall("Element"):
            if element.attrib.get("Name") == "SN03":
                subject_attr = []
                for attr in device_template.subject:
                    if attr.oid == x509.oid.NameOID.COMMON_NAME:
                        prefix = device_template.subject.get_attributes_for_oid(
                            x509.oid.NameOID.COMMON_NAME
                        )[0].value[:-18]
                        attr = x509.NameAttribute(
                            x509.oid.NameOID.COMMON_NAME,
                            get_device_sn_number(self.element.get_device_serial_number(), prefix),
                        )
                    subject_attr.append(attr)
                updated_subject = x509.Name(subject_attr)

        device_pubkey = bytearray(64)
        status = cal.atcab_get_pubkey(0, device_pubkey)
        assert status == cal.Status.ATCA_SUCCESS, "atcab_get_pubkey failed"
        device_pubkey = get_device_public_key(device_pubkey)
        device_pubkey = ec.EllipticCurvePublicNumbers(
            x=int(device_pubkey[:64], 16), y=int(device_pubkey[64:], 16), curve=ec.SECP256R1()
        ).public_key(get_backend())

        new_device = Cert()
        new_device.builder = new_device.builder.issuer_name(signer_template.subject)
        new_device.builder = new_device.builder.not_valid_before(
            datetime.utcnow().replace(minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
        )
        if validity == 0:
            new_device.builder = new_device.builder.not_valid_after(
                datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
                format=TimeFormat.GENERALIZED_TIME,
            )
        else:
            new_device.builder = new_device.builder.not_valid_after(
                new_device.builder._not_valid_before.replace(
                    year=new_device.builder._not_valid_before.year + validity
                ),
                format=TimeFormat.GENERALIZED_TIME,
            )
        new_device.builder = new_device.builder.subject_name(updated_subject)
        new_device.builder = new_device.builder.public_key(device_pubkey)
        new_device.builder = new_device.builder.serial_number(
            pubkey_cert_sn(16, new_device.builder, use_extended_date)
        )
        for extn in device_template.extensions:
            if extn.oid._name == "subjectKeyIdentifier":
                new_device.builder = new_device.builder.add_extension(
                    x509.SubjectKeyIdentifier.from_public_key(device_pubkey), extn.critical
                )
            elif extn.oid._name == "authorityKeyIdentifier":
                new_device.builder = new_device.builder.add_extension(
                    x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(
                        new_signer.certificate.extensions.get_extension_for_class(
                            x509.SubjectKeyIdentifier
                        ).value
                    ),
                    extn.critical,
                )
            else:
                new_device.builder = new_device.builder.add_extension(extn.value, extn.critical)
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

        # Write compressed certs to device
        certs = TFLEXCerts()
        certs.set_tflex_certificates(
            root_cert=new_root.certificate,
            signer_cert=new_signer.certificate,
            device_cert=new_device.certificate,
        )
        template = certs.get_tflex_py_definitions()
        certs.save_tflex_c_definitions()
        assert (
            cal.atcacert_write_cert(
                template.get("signer"),
                certs.signer.get_certificate_in_der(),
                len(certs.signer.get_certificate_in_der()),
            )
            == cal.Status.ATCA_SUCCESS
        ), "Loading signer certificate into slot failed"
        assert (
            cal.atcacert_write_cert(
                template.get("device"),
                certs.device.get_certificate_in_der(),
                len(certs.device.get_certificate_in_der()),
            )
            == cal.Status.ATCA_SUCCESS
        ), "Loading device certificate into slot failed"


# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == "__main__":
    pass
