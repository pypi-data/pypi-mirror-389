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
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import boto3
import botocore
import yaml
from cryptography import x509
from cryptography.hazmat.primitives import serialization

import tpds.tp_utils
from tpds.certs import Cert, cert_utils
from tpds.manifest import Manifest, ManifestIterator
from tpds.tp_utils.tp_settings import TPSettings

from .cloud_connect import CloudConnect

_DEFAULT_POLICY = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["iot:Connect"],
            "Resource": ["arn:aws:iot:*:*:client/${iot:Connection.Thing.ThingName}"],
        },
        {
            "Effect": "Allow",
            "Action": ["iot:Publish", "iot:Receive"],
            "Resource": [
                "arn:aws:iot:*:*:topic/${iot:Connection.Thing.ThingName}/*",
                "arn:aws:iot:*:*:topic/$aws/things/${iot:Connection.Thing.ThingName}/shadow/*",
                "arn:aws:iot:*:*:topic/$aws/things/${iot:Connection.Thing.ThingName}/streams/*",
                "arn:aws:iot:*:*:topic/$aws/things/${iot:Connection.Thing.ThingName}/jobs/*",
            ],
        },
        {
            "Effect": "Allow",
            "Action": ["iot:Subscribe"],
            "Resource": [
                "arn:aws:iot:*:*:topicfilter/${iot:Connection.Thing.ThingName}/#",
                "arn:aws:iot:*:*:topicfilter/$aws/things/${iot:Connection.Thing.ThingName}/shadow/*",
                "arn:aws:iot:*:*:topicfilter/$aws/things/${iot:Connection.Thing.ThingName}/streams/*",
                "arn:aws:iot:*:*:topicfilter/$aws/things/${iot:Connection.Thing.ThingName}/jobs/*",
            ],
        },
        {
            "Effect": "Allow",
            "Action": ["iot:UpdateThingShadow", "iot:GetThingShadow"],
            "Resource": [
                "arn:aws:iot:*:*:topic/$aws/things/${iot:Connection.Thing.ThingName}/shadow/*"
            ],
        },
    ],
}


class AWSZTKitError(RuntimeError):
    pass


