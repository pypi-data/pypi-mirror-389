# -*- coding: utf-8 -*-
# 2018to present - Copyright Microchip Technology Inc. and its subsidiaries.

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

import yaml
from google.api_core.exceptions import AlreadyExists
from google.cloud import iot_v1

from tpds.certs import Cert
from tpds.manifest import Manifest, ManifestIterator
from tpds.tp_utils.tp_settings import TPSettings

from .cloud_connect import CloudConnect


class GCPConnect(CloudConnect):
    def __init__(self):
        self.project_id = ""
        self.registry_id = ""
        self.region = ""
        self.default_creds = {"title": "GCP IoT Credentials", "registry_id": "", "region": ""}
        self.creds_file = os.path.join(TPSettings().get_base_folder(), "gcp_credentials.yaml")
        if not os.path.exists(self.creds_file):
            Path(self.creds_file).write_text(yaml.dump(self.default_creds, sort_keys=False))

    def set_credentials(self, iot_manifest=None, data_view=None, credentials=None):
        """
        Method logins into gcp portal via cli and
        set the credentials in azure cli

        Inputs:
              credentials    contain Registry ID and Region
        """
        # Set the project id
        if (
            isinstance(iot_manifest, str)
            and os.path.exists(iot_manifest)
            and iot_manifest.endswith(".json")
        ):
            with open(iot_manifest) as f:
                self.project_id = json.load(f).get("project_id")
        else:
            raise ValueError("Check GCP iot-manifest file information")

        # set the environment variable
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = iot_manifest

        if isinstance(data_view, str) and os.path.exists(data_view) and data_view.endswith(".json"):
            self.data_view = data_view
        else:
            raise ValueError("Check GCP data_view file information")

        # set the registry id and region
        if not isinstance(credentials, dict):
            raise ValueError("Unsupported User credentials type")

        self.registry_id = credentials.get("registry_id")
        self.region = credentials.get("region")

    def register_device(self, secure_element_manifest):
        """Method registers device with GCP"""
        if not secure_element_manifest:
            raise ValueError("Unsupported manifest format to process!")
        try:
            client = iot_v1.DeviceManagerClient()
            parent = client.registry_path(self.project_id, self.region, self.registry_id)

            for device in secure_element_manifest:
                print("Registering device with id {}...".format(device.get("id")), end="")
                client.create_device(parent=parent, device=device)
                print("OK")

        except AlreadyExists:
            print("Device is registered already!!!")
            pass

        except Exception as e:
            print("     {}".format(e))
            raise

    def register_from_manifest(self, device_manifest, device_manifest_ca, key_slot=0):
        """
        Method register device from given manifest
        Inputs:
              device_manifest     manifest contains certs and public keys
              device_manifest_ca  manifest signer key
              key_slot            slot where device private key present

            return true if device registered successfully else false
        """
        if device_manifest is None:
            raise ValueError("Unsupported manifest format to process")
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

            pubkey_format = dict()
            if slot.get("certs"):
                no_of_certs = len(slot.get("certs"))
                pubkey_format.update({"format": "ES256_X509_PEM"})
                pubkey_format.update({"key": slot.get("certs")[no_of_certs - 2]})
            elif slot.get("pub_key"):
                pubkey_format.update({"format": "ES256_PEM"})
                pubkey_format.update({"key": slot.get("pub_key")})
            else:
                raise ValueError("Unknown manifest secure element object!")

            # GCP manifest format which will be uploaded later
            manifest_format = {"id": "", "credentials": [{"public_key": dict()}]}
            se_manifest = []
            manifest_format.update({"id": f"""d{se.get('uniqueId').upper()}"""})
            manifest_format["credentials"][0]["public_key"] = pubkey_format
            se_manifest.append(manifest_format)
            self.register_device(se_manifest)

    def execute_gcp_gui(self, qtUiFile):
        # os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.data_view
        # with open(self.data_view) as f:
        #     self.project_id = json.load(f).get('project_id')

        # app = QtWidgets.QApplication.instance()
        # if app is None:
        #     app = QtWidgets.QApplication(sys.argv)
        # GCP_GUI(self.project_id, 'data-view', qtUiFile)
        # app.exec_()
        pass


__all__ = ["GCPConnect"]

# class GCP_GUI(QtWidgets.QMainWindow):
#     """Basic Message Visualizer gui"""
#     def __init__(self, project_id, subscription_id, qtUiFile):
#         super(GCP_GUI, self).__init__(parent=None)
#         self.qtUiFile = qtUiFile
#         self.load_UI()

#         self.subscriber = pubsub_v1.SubscriberClient()
#         self.subscription_path = self.subscriber.subscription_path(
#                                             project_id, subscription_id)
#         self.subscriber.subscribe(self.subscription_path,
#                                   callback=self.subscription_callback)

#     def load_UI(self):
#         # load ui file
#         self.mywidget = QUiLoader().load(self.qtUiFile)

#         # add icon
#         icon = os.path.join(os.getcwd(), 'assets', 'shield.ico')
#         self.mywidget.setWindowIcon(QtGui.QIcon(icon))

#         # display ui window
#         self.mywidget.show()

#         # Setup treeview
#         self.treeView.setRootIsDecorated(False)
#         self.treeView.setAlternatingRowColors(True)

#         self.model = QtGui.QStandardItemModel()
#         self.model.setHorizontalHeaderLabels(['Date/Time',
#                                               'Serial Number',
#                                               'Led Status'])
#         self.treeView.setModel(self.model)

#     def add_data(self, date_time, sno, led_status):
#         self.model.insertRow(0)
#         self.model.setData(self.model.index(0, 0), date_time)
#         self.model.setData(self.model.index(0, 1), sno)
#         self.model.setData(self.model.index(0, 2), led_status)

#     def subscription_callback(self, message):
#         """Receive messages from the subscription"""
#         data = json.loads(message.data)

#         self.LE_project.setText(message.attributes['projectId'])
#         self.LE_registry.setText(message.attributes['deviceRegistryId'])
#         self.LE_region.setText(message.attributes['deviceRegistryLocation'])

#         sample_values = [message.attributes['deviceId']] + \
#                         ['{}: {}'.format(k, v) for k, v in data.items() if k != 'timestamp']
#         sample_time = datetime.datetime.fromtimestamp(data['timestamp'])
#         serialno, led_status = sample_values

#         self.add_data(sample_time.strftime("%H:%M:%S"), serialno, led_status)

#         message.ack()


# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == "__main__":
    pass
