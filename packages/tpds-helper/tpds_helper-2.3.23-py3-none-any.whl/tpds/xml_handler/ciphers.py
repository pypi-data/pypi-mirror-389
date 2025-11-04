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

import os
import re
from base64 import b64decode
from pathlib import Path
from xml.dom import minidom

import cryptography.hazmat.primitives.padding as aes_padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class Hash_Sha256:
    def __init__(self):
        self.sha256_init()

    def sha256_init(self):
        self.sha256 = hashes.Hash(hashes.SHA256(), backend=default_backend())

    def sha256_update(self, data):
        self.sha256.update(data)

    def sha256_hash(self, data=None):
        if data is not None:
            self.sha256.update(data)
        return self.sha256.finalize()


class Cipher_AES:
    def __init__(self, aes_key=None, aes_iv=None):
        self.aes_key = aes_key or os.urandom(32)
        # print(f'AES Key: {self.aes_key.hex()}\n{list(self.aes_key)}')
        self.aes_iv = aes_iv or os.urandom(16)
        # print(f'AES IV: {self.aes_iv.hex()}\n{list(self.aes_iv)}')
        self.cipher = Cipher(
            algorithms.AES(self.aes_key), modes.CBC(self.aes_iv), backend=default_backend()
        )

    def encrypt(self, plain_text):
        plain_text = plain_text.hex().encode()
        cipher_text = bytearray(len(plain_text) * 2)
        padder = aes_padding.PKCS7(algorithms.AES.block_size).padder()
        # print(f'Plain text: {plain_text.hex()}')
        padded_data = padder.update(plain_text) + padder.finalize()
        encryptor = self.cipher.encryptor()
        len_encrypted = encryptor.update_into(padded_data, cipher_text)
        encryptor.finalize()
        # print(f'Cipher text: {cipher_text[:len_encrypted].hex()}')
        return cipher_text[:len_encrypted]

    def decrypt(self, cipher_text):
        plain_text = bytearray(len(cipher_text) + len(self.aes_iv))
        decryptor = self.cipher.decryptor()
        len_decrypted = decryptor.update_into(cipher_text, plain_text)
        decryptor.finalize()
        return plain_text[:len_decrypted]

    def get_key_iv(self):
        return self.aes_key + self.aes_iv


class Cipher_RSA:
    def __init__(self, rsa_key_xml_file=""):
        self.rsa_public_key = self.__get_public_key(rsa_key_xml_file)

    def encrypt(self, message):
        # print(f'RSA Input: {message.hex()}')
        ciphertext = self.rsa_public_key.encrypt(message, padding.PKCS1v15())
        # print(f'RSA Output: {ciphertext.hex()}')
        return ciphertext

    def __get_public_key(self, file_publickey_xml):
        if os.path.isfile(Path(file_publickey_xml)):
            with open(file_publickey_xml, "r") as pkFile:
                xmlPublicKey = pkFile.read()
            xmlPublicKey = re.sub(".*?xmlversion.*\n?", "", xmlPublicKey)
            rsaKeyValue = minidom.parseString(xmlPublicKey)
            modulus = self.__getLong(rsaKeyValue.getElementsByTagName("Modulus")[0].childNodes)
            exponent = self.__getLong(rsaKeyValue.getElementsByTagName("Exponent")[0].childNodes)
            rsa_publicKey = rsa.RSAPublicNumbers(exponent, modulus).public_key(default_backend())
            # public_key_file = os.path.splitext(file_publickey_xml)[0] + ".key"
        else:
            private_key_file = "Generated_RSA_Private.key"
            # public_key_file = "Generated_RSA_Public.key"
            rsa_private_key = rsa.generate_private_key(
                public_exponent=65537, key_size=2048, backend=default_backend()
            )
            with open(private_key_file, "wb") as key_file:
                key_file.write(
                    rsa_private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.TraditionalOpenSSL,
                        encryption_algorithm=serialization.NoEncryption(),
                    )
                )
            rsa_publicKey = rsa_private_key.public_key()

        # with open(public_key_file, 'wb') as key_file:
        #     key_file.write(rsa_publicKey.public_bytes(
        #         encoding=serialization.Encoding.PEM,
        #         format=serialization.PublicFormat.SubjectPublicKeyInfo))
        return rsa_publicKey

    def __getLong(self, nodelist):
        rc = []
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                rc.append(node.data)
        string = "".join(rc)
        return int.from_bytes(b64decode(string), byteorder="big")


class Ciphers(Cipher_AES, Cipher_RSA, Hash_Sha256):
    def __init__(self, rsa_key_xml_file="", aes_key=None, aes_iv=None):
        Cipher_AES.__init__(self, aes_key, aes_iv)
        Cipher_RSA.__init__(self, rsa_key_xml_file)
        Hash_Sha256.__init__(self)

    def encrypt_slot(self, slot_data):
        return Cipher_AES.encrypt(self, slot_data)

    def encrypt_aes_key_iv(self):
        return Cipher_RSA.encrypt(self, self.get_key_iv())


__all__ = ["Hash_Sha256", "Cipher_AES", "Cipher_RSA", "Ciphers"]

# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == "__main__":
    pass