class AWSConnect(CloudConnect):
    def __init__(self):
        self.default_creds = {
            "title": "AWS IoT Credentials",
            "access_key_id": "",
            "secret_access_key": "",
            "region": "",
        }
        self.creds_file = os.path.join(TPSettings().get_base_folder(), "aws_credentials.yaml")
        if not os.path.exists(self.creds_file):
            Path(self.creds_file).write_text(yaml.dump(self.default_creds, sort_keys=False))

    def set_credentials(self, credentials=None):
        """
        Method aids in logging into aws portal via cli and
        set the credentials in aws cli

        Inputs:
              credentials    contain aws access key ID and
                             secrey access key
        """
        # do aws configure
        if not isinstance(credentials, dict):
            raise ValueError("Unsupported User credentials type")

        # Setting the aws cli for the access key
        print("Setting aws access key...", end="")
        sys_shell = True if sys.platform == "win32" else False
        subProcessOut = tpds.tp_utils.run_subprocess_cmd(
            cmd=["aws", "configure", "set", "aws_access_key_id", credentials.get("access_key_id")],
            sys_shell=sys_shell,
        )
        print(
            "Failed with {}".format(subProcessOut.returncode) if subProcessOut.returncode else "OK"
        )

        print("Setting aws secret access key...", end="")
        subProcessOut = tpds.tp_utils.run_subprocess_cmd(
            cmd=[
                "aws",
                "configure",
                "set",
                "aws_secret_access_key",
                credentials.get("secret_access_key"),
            ],
            sys_shell=sys_shell,
        )
        print(
            "Failed with {}".format(subProcessOut.returncode) if subProcessOut.returncode else "OK"
        )

        print("Setting aws region...", end="")
        subProcessOut = tpds.tp_utils.run_subprocess_cmd(
            cmd=["aws", "configure", "set", "region", credentials.get("region")],
            sys_shell=sys_shell,
        )
        print(
            "Failed with {}".format(subProcessOut.returncode) if subProcessOut.returncode else "OK"
        )

        # initiate session
        self.__get_session("default")
        self.__install_policy("Default", _DEFAULT_POLICY)
        print(
            "Getting aws endpoint...{}".format(
                self.iot.describe_endpoint(endpointType="iot:Data").get("endpointAddress")
            )
        )

    def register_signer(self, signer_cert, signer_key="", verify_cert=""):
        """Method registers signer CA with AWS IoT

        Inputs:
            signer_cert          signer certificate to be registered
            signer_key           signer key which sign the verify cert
            verify_cert          verify certificate to be registered
        """

        if not signer_cert:
            raise ValueError("Signer certificate is required to register")

        signer = Cert()
        signer.set_certificate(signer_cert)
        verify = Cert()
        if not verify_cert:
            if not signer_key:
                raise ValueError("Either signer key or verify cert is req to register")
            else:
                verify_cert = "verify_cert.crt"
                self.get_verification_cert(signer_key, signer_cert, verify_cert)
        verify.set_certificate(verify_cert)

        print("Registering signer CA with AWS IoT...")
        try:
            response = self.iot.register_ca_certificate(
                caCertificate=signer.certificate.public_bytes(
                    encoding=serialization.Encoding.PEM
                ).decode("ascii"),
                verificationCertificate=verify.certificate.public_bytes(
                    encoding=serialization.Encoding.PEM
                ).decode("ascii"),
                setAsActive=True,
                allowAutoRegistration=True,
            )
            print("    Cert ID: " + response.get("certificateId"))
        except botocore.exceptions.ClientError as e:
            e_error = e.response.get("Error")
            if e_error.get("Code") == "ResourceAlreadyExistsException":
                ca_id = re.search("ID:([0-9a-zA-Z]+)", e_error.get("Message")).group(1)
                print("    Its already exists in AWS IoT.")
                print("    Cert ID: " + ca_id)
            else:
                print(e)
                raise

    def register_device_without_ca(self, device_id, device_cert):
        """Method registers device without CA

        Args:
            device_id               unique device ID
            device_cert             device certificate to be registered

        Returns:
            dict: dictionary with certArn, certId, thingArn,
                  registered or not values.
        """
        device = Cert()
        device.set_certificate(device_cert)
        reg_resp = thing_resp = dict()

        print("Registering device with AWS IoT...")
        try:
            # import certificate...
            # Load a certificate into AWS IoT and attach policy to it
            reg_resp = self.iot.register_certificate_without_ca(
                certificatePem=device.get_certificate_in_pem().decode(encoding="UTF-8")
            )
            self.iot.attach_policy(policyName=self.policy, target=reg_resp.get("certificateArn"))
            self.iot.update_certificate(
                certificateId=reg_resp.get("certificateId"), newStatus="ACTIVE"
            )
            print("    Cert ARN: " + reg_resp.get("certificateArn"))
            print("    Cert ID: " + reg_resp.get("certificateId"))

            # make thing...
            # Create an AWS IoT "thing" and attach the certificate
            thing_resp = self.iot.create_thing(thingName=device_id)
            self.iot.attach_thing_principal(
                thingName=device_id, principal=reg_resp.get("certificateArn")
            )
            print("    Thing ARN: " + thing_resp.get("thingArn"))

            is_registered = self.is_device_registered(device_id, device_cert)
            print("OK" if is_registered else "Verification failed")

        except botocore.exceptions.ClientError as e:
            e_error = e.response.get("Error")
            if e_error.get("Code") == "ResourceAlreadyExistsException":
                is_registered = True
                print("    " + e_error.get("Message"))
            else:
                print("     {}".format(e))
                raise

        return {
            "cert_arn": reg_resp.get("certificateArn"),
            "cert_id": reg_resp.get("certificateId"),
            "thing_arn": thing_resp.get("thingArn"),
            "is_registered": is_registered,
        }

    def register_from_manifest(self, device_manifest, device_manifest_ca, key_slot=0):
        """
        Method registers device from given manifest
        Inputs:
              device_manifest     manifest contains certs and public keys
              device_manifest_ca  manifest signer key
              key_slot            slot where device private key present

        Raises:
            ValueError: Occurs when device registration failed.
        """
        if os.path.exists(device_manifest) and device_manifest.endswith(".json"):
            with open(device_manifest) as json_data:
                device_manifest = json.load(json_data)

        if not isinstance(device_manifest, list):
            raise ValueError("Unsupport manifest format to process")

        manifest_ca = Cert()
        manifest_ca.set_certificate(device_manifest_ca)
        iterator = ManifestIterator(device_manifest)
        print("Number of certificates: {}".format(iterator.index))

        while iterator.index != 0:
            se = Manifest().decode_manifest(iterator.__next__(), manifest_ca.certificate)
            se_certs = Manifest().extract_public_data_pem(se)
            slot = next((sub for sub in se_certs if sub.get("id") == str(key_slot)), None)
            no_of_certs = len(slot.get("certs"))
            if no_of_certs:
                self.register_device_without_ca(
                    se.get("uniqueId").upper(), slot.get("certs")[no_of_certs - 2]
                )

    def get_verification_cert(self, signer_key, signer_cert, file=""):
        """
        Method gets the verification code and generate verification cert

        Inputs:
              signer_key      signer key which sign the verification cert
              signer_cert     signer certificate
              file            path where verification cert loaded

            return verification certificate
        """
        ca_key = tpds.tp_utils.TPAsymmetricKey(signer_key)
        ca_cert = Cert()
        ca_cert.set_certificate(signer_cert)

        # Request a registration code required for registering a CA
        # certificate (signer)
        print("Getting CA registration code from AWS IoT...")
        reg_code = self.iot.get_registration_code()["registrationCode"]
        print("    Code: %s" % reg_code)

        # Generate a verification certificate around the registration code
        # (subject common name)
        print("Generating signer CA AWS verification certificate...", end="")
        self.verify_cert = Cert()
        self.verify_cert.builder = x509.CertificateBuilder()
        self.verify_cert.builder = self.verify_cert.builder.serial_number(
            cert_utils.random_cert_sn(16)
        )
        self.verify_cert.builder = self.verify_cert.builder.issuer_name(ca_cert.certificate.subject)
        self.verify_cert.builder = self.verify_cert.builder.not_valid_before(
            datetime.utcnow().replace(tzinfo=timezone.utc)
        )
        self.verify_cert.builder = self.verify_cert.builder.not_valid_after(
            self.verify_cert.builder._not_valid_before + timedelta(days=1)
        )
        self.verify_cert.builder = self.verify_cert.builder.subject_name(
            x509.Name([x509.NameAttribute(x509.oid.NameOID.COMMON_NAME, reg_code)])
        )
        self.verify_cert.builder = self.verify_cert.builder.public_key(
            ca_cert.certificate.public_key()
        )
        self.verify_cert.sign_builder(ca_key.get_private_key())
        print("OK")

        if file:
            Path(file).write_bytes(self.verify_cert.get_certificate_in_pem())

        return self.verify_cert

    def is_device_registered(self, device_id, device_cert):
        """
        Method checks whether device is registered or not
        Inputs:
             device_id      device certificate common name

            return true if device is registered else false
        """
        device = Cert()
        device.set_certificate(device_cert)
        try:
            response = self.iot.list_thing_principals(thingName=device_id)
            response = self.iot.describe_certificate(
                certificateId=response["principals"][0].split("/")[-1]
            )

            if response.get("certificateDescription").get(
                "certificatePem"
            ) != device.get_certificate_in_pem().decode(encoding="UTF-8"):
                raise BaseException("Certificate Mismatch for {}".format(device_id))
        except BaseException as e:
            print("Exception occurred: {}".format(e))
            return False

        return True

    def get_thing_details(self, thingName=""):
        try:
            thing_details = self.iot.describe_thing(thingName=thingName)
            thing_principal = self.iot.list_thing_principals(thingName=thingName)
            cert_description = self.iot.describe_certificate(
                certificateId=thing_principal["principals"][0].split("/")[-1]
            ).get("certificateDescription")
            return {
                "thingArn": thing_details.get("thingArn"),
                "thingID": thing_details.get("thingId"),
                "certificateArn": cert_description.get("certificateArn"),
                "certificateId": cert_description.get("certificateId"),
                "certificatePem": cert_description.get("certificatePem"),
            }
        except Exception as e:
            print(e)

    def get_signer_cert_description(self, signer_cert):
        try:
            ca_cert = Cert()
            ca_cert.set_certificate(signer_cert)
            ca_list = self.iot.list_ca_certificates()
            print("Number of CAs listed {}".format(len(ca_list.get("certificates"))))
            for ca in ca_list.get("certificates"):
                cert_description = self.iot.describe_ca_certificate(
                    certificateId=ca.get("certificateId")
                ).get("certificateDescription")
                if cert_description is not None and cert_description.get(
                    "certificatePem"
                ) == ca_cert.get_certificate_in_pem().decode(encoding="UTF-8"):
                    return {
                        "certificateArn": cert_description.get("certificateArn"),
                        "certificateId": cert_description.get("certificateId"),
                        "certificatePem": cert_description.get("certificatePem"),
                    }
        except Exception as e:
            print(e)

    def execute_aws_gui(self, thing_id, qtUiFile):
        # app = QtWidgets.QApplication.instance()
        # if app is None:
        #     app = QtWidgets.QApplication(sys.argv)
        # AWS_GUI(aws_iot_data=self.aws_session.client('iot-data'),
        #         thing_name=thing_id,
        #         qtUiFile=qtUiFile)
        # app.exec_()
        pass

    def __get_session(self, aws_profile):
        """Create an AWS session with the credentials from the specified profile"""
        try:
            self.aws_session = boto3.session.Session(profile_name=aws_profile)
            self.iot = self.aws_session.client("iot")
        except botocore.exceptions.ProfileNotFound as e:
            print(e)
            raise AWSZTKitError(
                'AWS profile not found. Please make sure you have the AWS CLI \
                installed and run "aws configure --profile %s" \
                to setup profile.'
                % aws_profile
            )

    def __install_policy(self, policy_name, policy_document):
        try:
            self.iot.get_policy(policyName=policy_name)
        except botocore.exceptions.ClientError as e:
            if "ResourceNotFoundException" == e.response.get("Error").get("Code"):
                self.iot.create_policy(
                    policyName=policy_name, policyDocument=json.dumps(policy_document)
                )
                print("Created policy {}".format(policy_name))
            else:
                print("Exception occurred: {}".format(e))
                raise

        self.policy = policy_name


