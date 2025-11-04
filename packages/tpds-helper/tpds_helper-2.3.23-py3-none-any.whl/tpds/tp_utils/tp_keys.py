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

import base64
import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from pyasn1_modules import pem

from .tp_utils import get_c_hex_bytes


class TPSymmetricKey:
    """This class creates a Symmetric Key and
    writes into a .pem file or bytearray.
    """

    def __init__(self, key=None, key_length=32):
        """Constructs required attributes

        Args:
            key (.pem file, optional): .pem file which contains secret key and
                                        to store the symmetric key generated.
            key_length (int, optional): The length of the symmetric Key.
                                        Defaults to 32.
        """
        self.set_key(key, key_length)

    def set_key(self, key=None, key_length=32):
        """Method checks the type of key, whether bytes or a file and sets the key.

        Args:
            key ([type], optional): [description]. Defaults to None.
            key_length (int, optional): . Defaults to 32.

        Raises:
            ValueError: Value error is raised,
            when the format in the file is not correct or not as expected.
        """
        if isinstance(key, (bytearray, bytes)):
            self.key_bytes = key
        else:
            if key and os.path.exists(key):
                with open(key, "r") as f:
                    file_content = f.read()

                if "BEGIN SYMMETRIC KEY" in file_content:
                    key_pem = pem.readPemFromFile(
                        open(key),
                        startMarker="-----BEGIN SYMMETRIC KEY-----",
                        endMarker="-----END SYMMETRIC KEY-----",
                    )
                    self.key_bytes = b""
                    self.key_bytes += key_pem[17 : ((key_pem[14] - 2) + 17)]
                else:
                    raise ValueError("found unknown format in {}".format(key))
            else:
                self.key_bytes = os.urandom(key_length)

    def get_c_hex(self, file="", variable_name=""):
        """Converts the input to hex bytes, writes to the file
        and returns the hex bytes variable.
        """
        c_hex_bytes = get_c_hex_bytes(self.key_bytes)

        if file:
            with open(file, "w") as f:
                var_name = "user_secret_key" if variable_name == "" else variable_name
                f.write(f"#ifndef _{var_name.upper()}_H\n")
                f.write(f"#define _{var_name.upper()}\n\n")
                f.write('#include "cryptoauthlib.h"\n\n')
                f.write("#ifdef __cplusplus\n")
                f.write('extern "C" {\n')
                f.write("#endif\n\n")
                f.write(f"uint8_t {var_name}[] = \n")
                f.write("{\n" + f"{c_hex_bytes}" + "};\n\n")
                f.write("#ifdef __cplusplus\n")
                f.write("}\n")
                f.write("#endif\n")
                f.write("#endif\n")

        return c_hex_bytes

    def get_pem(self, file=""):
        """Writes the symmetric key to the .pem file or into the bytearray.

        Args:
            file (str, optional): .pem file. Defaults to ''.

        Returns:
            bytearray: After inserting symmetric key.
        """
        sym_key_der = bytearray.fromhex("304F300906072A8648CE4C030103")
        sym_key_der += bytearray([(len(self.key_bytes) + 2), 0x00, 0x04])
        sym_key_der += self.key_bytes
        sym_key_der[1] = len(sym_key_der) - 2

        sym_key_b64 = base64.b64encode(sym_key_der).decode("ascii")
        sym_key_pem = (
            "-----BEGIN SYMMETRIC KEY-----\n"
            + "\n".join(sym_key_b64[i : i + 64] for i in range(0, len(sym_key_b64), 64))
            + "\n"
            + "-----END SYMMETRIC KEY-----"
        )

        if file:
            with open(file, "w") as f:
                f.write(sym_key_pem)

        return sym_key_pem

    def get_bytes(self):
        return self.key_bytes


