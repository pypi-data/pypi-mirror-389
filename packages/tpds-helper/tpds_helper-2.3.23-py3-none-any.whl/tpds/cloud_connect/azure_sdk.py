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

import time
from azure.identity import InteractiveBrowserCredential
from azure.mgmt.resource import SubscriptionClient, ResourceManagementClient
from azure.mgmt.resource.resources.models import ResourceGroup
from azure.mgmt.iothub import IotHubClient
from azure.mgmt.iothub.models import CertificateBodyDescription, CertificateVerificationDescription, OperationInputs
from azure.mgmt.iothubprovisioningservices import IotDpsClient
from azure.iot.hub import IoTHubRegistryManager
from provisioningserviceclient import ProvisioningServiceClient
from provisioningserviceclient.models import (
    AttestationMechanism, X509Attestation,
    IndividualEnrollment, X509Certificates,
    X509CertificateWithInfo
)


class AzureSDK:
    def __init__(self):
        self.api_version = "2020-03-01"
        self.az_subscription_id = ""
        self.az_tags = {}

    def login(self):
        self.credential = InteractiveBrowserCredential(additionally_allowed_tenants="*")

        # Set Azure Active Directory Tenant ID
        subscription_client = SubscriptionClient(self.credential)
        tenants = subscription_client.tenants.list()
        self.credential._tenant_id = next(tenants).tenant_id

    def is_subscription_valid(self, subscription_id: str):
        try:
            subscription_client = SubscriptionClient(self.credential)
            subscription = subscription_client.subscriptions.get(subscription_id)
            self.az_tags = subscription.tags if subscription.tags is not None else {}
            return True
        except BaseException:
            return False

    def setup_client(self, subscription_id: str):
        self.az_subscription_id = subscription_id
        # Create IoT hub client
        self.iot_hub_client = IotHubClient(
            credential=self.credential,
            subscription_id=self.az_subscription_id,
            api_version=self.api_version
        )

        # Create Resource Client
        self.resource_client = ResourceManagementClient(
            credential=self.credential,
            subscription_id=self.az_subscription_id
        )

    def get_IoT_connection_string(self, resource_group: str, iot_hub: str):
        try:
            iothub_resource = self.iot_hub_client.iot_hub_resource.get_keys_for_key_name(
                resource_group, iot_hub, key_name="iothubowner")
            connection_string = f'HostName={iot_hub}.azure-devices.net;SharedAccessKeyName={iothub_resource.key_name};SharedAccessKey={iothub_resource.primary_key}'
        except BaseException as e:
            raise ValueError(f"Get Connection String Failed with error: {e}")

        return connection_string

    def check_resource_existence(self, resource_group: str) -> bool:
        """
        Checks whether resource group exists.
        return True if Resource exists else False
        CLI command:
        az group exists --name resourceGroup
        """
        return self.resource_client.resource_groups.check_existence(resource_group)

    def create_resource_group(self, resource_group: str):
        """
        Create a resource group.
        CLI commands:
        az group create --name resourceGroup --location location
        """
        resource = self.resource_client.resource_groups.create_or_update(
            resource_group_name=resource_group,
            parameters=ResourceGroup(location="centralus", tags=self.az_tags)
        )
        return resource

    def check_hub_name(self, iot_hub: str) -> bool:
        """
        Checks whether IoT hub name available.
        return True if HubName is available to Create else false
        """
        response = self.iot_hub_client.iot_hub_resource.check_name_availability(
            operation_inputs=OperationInputs(name=iot_hub))
        return response.name_available

    def get_iothub(self, resource_group: str, iot_hub: str):
        try:
            response = self.iot_hub_client.iot_hub_resource.get(
                resource_group_name=resource_group, resource_name=iot_hub)
        except BaseException:
            response = None
        return response

    def create_iot_hub(self, resource_group: str, iot_hub: str):
        """
        Create IoT hub
        CLI command:
        az iot hub  create --resource-group <resourceGroup> --name <hostName>
        """
        iot_hub = self.iot_hub_client.iot_hub_resource.begin_create_or_update(
            resource_group_name=resource_group,
            resource_name=iot_hub,
            iot_hub_description={'location': "centralus", 'sku': {'name': "S1", 'capacity': "1"}}
        )
        self.activate_hub(resource_group, iot_hub)
        return iot_hub

    def activate_hub(self, resource_group: str, iot_hub: str):
        """
        When creating an Azure IoT Hub, it may take some time for the hub to become fully activated
        and ready for use. To handle this situation, This method will use retry mechanism that waits
        until the hub is active before proceeding with the required steps.
        """
        TIMEOUT_SECONDS = 130  # Timeout duration in seconds
        start_time = time.time()
        while True:
            try:
                iot_hub = self.get_iothub(resource_group, iot_hub)
                if iot_hub is not None:
                    break
            except BaseException as e:
                raise ValueError(f"An error occurred: {e}")

            elapsed_time = time.time() - start_time
            if elapsed_time >= TIMEOUT_SECONDS:
                break

            time.sleep(5)


