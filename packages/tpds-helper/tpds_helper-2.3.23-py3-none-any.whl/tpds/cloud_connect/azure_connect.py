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

import json
import os
import yaml
import base64
from cryptography import x509
from datetime import datetime, timezone, timedelta
from pathlib import Path
from tpds.certs.cert import Cert
from tpds.tp_utils.tp_settings import TPSettings
from tpds.tp_utils.tp_keys import TPAsymmetricKey
from tpds.manifest import ManifestIterator, Manifest
from tpds.certs.cert_utils import (
    get_certificate_CN,
    get_certificate_thumbprint,
    random_cert_sn
)
from .cloud_connect import CloudConnect
from .azure_sdk import AzureSDK_IotAuthentication


class AzureConnectBase(CloudConnect):
    def __init__(self, SDK):
        self.az_sdk = SDK()
        self.az_credentials = {}
        self.az_resource_group = ""
        self.az_iot_hub = ""
        self.az_subscription_id = ""
        self.creds_file = os.path.join(TPSettings().get_base_folder(), 'azure_credentials.yaml')

    def login(self):
        self.az_sdk.login()

    def save_credentials(self):
        Path(self.creds_file).write_text(
            yaml.dump(self.az_credentials, sort_keys=False))

    def az_group_create(self, resource_group: str):
        print("Checking if the resource group exists...")
        if (not self.az_sdk.check_resource_existence(resource_group)):
            print("Creating the Resource group...")
            try:
                self.az_sdk.create_resource_group(resource_group)
                print("Azure Resource group created successfully")
            except BaseException as e:
                # print the error message in teriminal log
                print(e)
                raise ValueError(
                    '''
                    The creation of the resource group has failed. For more information,
                    please check the terminal for detailed error messages.
                    Try Creating manually in the Azure Portal.
                    For additional guidance, please refer to the usecase helper.
                    '''
                )
        else:
            print("Ok")

    def az_hub_create(self, resource_group: str, iot_hub: str):
        print("Checking if the IoT Hub exists...")
        hubInstance = self.az_sdk.get_iothub(resource_group, iot_hub)
        if (hubInstance is None):
            print("Creating the iot Hub.....")
            print("Please wait, this may take up to 2 minutes...")
            try:
                self.az_sdk.create_iot_hub(resource_group, iot_hub)
                print("Hub creation was successful")
            except BaseException as e:
                raise ValueError(
                    "Hub creation creation failed with {}".format(e))
        else:
            print("Ok")

    def set_subscription_id(self, subscription_id):
        """
        Setup Azure Client using subscription ID
        """
        if (not self.az_sdk.is_subscription_valid(subscription_id)):
            raise ValueError("Subscription is not valid or does not exist.")

        self.az_subscription_id = subscription_id
        self.az_sdk.setup_client(self.az_subscription_id)