class TPAsymmetricKey:
    """Class generates an Asymmetric Key with Private and Public Key pair."""

    def __init__(self, key="", **key_info):
        self.key_info = key_info
        self.set_private_key(key)

    def set_private_key(self, key="", password=None):
        """Method generates the private key.

        Args:
            key (str, optional): bytearray or .pem file. Defaults to ''.

        Raises:
            ValueError: ValueError is raised when expected format is
            not available.
        """
        if isinstance(key, ec.EllipticCurvePrivateKey) or isinstance(key, rsa.RSAPrivateKey):
            self.private_key = key

        elif key and os.path.exists(key):
            with open(key, "r") as f:
                file_content = f.read()

            if any(key in file_content for key in
                   ("BEGIN PRIVATE KEY", "BEGIN EC PRIVATE KEY", "BEGIN RSA PRIVATE KEY")):
                self.private_key = serialization.load_pem_private_key(
                    data=file_content.encode(), password=password, backend=default_backend()
                )
            else:
                raise ValueError("found unknown format in {}".format(key))
        else:
            # Generates key pair based on the algorithm argument
            if self.key_info.get("algo") == "RSA":
                if (
                    self.key_info.get("size") == 1024
                    or self.key_info.get("size") == 2048
                    or self.key_info.get("size") == 3072
                    or self.key_info.get("size") == 4096
                ):
                    self.private_key = rsa.generate_private_key(
                        public_exponent=65537, key_size=self.key_info.get("size")
                    )
                else:
                    raise ("Invalid RSA key size")

            elif self.key_info.get("algo") == "ECC":
                if self.key_info.get("size") == "secp256r1":
                    self.private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
                elif self.key_info.get("size") == "secp224r1":
                    self.private_key = ec.generate_private_key(ec.SECP224R1(), default_backend())
                elif self.key_info.get("size") == "secp384r1":
                    self.private_key = ec.generate_private_key(ec.SECP384R1(), default_backend())
                elif self.key_info.get("size") == "secp521r1":
                    self.private_key = ec.generate_private_key(ec.SECP521R1(), default_backend())
                elif self.key_info.get("size") == "secp256k1":
                    self.private_key = ec.generate_private_key(ec.SECP256K1(), default_backend())
                else:
                    raise ("Invalid ECC Curve type")

            else:
                """Generate default keypair ECC-SECP256R1"""
                self.private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())

        # Update key_info according to the key generated/loaded
        if isinstance(self.private_key, ec.EllipticCurvePrivateKey):
            self.key_info["algo"] = "ECC"
            self.key_info["size"] = self.private_key.curve.name
        elif isinstance(self.private_key, rsa.RSAPrivateKey):
            self.key_info["algo"] = "RSA"
            self.key_info["size"] = self.private_key.key_size

        if self.key_info.get("algo") == "RSA":
            public_key = self.private_key.public_key().public_numbers()
            self.public_key_bytes = bytearray(
                public_key.n.to_bytes(int(self.key_info.get("size") / 8), "big")
            )
        else:
            self.public_key_bytes = self.private_key.public_key().public_bytes(
                serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
            )[1:]

    def set_public_key(self, key=""):
        """Method generates the public key.

        Args:
            key (str, optional): bytearray or .pem file. Defaults to ''.

        Raises:
            ValueError: ValueError is raised when expected format is not
            available.
        """
        if isinstance(key, (bytearray, bytes)):
            self.public_key_bytes = key
            self.private_key = None
        elif isinstance(key, ec.EllipticCurvePublicKey):
            self.public_key_bytes = key.public_bytes(
                serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
            )[1:]
        elif key and os.path.exists(key):
            with open(key, "r") as f:
                file_content = f.read()

            if "BEGIN PUBLIC KEY" in file_content:
                self.private_key = None
                with open(key, "rb") as f:
                    public_key = serialization.load_pem_public_key(
                        data=f.read(), backend=default_backend()
                    )
                    self.public_key_bytes = public_key.public_bytes(
                        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
                    )[1:]
            else:
                raise ValueError("found unknown format in {}".format(key))
        else:
            raise ValueError("key is not found in {}".format(key))

    def get_private_key(self):
        return self.private_key

    def get_private_pem(self, file=""):
        if self.private_key is None:
            raise ValueError("Private key is not available")

        private_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        if file:
            with open(file, "wb") as f:
                f.write(private_pem)

        return str(private_pem, "utf-8")

    def get_public_c_hex(self, file="", variable_name=""):
        c_hex_bytes = get_c_hex_bytes(self.public_key_bytes)

        if file:
            with open(file, "w") as f:
                var_name = "user_public_key" if variable_name == "" else variable_name
                variable_declaration = "uint8_t " + str(var_name) + "[] = {\n"
                f.write(variable_declaration)
                f.write(c_hex_bytes)
                f.write("};")

        return c_hex_bytes

    def get_public_pem(self, file=""):
        public_key_der = bytearray.fromhex("3059301306072A8648CE3D020106082A8648CE3D03010703420004")
        public_key_der += self.public_key_bytes
        public_key_b64 = base64.b64encode(public_key_der).decode("ascii")
        public_key_pem = (
            "-----BEGIN PUBLIC KEY-----\n"
            + "\n".join(public_key_b64[i : i + 64] for i in range(0, len(public_key_b64), 64))
            + "\n"
            + "-----END PUBLIC KEY-----"
        )

        if file:
            with open(file, "w") as f:
                f.write(public_key_pem)

        return public_key_pem

    def get_public_key(self):
        if self.private_key:
            public_key = self.private_key.public_key()
        else:
            public_key = serialization.load_pem_public_key(
                data=self.get_public_pem(), backend=default_backend()
            )

        return public_key

    def get_public_key_bytes(self):
        return self.public_key_bytes

    def get_private_key_bytes(self):
        ecc_key_size = {
            "secp256r1": ec.SECP256R1.key_size,
            "secp224r1": ec.SECP224R1.key_size,
            "secp384r1": ec.SECP384R1.key_size,
            "secp521r1": 528,  # Setting fixed size of 66 bytes instead of 521 bits
            "secp256k1": ec.SECP256K1.key_size,
        }

        if self.private_key is None:
            raise ValueError("Private key is not available")

        if self.key_info.get("algo") == "RSA":
            private = self.private_key.private_numbers()
            private_key_p = bytearray(
                private.p.to_bytes(int((self.key_info.get("size") / 8) / 2), "big")
            )
            private_key_q = bytearray(
                private.q.to_bytes(int((self.key_info.get("size") / 8) / 2), "big")
            )
            return private_key_p + private_key_q

        elif self.key_info.get("algo") == "ECC":
            return bytearray(
                self.private_key.private_numbers().private_value.to_bytes(
                    int(ecc_key_size.get(self.key_info.get("size")) / 8), "big"
                )
            )

        else:
            return bytearray(
                self.private_key.private_numbers().private_value.to_bytes(
                    int(ecc_key_size.get("secp256r1") / 8), "big"
                )
            )


# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == "__main__":
    pass