class AzureSDK_IotAuthentication(AzureSDK):
    def __init__(self):
        super().__init__()

    def connect_azure(self, resource_group: str, iot_hub: str):
        # get IoT Hub Connection String
        self.iot_connection_string = self.get_IoT_connection_string(resource_group, iot_hub)

        # create the registry manager object
        self.registry_manager = IoTHubRegistryManager.from_connection_string(
            self.iot_connection_string)

    def get_devices(self):
        """
        Get the list of devices
        cli command:
        az iot hub device-identity list --hub-name <az_IoT_hub_name>
        """
        # get the list of devices
        return self.registry_manager.get_devices()

    def delete_device(self, device_id: str):
        '''
        Method delete the registered device in Azure IoT hub
        Inputs:
            device_id        device certificate common name
        cli command:
        az iot hub device-identity delete -n <az_IoT_hub_name> -d <device_id>
        '''
        self.registry_manager.delete_device(device_id)

    def register_device_with_x509(self, device_id: str, ptp: str, stp: str):
        """
        Creates a device identity on IoTHub using X509 authentication.
        cli command:
        az iot hub device-identity create -n <az_IoT_hub_name> -d <device_id> --am x509_thumbprint --ptp <thumbprint> --stp <thumbprint>
        """
        device = self.registry_manager.create_device_with_x509(
            device_id=device_id,
            primary_thumbprint=ptp,
            secondary_thumbprint=stp,
            status="enabled"
        )
        return device

    def register_device_with_CA(self, device_id: str):
        """
        Creates a device identity on IoTHub using certificate authority.
        cli command:
        az iot hub device-identity create -n <az_IoT_hub_name> -d device_id --am x509_ca
        """
        device = self.registry_manager.create_device_with_certificate_authority(
            device_id=device_id,
            status="enabled"
        )
        return device

    def get_certificates(self, resource_group: str, iot_hub: str):
        """
        get a list of all certificates in the IoT Hub.
        cli command:
            az iot hub certificate list --hub-name <az_IoT_hub_name>
        """
        certificates = self.iot_hub_client.certificates.list_by_iot_hub(
            resource_name=iot_hub,
            resource_group_name=resource_group
        )
        return certificates

    def get_certificates_thumbprint(self, resource_group: str, iot_hub: str):
        """
        get a list of all certificates thumbprint in the IoT Hub.
        cli command:
        az iot hub certificate list --hub-name <az_IoT_hub_name> --query value[].properties[].thumbprint
        """
        certificates = self.get_certificates(resource_group, iot_hub)
        thumbprints = [
            cert.properties.thumbprint for cert in certificates.value]
        return thumbprints

    def get_certificate_etag(self, resource_group: str, iot_hub: str, certificate_name: str):
        """
        return eTag of given certificate_name
        cli command:
        az iot hub certificate show --hub-name <az_IoT_hub_name> --name <certificate_name> --query eTag
        """
        certificate = self.iot_hub_client.certificates.get(
            resource_name=iot_hub,
            resource_group_name=resource_group,
            certificate_name=certificate_name,
        )
        return certificate.etag

    def create_certificate(self, resource_group: str, iot_hub: str, certificate_name: str, certificate_description: str):
        """
        Upload the certificate to the IoT hub. Adds new or replaces existing certificate.
        inputs:
            certificate_name: The name of the certificate.
            certificate_description: base-64 representation of the X509 leaf certificate .cer file or just .pem
                file content.
        cli command:
        az iot hub certificate create --hub-name <iot_hub> --name <signer_name> --path <signer_cert>
        """
        cert_content = CertificateBodyDescription(
            certificate=certificate_description)

        certificates = self.iot_hub_client.certificates.create_or_update(
            resource_name=iot_hub,
            resource_group_name=resource_group,
            certificate_name=certificate_name,
            certificate_description=cert_content
        )
        return certificates

    def generate_verification_code(self, resource_group: str, iot_hub: str, certificate_name: str, eTag: str) -> str:
        """
        Generates verification code for proof of possession flow. The verification code will be used to generate a leaf certificate.
        cli command:
        az iot hub certificate generate-verification-code --hub-name <az_IoT_hub_name> --name <signer_name> --eTag <etag_id>
        """
        verification_code = self.iot_hub_client.certificates.generate_verification_code(
            resource_name=iot_hub,
            resource_group_name=resource_group,
            certificate_name=certificate_name,
            if_match=eTag
        )
        return verification_code.properties.verification_code

    def verify_certificate(self, resource_group: str, iot_hub: str, certificate_name: str, verify_cert, eTag: str):
        """
        Generates verification code for proof of possession flow. The verification code will be used to generate a leaf certificate.
        cli command:
        az iot hub certificate verify --hub-name az_IoT_hub_name --name signer_name --path verify_cert --eTag eTag
        """
        verification_body = CertificateVerificationDescription(
            certificate=verify_cert)

        certificate = self.iot_hub_client.certificates.verify(
            resource_name=iot_hub,
            resource_group_name=resource_group,
            certificate_name=certificate_name,
            certificate_verification_body=verification_body,
            if_match=eTag
        )
        return certificate

    def delete_certificate(self, resource_group: str, iot_hub: str, certificate_name: str, eTag: str) -> None:
        """
        Deletes an existing X509 certificate or does nothing if it does not exist.
        cli command:
        az iot hub certificate delete --eTag <eTag> --name <certificate_name> --hub-name <az_IoT_hub_name>
        """
        self.iot_hub_client.certificates.delete(
            resource_name=iot_hub,
            resource_group_name=resource_group,
            certificate_name=certificate_name,
            if_match=eTag
        )


