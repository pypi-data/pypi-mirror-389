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

from .tp_client import Client


class TPInputDialog:
    def __init__(self, cb_msg_trigger, cb_msg_response):
        self.cb_msg_trigger = cb_msg_trigger
        self.cb_msg_received = cb_msg_response

    def invoke_dialog(self):
        self.client_c = Client(None)
        self.cb_msg_trigger()
        resp_msg = self.client_c.client.recv()
        self.client_c.client.close()
        self.cb_msg_received(json.loads(resp_msg).get("response"))


class TPInputFileUpload(TPInputDialog):
    def __init__(self, file_filter=None, dialog_title="UserInput", nav_dir=None):
        self.filter = file_filter
        self.dialog_title = dialog_title
        self.file_selection = None
        self.nav_dir = nav_dir
        super().__init__(self.file_upload, self.process_response)

    def file_upload(self):
        self.client_c.send_message("file_upload", [self.dialog_title, self.filter, self.nav_dir])

    def process_response(self, message):
        self.file_selection = message


class TPInputTextBox(TPInputDialog):
    def __init__(self, desc="Enter Here", dialog_title="UserInput"):
        self.desc = desc
        self.dialog_title = dialog_title
        self.user_text = None
        super().__init__(self.text_box, self.process_response)

    def text_box(self):
        self.client_c.send_message("text_box", [self.dialog_title, self.desc])

    def process_response(self, message):
        self.user_text = message


class TPInputDropdown(TPInputDialog):
    def __init__(self, item_list, desc="Select your option", dialog_title="UserInput"):
        self.item_list = item_list
        self.desc = desc
        self.dialog_title = dialog_title
        self.user_option = None
        super().__init__(self.dropdown, self.process_response)

    def dropdown(self):
        self.client_c.send_message("dropdown", [self.dialog_title, self.item_list, self.desc])

    def process_response(self, message):
        self.user_option = message


class TPMessageBox(TPInputDialog):
    def __init__(self, title="Select your option", info="UserInput", option_list=["OK", "Cancel"]):
        self.title = title
        self.info = info
        self.option_list = option_list
        self.user_select = None
        super().__init__(self.messagebox, self.process_response)

    def messagebox(self):
        self.client_c.send_message("messagebox", [self.title, self.info])

    def process_response(self, message):
        self.user_select = message


# class TPOpenLink(TPInputDialog):
#     def __init__(
#             self, link):
#         self.link = link
#         super().__init__(self.open_link, self.process_response)

#     def open_link(self):
#         self.client_c.send_message(
#                             'open_link', [self.link])

#     def process_response(self, message):
#         pass


class OpenExplorerFolder(TPInputDialog):
    def __init__(self, path=""):
        self.path = path
        super().__init__(self.openexplorer, self.process_response)

    def openexplorer(self):
        self.client_c.send_message("open_explorer", [self.path])

    def process_response(self, message):
        pass


__all__ = [
    "TPInputDialog",
    "TPInputFileUpload",
    "TPInputTextBox",
    "TPInputDropdown",
    "TPMessageBox",
    "OpenExplorerFolder",
]

# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == "__main__":
    pass