__all__ = ["AWSZTKitError", "AWSConnect"]

# class AWS_GUI(QtWidgets.QMainWindow):
#     def __init__(self, aws_iot_data, thing_name, qtUiFile):
#         super(AWS_GUI, self).__init__(parent=None)
#         self.aws_iot_data = aws_iot_data
#         self.thing_name = thing_name
#         self.qtUiFile = qtUiFile
#         self.state = ''
#         self.load_UI()
#         self.rBtnOn.toggled.connect(self.led_click)
#         self.lineEdit.setText(thing_name)
#         self.on_update()

#     def load_UI(self):
#         # Load the .ui file
#         self.mywidget = QUiLoader().load(self.qtUiFile)
#         # Set window icon
#         icon = os.path.join(os.getcwd(), 'assets', 'shield.ico')
#         self.mywidget.setWindowIcon(QtGui.QIcon(icon))
#         # display ui window
#         self.mywidget.show()

#     def led_click(self, led_index):
#         if self.rBtnOn.isChecked():
#             led_value = 'on'
#         else:
#             led_value = 'off'

#         msg = {'state': {'desired': {('led1'): led_value}}}
#         # print('update_thing_shadow(): %s\n' % json.dumps(msg))
#         self.aws_iot_data.update_thing_shadow(thingName=self.thing_name,
#                                               payload=json.dumps(msg))