class AzureSDK_RTOS(AzureSDK):
    def __init__(self):
        super().__init__()

    def setup_client(self, subscription_id):
        super().setup_client(subscription_id)
        # create IoT DPS Client
        self.dps_client = IotDpsClient(
            self.credential, self.az_subscription_id)

    def connect_azure(self, resource_group: str, dps_name: str):
        # get DPS connection string
        self.dps_connection_string = self.get_dps_connection_string(resource_group, dps_name)

        # create provisioning service client
        self.provisioning_service_client = ProvisioningServiceClient.create_from_connection_string(
            self.dps_connection_string)

    def get_dps(self, resource_group: str, dps_name: str):
        try:
            response = self.dps_client.iot_dps_resource.get(
                provisioning_service_name=dps_name,
                resource_group_name=resource_group,
            )
            return response
        except BaseException:
            return None

    def create_dps(self, resource_group: str, dps_name: str):
        response = self.dps_client.iot_dps_resource.begin_create_or_update(
            resource_group_name=resource_group,
            provisioning_service_name=dps_name,
            iot_dps_description={
                "location": "East US",
                "properties": {"enableDataResidency": False},
                "sku": {"capacity": 1, "name": "S1"},
                "tags": {},
            }
        ).result()
        return response

    def get_dps_connection_string(self, resource_group: str, dps_name: str):
        dps_instance = self.dps_client.iot_dps_resource.get(
            provisioning_service_name=dps_name, resource_group_name=resource_group)
        dps_resource = self.dps_client.iot_dps_resource.list_keys(
            provisioning_service_name=dps_name, resource_group_name=resource_group)
        key_name = ""
        primary_key = ""
        for dps in dps_resource:
            key_name = dps.key_name
            primary_key = dps.primary_key
            break

        # Extract the connection string from the DPS resource
        dps_connection_string = f"HostName={dps_instance.properties.service_operations_host_name};SharedAccessKeyName={key_name};SharedAccessKey={primary_key}"
        return dps_connection_string

    def get_individual_enrollment(self, device_id: str):
        """
        Retrieve an Individual Enrollment from the Provisioning Service
        CLI commands:
        az iot dps enrollment show --dps-name dname --eid device_id
        """
        try:
            enrollment = self.provisioning_service_client.get_individual_enrollment(
                device_id)
        except BaseException:
            enrollment = None
        return enrollment

    def enroll_device(self, iot_hub: str, device_id: str, cert_content: str) -> IndividualEnrollment:
        """
        Create or update an Individual Enrollment on the Provisioning Service
        CLI commands:
        az iot dps enrollment create -g resourceGroup  --dps-name dname --enrollment-id device_id --attestation-type x509 --certificate-path path
        """
        attestation = AttestationMechanism(
            type="x509",
            x509=X509Attestation(client_certificates=X509Certificates(primary=X509CertificateWithInfo(certificate=cert_content))))
        enrollment = IndividualEnrollment(
            iot_hubs=[iot_hub],
            registration_id=device_id,
            attestation=attestation,
            device_id=device_id
        )
        device = self.provisioning_service_client.create_or_update(enrollment)
        return device