class AzureConnect(AzureConnectBase):
    def __init__(self):
        super().__init__(AzureSDK_IotAuthentication)
        self.az_credentials = {
            'title': 'Azure IoT Credentials',
            'subscription_id': '',
            'resource_group': '',
            'iot_hub': '',
        }

        if not os.path.exists(self.creds_file):
            self.save_credentials()
        else:
            with open(self.creds_file, 'r') as f:
                self.az_credentials = yaml.safe_load(f)

    def connect_azure(self, resource_group: str, iot_hub: str):
        self.az_resource_group = resource_group
        self.az_iot_hub = iot_hub
        self.az_sdk.connect_azure(self.az_resource_group, self.az_iot_hub)

    def register_device_as_self_signed(self, device_cert: str) -> None:
        """
        Method register device with authentication method as
        X509 self signed authentication. In this method, it will
        register device certificate thumbprint to Azure

        Inputs:
              device_cert      device certificate to be registered
        """
        device_id = get_certificate_CN(device_cert)
        thumbprint = get_certificate_thumbprint(device_cert)

        if self.is_device_registered(device_id):
            self.delete_registered_device(device_id)

        print('Registering device with thumbprint {}...'.format(
              thumbprint), end='')
        self.az_sdk.register_device_with_x509(
            device_id, thumbprint, thumbprint)
        print('OK')

    def register_device_as_CA_signed(self, device_cert: str) -> None:
        """
        Method register device with authentication method as
        X509 CA signed authentication. In this method, device certificate
        common name is registered as device id

        Inputs:
              device_cert     device certificate to be registered
        """
        device_id = get_certificate_CN(device_cert)

        if self.is_device_registered(device_id):
            self.delete_registered_device(device_id)

        print('Registering device with id {}...'.format(device_id), end='')
        self.az_sdk.register_device_with_CA(device_id)
        print('OK')

    def register_device_from_manifest(
            self, device_manifest, device_manifest_ca,
            key_slot=0, as_self_signed=True):
        """
        Method register device from given manifest
        Inputs:
              device_manifest     manifest contains certs and public keys
              device_manifest_ca  manifest signer key
              key_slot            slot where device private key present

            return true if device registered successfully else false
        """
        if os.path.exists(device_manifest) \
                and device_manifest.endswith('.json'):
            with open(device_manifest) as json_data:
                device_manifest = json.load(json_data)

        if not isinstance(device_manifest, list):
            raise ValueError('Unsupport manifest format to process')

        manifest_ca = Cert()
        manifest_ca.set_certificate(device_manifest_ca)
        iterator = ManifestIterator(device_manifest)
        print('Number of Devices: {}'.format(iterator.index))

        while iterator.index != 0:
            se = Manifest().decode_manifest(
                iterator.__next__(), manifest_ca.certificate)
            se_certs = Manifest().extract_public_data_pem(se)
            slot = next((sub for sub in se_certs if sub.get(
                'id') == str(key_slot)), None)
            no_of_certs = len(slot.get('certs'))
            if no_of_certs:
                device_cert = 'device.crt'
                with open(device_cert, 'w') as f:
                    f.write(slot.get('certs')[no_of_certs - 2])
                    f.close()

                if as_self_signed:
                    self.register_device_as_self_signed(device_cert)
                else:
                    self.register_device_as_CA_signed(device_cert)

    def is_device_registered(self, device_id: str) -> bool:
        """
        Method checks whether device is registered or not
        Inputs:
            device_id      device certificate common name

            return true if device is registered else false
        """
        devices = self.az_sdk.get_devices()

        # filter the device_ids from the devices
        device_ids = [dev.device_id for dev in devices]

        return device_id in device_ids

    def delete_registered_device(self, device_id: str) -> None:
        '''
        Method delete the registered device in Azure IoT hub
        Inputs:
            device_id        device certificate common name
        '''
        print(f'Try Deleting device: {device_id}', end='')
        self.az_sdk.delete_device(device_id)
        print('OK')

    def register_signer_certificate(
            self, signer_cert, signer_key='', verify_cert=''):
        '''
        Method register the signer certificate in Azure IoT hub
        Steps followed to register signer:
        1. Upload signer certificate
        2. Get verification code and generate verification certificate
        3. Upload verification certificate

        Inputs:
              signer_cert    signer certificate to be registered
              signer_key     key to sign the verification cert
                             for proof of possession
              verify_cert    verification cert to be uploaded
                             to validate signer certificate
        '''
        if not signer_key and not signer_cert:
            raise ValueError(
                'Either signer key or verify cert required to register')

        if self.is_signer_registered(signer_cert):
            self.delete_registered_signer(signer_cert)

        self.upload_signer_cert(signer_cert)

        if not verify_cert:
            verify_cert = 'verify_cert.cer'
            self.get_verification_cert(signer_key, signer_cert, verify_cert)

        self.activate_signer_cert(signer_cert, verify_cert)

    def upload_signer_cert(self, signer_cert):
        """
        Method upload signer certificate to Azure IoT hub

        Inputs:
            signer_cert      signer certificate
        """
        if not isinstance(signer_cert, str) or not os.path.exists(signer_cert):
            raise FileNotFoundError("Unknown Signer certificate type")

        signer_name = 'signer_{}'.format(
            get_certificate_thumbprint(signer_cert))

        # Upload the signer certificate
        print('Uploading signer certificate to Azure IoT hub...', end='')

        with open(signer_cert, 'rb') as f:
            data = f.read()
            cert_content = base64.b64encode(data).decode('utf-8')
            self.az_sdk.create_certificate(self.az_resource_group, self.az_iot_hub, signer_name, cert_content)
        print('OK')

    def activate_signer_cert(self, signer_cert, verify_cert):
        """
        Method upload verification certificate, by validating this
        certificate, signer certificate will be registered successfully

        Inputs:
            signer_cert    path to signer certificate
            verify_cert    path to verification certificate
        """
        if not isinstance(signer_cert, str) or not os.path.exists(signer_cert):
            raise FileNotFoundError("Unknown Signer certificate type")

        if (not isinstance(verify_cert, str) or not os.path.exists(verify_cert)):
            raise FileNotFoundError("Unknown Verification certificate type")

        signer_name = 'signer_{}'.format(
            get_certificate_thumbprint(signer_cert))
        etag = self.get_signer_certificate_etag(signer_cert)

        # Uploading verification certificate
        print('Uploading verification certificate to azure IoT hub...', end='')

        with open(verify_cert, 'rb') as f:
            data = f.read()
            cert_content = base64.b64encode(data).decode('utf-8')
            self.az_sdk.verify_certificate(self.az_resource_group, self.az_iot_hub, signer_name, cert_content, etag)
        print('OK')

    def is_signer_registered(self, signer_cert):
        """
        Method check whether signer certificate is registered or not
        Inputs:
              signer_cert    signer certificate

            return true if signer certificate registered else false
        """
        signer_fingerprint = get_certificate_thumbprint(signer_cert)

        thumbprints = self.az_sdk.get_certificates_thumbprint(self.az_resource_group, self.az_iot_hub)
        return (signer_fingerprint in thumbprints)

    def delete_registered_signer(self, signer_cert):
        """
        Method delete the registered signer certificate in Azure IoT hub
        Inputs:
             signer_cert      signer certificate registered already
        """
        signer_name = 'signer_{}'.format(
            get_certificate_thumbprint(signer_cert))

        # Get eTag
        eTag = self.get_signer_certificate_etag(signer_cert)

        print('Try Deleting Signer...', end='')
        self.az_sdk.delete_certificate(self.az_resource_group, self.az_iot_hub, signer_name, eTag)
        print('OK')

    def get_verification_cert(self, signer_key, signer_cert, file=''):
        """
        Method get the verification code and generate verification cert

        Inputs:
              signer_key      signer key which sign the verification cert
              signer_cert     signer certificate
              file            path where verification cert loaded

            return verification certificate
        """
        ca_key = TPAsymmetricKey(signer_key)
        ca_cert = Cert()
        ca_cert.set_certificate(signer_cert)

        etag_id = self.get_signer_certificate_etag(signer_cert)
        signer_fingerprint = get_certificate_thumbprint(signer_cert)
        signer_name = 'signer_{}'.format(signer_fingerprint)

        # Request a verification code for signer certificate
        print('Getting verification code from azure IoT hub...', end='')
        reg_code = self.az_sdk.generate_verification_code(self.az_resource_group, self.az_iot_hub, signer_name, etag_id)
        print('{}'.format(reg_code))

        # Generate a verification certificate around the registration code
        # (subject common name)
        print('Generating signer CA verification certificate...', end='')
        verify_cert = Cert()
        verify_cert.builder = x509.CertificateBuilder()
        verify_cert.builder = verify_cert.builder.serial_number(
            random_cert_sn(16))
        verify_cert.builder = verify_cert.builder.issuer_name(
            ca_cert.certificate.subject)
        verify_cert.builder = verify_cert.builder.not_valid_before(
            datetime.utcnow().replace(tzinfo=timezone.utc))
        verify_cert.builder = verify_cert.builder.not_valid_after(
            verify_cert.builder._not_valid_before + timedelta(days=1))
        verify_cert.builder = verify_cert.builder.subject_name(
            x509.Name(
                [x509.NameAttribute(x509.oid.NameOID.COMMON_NAME, reg_code)]))
        verify_cert.builder = verify_cert.builder.public_key(
            ca_cert.certificate.public_key())
        verify_cert.sign_builder(ca_key.get_private_key())
        print('OK')

        if file:
            Path(file).write_bytes(verify_cert.get_certificate_in_pem())

        return verify_cert

    def get_signer_certificate_etag(self, signer_cert):
        """
        Methos get the etag from Azure IoT hub for given signer certificate
        Inputs:
              signer_cert       signer certificate
        Outputs:
              etag              etag for signer certifcate
        """
        signer_name = 'signer_{}'.format(
            get_certificate_thumbprint(signer_cert))

        # get eTag
        return self.az_sdk.get_certificate_etag(self.az_resource_group, self.az_iot_hub, signer_name)


if __name__ == '__main__':
    pass