#     def on_update(self):
#         try:
#             response = self.aws_iot_data.get_thing_shadow(
#                                                 thingName=self.thing_name)

#             self.shadow = json.loads(
#                         response.get('payload').read().decode('ascii'))
#             curr_state = self.shadow.get('state')

#             if curr_state != self.state:
#                 self.state = curr_state
#                 self.lineEdit.setText(self.thing_name)

#                 print(
#                     'get_thing_shadow(): state changed\n%s\n' % json.dumps(
#                                                 self.shadow, sort_keys=True))

#                 if 'desired' in curr_state:
#                     led_label = 'led1'
#                     if led_label in curr_state.get('desired'):
#                         if curr_state.get('desired').get(led_label) == 'on':
#                             self.rBtnOn.setChecked(True)
#                         else:
#                             self.rBtnOn.setChecked(False)

#         except botocore.exceptions.ClientError as e:
#             if 'ResourceNotFoundException' == e.response.get('Error').get(
#                                                 'Code'):
#                 if self.state != 'no thing shadow':
#                     self.state = 'no thing shadow'
#                     status_msg = e.response.get('Error').get('Message') + '. \
#                         device may not have successfully connected to AWS yet.'
#                     self.lineEdit.setText(status_msg)
#                     print(status_msg)
#             else:
#                 raise

#         QtCore.QTimer.singleShot(2000, self.on_update)


# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == "__main__":
    pass
