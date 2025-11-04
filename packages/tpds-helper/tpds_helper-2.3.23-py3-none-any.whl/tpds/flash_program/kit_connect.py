# -*- coding: utf-8 -*-
# 2022 to present - Copyright Microchip Technology Inc. and its subsidiaries.

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

import platform
import re
import hid
import libusb_package
import serial
import usb.backend.libusb1
import usb.core
import usb.util
from pykitinfo import pykitinfo
from tpds.helper import log


class KitConnect:
    def __init__(self, board_info):
        self.board_info = board_info
        if self.board_info.connection.interfaceType == "hid":
            self.kit_iface = KitConnectHid(board_info)
        else:
            self.kit_iface = KitConnectUART(board_info)

    def is_board_connected(self):
        for kit in pykitinfo.detect_all_kits():
            if self.board_info.mcu_part_number == kit.get("debugger").get(
                "device"
            ) or self.board_info.kit_name == kit.get("debugger", {}).get("kitname", ""):
                return True
        return False

    def get_kit_connected_COM(self):
        com_port = None
        if self.board_info.product_string == "Explorer 16/32 PICkit on Board":
            com_port = self._get_MCP2221_port()
        else:
            kits = pykitinfo.detect_all_kits()
            for kit in kits:
                if self.board_info.kit_name == kit.get("debugger", {}).get("kitname", ""):
                    port = kit.get("debugger", {}).get("serial_port", None)
                    if port and platform.system() == "Windows":
                        com_port = int(port[3:])
                    else:
                        com_port = port
        return com_port

    def get_board_details(self):
        board_details = None
        for kit in pykitinfo.detect_all_kits():
            if self.board_info.mcu_part_number == kit.get("debugger").get(
                "device"
            ) or self.board_info.kit_name == kit.get("debugger", {}).get("kitname", ""):
                board_details = kit
        return board_details

    def set_board_info(self, board_info):
        self.board_info = board_info

    def _get_MCP2221_port(self):
        usbports = [p for p in serial.tools.list_ports.comports() if "04D8:00DD" in p.hwid]
        for port in usbports:
            return int(port.device[3:])
        return None


class KitConnectHid(KitConnect):
    def __init__(self, board_info):
        self.set_board_info(board_info)

    def is_factory_programmed(self):
        for dev in hid.enumerate(
            vendor_id=self.board_info.connection.vid, product_id=self.board_info.kit_parser_pid
        ):
            if dev["product_string"] == self.board_info.product_string:
                return True
        return False

    def get_kit_version(self):
        msg = "b:f()\n"
        if platform.system() == "Windows":
            msg = f"{msg:64}"
        try:
            response = self.__send_query_to_board(msg)
            version = re.findall("\\((.*?)\\)", response)[0]
            kit_version = ".".join(a + b for a, b in zip(version[::2], version[1::2]))
        except BaseException as e:
            log(f"Version fetch has failed with error: {e}")
            kit_version = "0.0.0"
        return kit_version

    def __send_query_to_board(self, query):
        libusb1_backend = usb.backend.libusb1.get_backend(find_library=libusb_package.find_library)
        dev = usb.core.find(
            idVendor=self.board_info.connection.vid,
            idProduct=self.board_info.kit_parser_pid,
            product=self.board_info.product_string,
            backend=libusb1_backend,
        )
        assert dev, (
            f"{self.board_info.description} with PID: "
            f"0x{self.board_info.kit_parser_pid:04X} is not connected. "
            "Connect board and try again."
        )

        assert dev.write(1, query, 100) == (
            len(query) + 1
        ), "USB Write is failed... Reset board and retry again"
        response = "".join([chr(x) for x in dev.read(0x81, len(query), 100)])
        log(f"Response from the board: {response}")
        return response


class KitConnectUART(KitConnect):
    def __init__(self, board_info):
        self.set_board_info(board_info)
        self.com_port = self.get_kit_connected_COM()
        log(f"Kit Uart COM port: {self.com_port}")
        assert self.com_port, "COM port is not detected... Check the connections and try again."

    def is_factory_programmed(self):
        is_programmed = False
        try:
            is_programmed = self.__send_query_to_board(b"b:f()\n") is not None
        except BaseException as e:
            log(f"{e}")
        return is_programmed

    def get_kit_version(self):
        try:
            response = self.__send_query_to_board(b"b:f()\n")
            version = re.findall("\\((.*?)\\)", response)[0]
            kit_version = ".".join(a + b for a, b in zip(version[::2], version[1::2]))
        except BaseException as e:
            log(f"Version fetch has failed with error: {e}")
            kit_version = "0.0.0"
        return kit_version

    def __send_query_to_board(self, query):
        response = None
        with serial.Serial(f"COM{self.com_port}", self.board_info.connection.baud, timeout=5) as ser:
            ser.write(query)
            response = ser.readline().decode()
            log(f"Response from the board: {response}")
        return response


# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == "__main__":
    pass

__all__ = ["KitConnect"]
