import os
import struct
from pathlib import Path

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


# AES-GCM 256 bit encryption & decryption methods
class CipherAESGCM:
    def __init__(self, aes_key=None):
        self.aes_key = aes_key or bytes(os.urandom(32))

    """
    Perform an AES-GCM encryption with random iv generated internally.
    Args:
        plaintext           Plaintext to be encrypted in bytes
    Returns:
        ciphertext, tag, iv
    """

    def encrypt(self, plain_text):
        iv = bytes(os.urandom(12))
        cipher = Cipher(algorithms.AES(self.aes_key), modes.GCM(iv), backend=default_backend())

        encryptor = cipher.encryptor()
        cipher_text = encryptor.update(plain_text) + encryptor.finalize()
        return cipher_text, encryptor.tag, iv

    """
    Perform an AES-GCM decryption operation.
    Args:
        cipher_text           Encrypted cipher text
        iv                    12 byte Initialization vector used in encryption
        tag                   16 byte Tag
    Returns:
        plaintext
    """

    def decrypt(self, cipher_text, iv, tag):
        cipher = Cipher(algorithms.AES(self.aes_key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        plain_text = decryptor.update(cipher_text) + decryptor.finalize()
        return plain_text

    def get_key_bytes(self):
        return self.aes_key


# AES-GCM 256 bit encryption & decryption methods


class CipherAESCBC:
    def __init__(self, aes_key=None, aes_iv=None):
        self.aes_key = aes_key or bytes(os.urandom(32))
        self.aes_iv = aes_iv or bytes(os.urandom(16))

    """
    Perform an AES-GCM encryption with random iv generated internally.
    Args:
        plaintext           Plaintext to be encrypted in bytes
    Returns:
        ciphertext, tag, iv
    """

    def encrypt(self, plain_text):
        cipher = Cipher(
            algorithms.AES(self.aes_key), modes.CBC(self.aes_iv), backend=default_backend()
        )

        encryptor = cipher.encryptor()
        cipher_text = encryptor.update(plain_text) + encryptor.finalize()
        return cipher_text, self.aes_iv

    """
    Perform an AES-GCM decryption operation.
    Args:
        cipher_text           Encrypted cipher text
        iv                    12 byte Initialization vector used in encryption
        tag                   16 byte Tag
    Returns:
        plaintext
    """

    def decrypt(self, cipher_text):
        cipher = Cipher(
            algorithms.AES(self.aes_key), modes.CBC(self.aes_iv), backend=default_backend()
        )
        decryptor = cipher.decryptor()
        plain_text = decryptor.update(cipher_text) + decryptor.finalize()
        return plain_text


# RSA2048 bit encryption methods
class CipherRSA:
    def __init__(self, rsa_key_file=None):
        if rsa_key_file is None:
            self.private_key = rsa.generate_private_key(
                public_exponent=65537, key_size=4096, backend=default_backend()
            )
            self.rsa_public_key = self.private_key.public_key()
        else:
            self.rsa_public_key = self.__get_public_key(rsa_key_file)

    """
    Perform an RSA encryption.
    Args:
        plaintext           Plaintext to be encrypted in bytes
    Returns:
        ciphertext
    """

    def encrypt(self, message):
        ciphertext = self.rsa_public_key.encrypt(
            message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None
            ),
        )
        return ciphertext

    def decrypt(self, ciphertext):
        plaintext = self.private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None
            ),
        )
        return plaintext

    def encrypt_dten(self, message):
        aes_gcm = CipherAESGCM()

        cipher_text, tag, iv = aes_gcm.encrypt(message)

        wrapped_key = self.rsa_public_key.encrypt(
            aes_gcm.aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None
            ),
        )

        wrapped_key_len = struct.pack(">L", len(wrapped_key))
        iv_len = struct.pack(">L", len(iv))
        cipher_text_len = struct.pack(">L", len(cipher_text))
        tag_len = struct.pack(">L", len(tag))

        return (
            wrapped_key_len
            + wrapped_key
            + iv_len
            + iv
            + cipher_text_len
            + cipher_text
            + tag_len
            + tag
        )

    def __get_public_key(self, rsa_public_key):
        if os.path.isfile(Path(rsa_public_key)):
            with open(rsa_public_key, "rb") as pkFile:
                public_pem_data = pkFile.read()
            rsa_publicKey = serialization.load_pem_public_key(
                public_pem_data, backend=default_backend()
            )
        elif isinstance(rsa_public_key, str):
            modulus = int(rsa_public_key, 16)
            exponent = 65537
            rsa_publicKey = rsa.RSAPublicNumbers(exponent, modulus).public_key(default_backend())
        else:
            raise ValueError("Invalid RSA key format")

        return rsa_publicKey

    def export_rsa_keys(self, file=None):
        private_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        if file:
            with open(file + "_private.pem", "wb") as key_file:
                key_file.write(private_pem)
        return private_pem

    def export_rsa_public_key(self, file=None):
        public_key = self.private_key.public_key()
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        if file:
            with open(file + "_public.pem", "wb") as key_file:
                key_file.write(pem)

    def get_key_bytes(self):
        return self.rsa_public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )


__all__ = ["CipherAESGCM", "CipherAESCBC", "CipherRSA"]
