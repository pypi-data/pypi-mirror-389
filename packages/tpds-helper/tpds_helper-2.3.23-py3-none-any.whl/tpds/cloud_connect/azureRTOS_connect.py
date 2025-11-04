import json
import yaml
import os
import re
import sys
import unicodedata
import struct
import ctypes
import base64
from cryptography.hazmat.primitives.serialization import Encoding
from tpds.certs.cert import Cert
from tpds.certs.cert_utils import get_certificate_CN
from tpds.manifest import ManifestIterator, Manifest
from tpds.secure_element import ECC608B
import cryptoauthlib as cal
from tpds.secure_element.constants import Constants
from .azure_sdk import AzureSDK_RTOS
from .azure_connect import AzureConnectBase


ATCA_SUCCESS = 0x00


def make_valid_filename(s):
    """
    Convert an arbitrary string into one that can be used in an ascii filename.
    """
    if sys.version_info[0] <= 2:
        if not isinstance(s, str):
            s = str(s).decode("utf-8")
    else:
        s = str(s)
    # Normalize unicode characters
    s = unicodedata.normalize("NFKD", s).encode(
        "ascii", "ignore").decode("ascii")
    # Remove non-word and non-whitespace characters
    s = re.sub(r"[^\w\s-]", "", s).strip()
    # Replace repeated whitespace with an underscore
    s = re.sub(r"\s+", "_", s)
    # Replace repeated dashes with a single dash
    s = re.sub(r"-+", "-", s)
    return s


