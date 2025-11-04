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

import cryptoauthlib as cal

from tpds.secure_element.constants import Constants
from tpds.tp_utils import TPAsymmetricKey, TPSymmetricKey


class ResourceGeneration:
    def __init__(self):
        pass

    def generate_private_key(self, slot, public_key=None):
        """
        Method perform generate private key on device and get public key
        return ATCA_SUCCESS on success or error code
        Inputs:
              slot                slot number
        Outputs:
              public_key_file     public key of corresponding slot will be
                                  returned here
              status              status of generate private key returned
                                  here

              Method create a .pem and .h file which contains public key
              e.g., slot_x_public_key.pem and slot_x_public_key.h
        """
        slot_public_key = bytearray(64)
        status = cal.atcab_genkey(slot, slot_public_key)
        if status == cal.Status.ATCA_SUCCESS:
            public_key_title = "slot_{}_ecc_public_key".format(slot)
            asym_key = TPAsymmetricKey()
            asym_key.set_public_key(slot_public_key)
            asym_key.get_public_c_hex(
                file="{}.h".format(public_key_title), variable_name=public_key_title
            )
            asym_key.get_public_pem("{}.pem".format(public_key_title))

            if isinstance(public_key, bytearray):
                public_key[0:] = slot_public_key
            elif public_key:
                asym_key.get_public_pem(public_key)

        return status

    def load_public_key(self, slot, public_key=None):
        """
        Method load a public key into given slot
        return ATCA_SUCCESS on success or error code
        Inputs:
             slot                   slot number where public key
                                    will be loaded
             public_key             either .pem or bytearray
                                    which contains public key in it
        Outputs:
              status                load public key status returned here

              Method create a .pem and .h file which contains public key
              e.g., slot_x_public_key.pem and slot_x_public_key.h
        """
        public_key_control_bytes = bytearray(4)
        status = cal.atcab_read_zone(
            Constants.ATCA_DATA_ZONE,
            slot,
            0,
            0,
            public_key_control_bytes,
            len(public_key_control_bytes),
        )

        if public_key_control_bytes[0] & 0x50:
            print("Slot requires invalidation prior to write.")
            return status
        else:
            asym_key = TPAsymmetricKey()
            if public_key:
                asym_key.set_public_key(public_key)
            else:
                privkey_file = "slot_{}_ecc_private_key".format(slot) + ".pem"
                asym_key.get_private_pem(privkey_file)

            status = cal.atcab_write_pubkey(slot, asym_key.public_key_bytes)
            if status == cal.Status.ATCA_SUCCESS:
                public_key_title = "slot_{}_ecc_public_key".format(slot)
                asym_key.get_public_c_hex(
                    file="{}.h".format(public_key_title), variable_name=public_key_title
                )
                asym_key.get_public_pem("{}.pem".format(public_key_title))
            return status

    def load_secret_key(self, slot, secret_key=None, encryption_slot=None, encryption_key=None):
        """
        Method load a secret key into device and return it status
        Inputs:
              slot          slot number (secret key slot)
              secret_key    either .pem file or bytearray
                            which contains secret key in it
              encrypt_slot  slot number (encryption key slot)
              encrypt_key   either .pem file or bytearray
                            which contains encryption key in it
        Outputs:
              status        write secret key status returned here

                Method creates .pem and .h file which contains secret key
                e.g., slot_x_secret_key.pem and slot_x_secret_key.h
        """
        sym_key = TPSymmetricKey(key=secret_key)

        if encryption_slot and encryption_key:
            sym_encryption_key = TPSymmetricKey(key=encryption_key)

            status = cal.atcab_write_enc(
                slot, 0, sym_key.key_bytes, sym_encryption_key.key_bytes, encryption_slot
            )
        else:
            status = cal.atcab_write_bytes_zone(
                Constants.ATCA_DATA_ZONE, slot, 0, sym_key.key_bytes, len(sym_key.key_bytes)
            )

        if status == cal.Status.ATCA_SUCCESS:
            slot_key_title = "slot_{}_secret_key".format(slot)
            sym_key.get_c_hex(file="{}.h".format(slot_key_title), variable_name=slot_key_title)
            sym_key.get_pem("{}.pem".format(slot_key_title))

        return status


# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == "__main__":
    pass
