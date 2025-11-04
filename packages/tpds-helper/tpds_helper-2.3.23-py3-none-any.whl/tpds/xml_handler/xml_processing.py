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

from __future__ import annotations

from typing import Any

from tpds.xml_handler.tflxtls_xml_updates import TFLXTLSXMLUpdates
from tpds.xml_handler.tflxwpc_xml_updates import TFLXWPCXMLUpdates


class XMLProcessingRegistry:
    __shared_state: dict[str, Any] = {}

    def __new__(cls, **kwargs: str) -> Any:
        # Only ever allow one global instance of the usecase collector
        instance = super().__new__(cls)
        instance.__dict__ = cls.__shared_state
        return instance

    def __init__(self) -> None:
        if "_registry" not in self.__dict__.keys():
            self._registry = {
                "ECC608B_TFLXTLS.xml": TFLXTLSXMLUpdates("ECC608B_TFLXTLS.xml"),
                "PIC32CMLS60_ECC608.xml": TFLXTLSXMLUpdates("PIC32CMLS60_ECC608.xml"),
                "ECC608A-MAH-TFLXWPC.xml": TFLXWPCXMLUpdates("ECC608A-MAH-TFLXWPC.xml"),
            }

    def add_handler(self, name: str, handler: Any) -> None:
        self._registry[name] = handler

    def get_handler(self, name: str, default: Any = None) -> Any:
        return self._registry.get(name, default)


class XMLProcessing:
    def __new__(cls, base_xml="ECC608B_TFLXTLS.xml"):
        if base_xml is None:
            base_xml = "ECC608B_TFLXTLS.xml"
        return XMLProcessingRegistry().get_handler(base_xml, cls)


__all__ = ["XMLProcessing", "XMLProcessingRegistry"]
