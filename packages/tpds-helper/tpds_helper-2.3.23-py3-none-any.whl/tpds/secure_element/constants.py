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


class Constants:
    # List all Secure Element constants here
    ATCA_CONFIG_ZONE = 0x00
    ATCA_ZONE_OTP = 0x01
    ATCA_DATA_ZONE = 0x02

    LOCK_ZONE_CONFIG = 0x00
    LOCK_ZONE_DATA = 0x01

    # List all SHA204A constants here
    ATCA_SHA204A_MAC_OPCODE = 0x08
    ATCA_SHA204A_MAC_MODE = 0x00

    # List all ECC608 constants here
    ATCA_ECC608_MAC_OPCODE = 0x08
    ATCA_ECC608_NONCE_OPCODE = 0x16

    # List all SHA206A constants here

    # List all ECC204 constants here
    ATCA_ECC204_ZONE_DATA = 0x00
    ATCA_ECC204_ZONE_CONFIG = 0x01


# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == "__main__":
    pass
