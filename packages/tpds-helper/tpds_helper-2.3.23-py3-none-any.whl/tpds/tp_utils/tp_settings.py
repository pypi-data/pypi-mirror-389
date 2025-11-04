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
import os
import platform

from tpds.settings import TrustPlatformSettings


class TPSettings:
    def __init__(self):
        self.__tp_settings = TrustPlatformSettings(log_enable=False)

    def get_mplab_paths(self):
        mplab_paths = {}
        if self.__tp_settings.settings.mplab_path is not None and os.path.exists(
            self.__tp_settings.settings.mplab_path
        ):
            mplab_path = self.__tp_settings.settings.mplab_path
            mplab_paths.update({"mplab_path": mplab_path})
            jar_dir_path = os.path.join(mplab_path, "mplab_platform", "mplab_ipe")
            java_dir_path = os.path.join(mplab_path, "sys")
            if platform.system().lower() == "darwin":
                jar_loc = self.__get_file_path("ipecmd.sh", jar_dir_path)
                java_loc = self.__get_file_path("java", java_dir_path)
                ide_path = self.__get_file_path(
                    "mplab_ide", os.path.join(mplab_path, "mplab_platform", "bin")
                )
            elif platform.system().lower() == "linux":
                jar_loc = self.__get_file_path("ipecmd.jar", jar_dir_path)
                java_loc = self.__get_file_path("java", java_dir_path)
                ide_path = self.__get_file_path(
                    "mplab_ide", os.path.join(mplab_path, "mplab_platform", "bin")
                )
            else:
                jar_loc = self.__get_file_path("ipecmd.jar", jar_dir_path)
                java_loc = self.__get_file_path("java.exe", java_dir_path)
                ide_path = self.__get_file_path(
                    "mplab_ide64.exe", os.path.join(mplab_path, "mplab_platform", "bin")
                )
            mplab_paths.update({"jar_loc": jar_loc})
            mplab_paths.update({"java_loc": java_loc})
            mplab_paths.update({"ide_path": ide_path})

        return mplab_paths

    def get_tpds_core_path(self):
        return self.__tp_settings.settings.local_path

    def get_active_board(self):
        return self.__tp_settings.runtime_settings.active_board.lower()

    def get_base_folder(self):
        return self.__tp_settings.settings.home_path

    def __get_file_path(self, file_name, dir_path):
        file_loc = None
        for root, dirs, files in os.walk(dir_path):
            if file_name in files:
                if os.path.exists(os.path.join(root, file_name)):
                    file_loc = os.path.join(root, file_name)

        # if file_loc is None:
        #     raise FileNotFoundError("{} is not found".format(file_name))

        return file_loc


# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == "__main__":
    pass