class AzurertosConnect(AzureConnectBase):
    def __init__(self):
        super().__init__(AzureSDK_RTOS)
        self.cfg = cal.ATCAIfaceCfg()
        self.dps_name = ""
        self.az_credentials = {
            'title': 'Azure RTOS Credentials',
            'subscription_id': '',
            'resource_group': '',
            'iot_hub': '',
            'dps_name': '',
        }

        if not os.path.exists(self.creds_file):
            self.save_credentials()
        else:
            with open(self.creds_file, 'r') as f:
                self.az_credentials = yaml.safe_load(f)

    def connect_azure(self, resource_group: str, dps_name: str):
        self.az_resource_group = resource_group
        self.dps_name = dps_name
        self.az_sdk.connect_azure(self.az_resource_group, self.dps_name)

    def az_dps_create(self, resource_group: str, dps_name: str):
        print("Checking if the DPS exists...")
        dps_instance = self.az_sdk.get_dps(resource_group, dps_name)
        if (dps_instance is None):
            print("Creating the dps....")
            try:
                dps_instance = self.az_sdk.create_dps(resource_group, dps_name)
                print("DPS creation was successful")
            except BaseException as e:
                raise ValueError(
                    "DPS creation creation failed with {}".format(e)
                )
        else:
            print("Ok")
        self.id_Scope = dps_instance.properties.id_scope
        self.dps_name = dps_instance.name

    def register_dps(self, cert_path: str) -> None:
        enrollment = self.az_sdk.get_individual_enrollment(self.device_id)
        if enrollment is None:
            cert_content = None
            with open(cert_path, 'rb') as f:
                pem_data = f.read()
                base64_data = base64.b64encode(pem_data)
                cert_content = base64_data.decode('utf-8')
            enrollment = self.az_sdk.enroll_device(
                self.az_iot_hub,
                self.device_id, cert_content)
            print("Device enrolled successfully")
        else:
            print("Devcie is already enrolled")

    def enroll_device(self, i2c_address, port, manifest, b):
        self.element = ECC608B(i2c_address, port)
        self.serial_number = self.element.get_device_serial_number()
        self.kit_atcab_init(i2c_address, port)

        device_manifest = manifest.get("json_file")
        device_manifest_ca = manifest.get("ca_cert")

        if os.path.exists(device_manifest) and device_manifest.endswith(".json"):
            with open(device_manifest) as json_data:
                device_manifest = json.load(json_data)

        if not isinstance(device_manifest, list):
            raise ValueError("Unsupport manifest format to process")

        manifest_ca = Cert()
        manifest_ca.set_certificate(device_manifest_ca)
        iterator = ManifestIterator(device_manifest)
        print("Number of Devices: {}".format(iterator.index))

        while iterator.index != 0:
            se = Manifest().decode_manifest(
                iterator.__next__(), manifest_ca.certificate
            )
            se_certs = Manifest().extract_public_data_pem(se)
            slot = next(
                (sub for sub in se_certs if sub.get("id") == str(0)), None)
            no_of_certs = len(slot.get("certs"))
            if no_of_certs:
                device_cert = "device.crt"

                with open(device_cert, "w") as f:
                    f.write(slot.get("certs")[no_of_certs - 2])
                    f.close()

                self.device_id = get_certificate_CN(device_cert)

                filename = make_valid_filename(self.device_id) + ".pem"
                crt = Cert()
                crt.set_certificate(device_cert)
                with open(filename, "wb") as f:
                    f.write(crt.certificate.public_bytes(
                        encoding=Encoding.PEM))
                cert_path = os.path.join(os.getcwd(), filename)
                self.register_dps(cert_path)

    def kit_atcab_init(self, address, port):
        self.cfg.iface_type = int(cal.ATCAIfaceType.ATCA_UART_IFACE)
        self.cfg.devtype = int(cal.ATCADeviceType.ATECC608B)
        self.cfg.wake_delay = 1500
        self.cfg.rx_retries = 10

        self.cfg.cfg.atcauart.dev_interface = int(
            cal.ATCAKitType.ATCA_KIT_I2C_IFACE)
        self.cfg.cfg.atcauart.dev_identity = address
        if isinstance(port, str):
            self.cfg.cfg.cfg_data = ctypes.c_char_p(port.encode("ascii"))
        else:
            self.cfg.cfg.atcauart.port = port
        self.cfg.cfg.atcauart.baud = 115200
        self.cfg.cfg.atcauart.wordsize = 8
        self.cfg.cfg.atcauart.parity = 2
        self.cfg.cfg.atcauart.stopbits = 1
        assert cal.atcab_init(self.cfg) == ATCA_SUCCESS
        # Initialize the stack

    def saveDataSlot(self, address, port):
        # Saving azure data to slot 8
        dps_instance = self.az_sdk.get_dps(self.az_resource_group, self.dps_name)
        self.id_Scope = dps_instance.properties.id_scope

        self.kit_atcab_init(address, port)
        idScope_len = len(bytes(self.id_Scope, "utf-8"))
        data = struct.pack(
            "BB {var1}s ".format(var1=len(self.id_Scope)),
            address,
            idScope_len,
            bytes(self.id_Scope, "utf-8"),
        )
        bytePads = len(data) % 4
        if bytePads != 0:
            bytePads = 4 - bytePads
            data = struct.pack(
                "BB {var1}s  {bd}x".format(
                    var1=len(self.id_Scope), bd=bytePads),
                address,
                idScope_len,
                bytes(self.id_Scope, "utf-8"),
            )

        offst = 0
        block_size = 32
        end_block = block_size

        if len(data) <= block_size:
            assert (
                cal.atcab_write_bytes_zone(
                    Constants.ATCA_DATA_ZONE,
                    8,
                    offst,
                    data[offst: len(data)],
                    len(data),
                )
                == ATCA_SUCCESS
            )
            print("Saving data to slot 8 was successful")
        else:
            while end_block < len(data):
                # assert cal.atcab_write_bytes_zone(Constants.ATCA_DATA_ZONE, 8, offst, data[offst : end_block], block_size) == ATCA_SUCCESS
                assert (
                    cal.atcab_write_bytes_zone(
                        Constants.ATCA_DATA_ZONE,
                        8,
                        offst,
                        data[offst:end_block],
                        block_size,
                    )
                    == ATCA_SUCCESS
                )

                end_block += block_size
                offst += block_size
                if end_block >= len(data):
                    end_block = len(data)
                    assert (
                        cal.atcab_write_bytes_zone(
                            Constants.ATCA_DATA_ZONE,
                            8,
                            offst,
                            data[offst:end_block],
                            (end_block - offst),
                        )
                        == ATCA_SUCCESS
                    )
                    print("Saving data to slot 8 was successful")
                    break

        cal.atcab_release()

    def save_i2c_add(self, address, port):
        self.kit_atcab_init(address, port)
        data = address.to_bytes(1, "big")
        assert (
            cal.atcab_write_bytes_zone(Constants.ATCA_DATA_ZONE, 8, 0, data, 4)
            == ATCA_SUCCESS
        )
        print("Secure element address saved successfully")
        cal.atcab_release()


if __name__ == "__main__":
    pass
