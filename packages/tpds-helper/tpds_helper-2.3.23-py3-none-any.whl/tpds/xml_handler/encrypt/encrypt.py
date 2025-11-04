from argparse import ArgumentParser
from base64 import b64decode, b64encode
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa, ed25519, x25519
from lxml import etree

from .ciphers import CipherAESGCM, CipherRSA


class GenerateEncryptedXml:
    """
    This class takes the xml file with random secret unencrypted and
    generate the new xml file with random secret encrypted
    """

    def __init__(self, input_file, encryption_key_file) -> None:
        self.input_file = input_file
        self.tree = etree.parse(self.input_file, etree.XMLParser(remove_blank_text=True))
        self.root = self.tree.getroot()
        self.aes = CipherAESGCM()
        self.rsa = CipherRSA(encryption_key_file)
        self.aes_key = self.aes.get_key_bytes()
        self.wrap_key_name = "WrapKey1"
        # print(f'Generated AES Key - {self.aes_key.hex()}')

    def convert_bytes_to_encrypted_data(self, secret: bytes) -> bytes:
        """
        Function convert the random secret to encrypted data
        Args - random secret
        Return - encrypted secret
        """
        cipher_text, tag, iv = self.aes.encrypt(secret)
        # -- Format the encrypted data - iv_len, iv, cipher_len, cipher, tag_len, tag

        encrypted_data = bytes()
        encrypted_data += len(iv).to_bytes(length=4, byteorder="big")
        encrypted_data += iv
        encrypted_data += len(cipher_text).to_bytes(length=4, byteorder="big")
        encrypted_data += cipher_text
        encrypted_data += len(tag).to_bytes(length=4, byteorder="big")
        encrypted_data += tag

        return encrypted_data

    def encode_encrypted_attribute(self, is_encrypted: bool) -> str:
        if self.root.nsmap[None] == "https://www.microchip.com/schema/TA100_Config_1.0":
            # This early config used lower case boolean names for just this attribute, which was inconsistent with
            # other fields
            return "true" if is_encrypted else "false"
        else:
            # Later configs fixed this inconsistency and used capitalized boolean names
            return "True" if is_encrypted else "False"

    def encrypt_bytes(self, secret_element: etree.Element):
        if sum(1 for _ in secret_element.iter()) > 1:
            raise ValueError(
                "Secret element has more than one node, which is not supported. Embedded comment?"
            )
        if secret_element.text is None:
            raise ValueError(f'Key Value field is empty for {secret_element.attrib["key_name"]} handle.')
        if secret_element.attrib["algorithm"] != "AES256_GCM":
            raise ValueError(f'Unsupported algorithm "{secret_element.attrib["algorithm"]}".')
        # There were some changes around the style of the encrypted attribute (false and False).
        if secret_element.attrib["encrypted"].lower() != "false":
            raise ValueError(
                f'Unexpected encrypted attribute "{secret_element.attrib["encrypted"]}". Should be false.'
            )

        if secret_element.attrib["encoding"] == "Hex":
            data = bytes.fromhex(secret_element.text)
        elif secret_element.attrib["encoding"] == "Base64":
            data = b64decode(secret_element.text)
        else:
            raise ValueError(f'Unsupported encoding "{secret_element.attrib["encoding"]}".')
        encrypted_data = self.convert_bytes_to_encrypted_data(data)
        if secret_element.attrib["encoding"] == "Hex":
            encoded_encrypted_data = encrypted_data.hex()
        elif secret_element.attrib["encoding"] == "Base64":
            encoded_encrypted_data = b64encode(encrypted_data)
        else:
            raise ValueError(f'Unsupported encoding "{secret_element.attrib["encoding"]}".')

        secret_element.attrib["encrypted"] = self.encode_encrypted_attribute(True)
        secret_element.attrib["key_name"] = self.wrap_key_name
        self.set_indent_element_text(
            element=secret_element, data=self.format_data(data=encoded_encrypted_data)
        )

    def encrypt_rsa_public_key(self, secret_element: etree.Element):
        if sum(1 for _ in secret_element.iter()) > 1:
            raise ValueError(
                "Secret element has more than one node, which is not supported. Embedded comment?"
            )
        if secret_element.text is None:
            raise ValueError(f'Key Value field is empty for {secret_element.attrib["key_name"]} handle.')
        if secret_element.attrib["algorithm"] != "AES256_GCM":
            raise ValueError(f'Unsupported algorithm "{secret_element.attrib["algorithm"]}".')
        if secret_element.attrib["encrypted"].lower() != "false":
            raise ValueError(
                f'Unexpected encrypted attribute "{secret_element.attrib["encrypted"]}". Should be false.'
            )

        if secret_element.attrib["encoding"] == "Hex":
            if secret_element.attrib["format"] != "TA100_Write":
                raise ValueError(
                    (
                        f'Unexpected format attribute "{secret_element.attrib["format"]}"'
                        f' for "{secret_element.attrib["encoding"]}" encoding. Expected TA100_Write.'
                    )
                )
            data = bytes.fromhex(secret_element.text)
        elif secret_element.attrib["encoding"] == "Base64":
            if secret_element.attrib["format"] != "TA100_Write":
                raise ValueError(
                    (
                        f'Unexpected format attribute "{secret_element.attrib["format"]}"'
                        f' for "{secret_element.attrib["encoding"]}" encoding. Expected TA100_Write.'
                    )
                )
            data = b64decode(secret_element.text)
        elif secret_element.attrib["encoding"] == "PEM":
            if secret_element.attrib["format"] != "Subject_Public_Key_Info":
                raise ValueError(
                    (
                        f'Unexpected format attribute "{secret_element.attrib["format"]}"'
                        f' for "{secret_element.attrib["encoding"]}" encoding. Expected Subject_Public_Key_Info.'
                    )
                )
            public_key = serialization.load_pem_public_key(secret_element.text.encode("utf8"))
            if not isinstance(public_key, rsa.RSAPublicKey):
                raise ValueError("Subject_Public_Key_Info is not for an RSA public key.")
            # Convert the public key to TA100_Write format (only one support right now)
            # TA100_Write format omits the exponent, since it must be 65537 in most cases (3072 can also use 3, but
            # that's also not supported yet). Make sure the exponent is expected.
            if public_key.public_numbers().e != 65537:
                raise ValueError(
                    (
                        f"RSA public key has unsupported exponent {public_key.public_numbers().e}."
                        f" Must be 65537 for TA100."
                    )
                )
            data = public_key.public_numbers().n.to_bytes(public_key.key_size / 8, byteorder="big")
        else:
            raise ValueError(f'Unsupported encoding "{secret_element.attrib["encoding"]}".')

        encrypted_data = self.convert_bytes_to_encrypted_data(data)

        secret_element.attrib["encoding"] = "Hex"
        secret_element.attrib["encrypted"] = self.encode_encrypted_attribute(True)
        secret_element.attrib["key_name"] = self.wrap_key_name

        self.set_indent_element_text(
            element=secret_element, data=self.format_data(data=encrypted_data.hex())
        )

    def encrypt_rsa_private_key(self, secret_element: etree.Element):
        if secret_element.text is None:
            raise ValueError(f'Key Value field is empty for {secret_element.attrib["key_name"]} handle.')
        if secret_element.attrib["algorithm"] != "AES256_GCM":
            raise ValueError(f'Unsupported algorithm "{secret_element.attrib["algorithm"]}".')
        if secret_element.attrib['encrypted'].lower() != 'false':
            raise ValueError(
                f'Unexpected encrypted attribute "{secret_element.attrib["encrypted"]}". Should be false.'
            )

        if secret_element.attrib["format"] != "TA100_Write":
            raise ValueError(
                f'Unexpected format attribute "{secret_element.attrib["format"]}". Only expected TA100_Write.'
            )
        if secret_element.attrib["encoding"] == "Hex":
            data = bytes.fromhex(secret_element.text)
        elif secret_element.attrib["encoding"] == "Base64":
            data = b64decode(secret_element.text)
        else:
            raise ValueError(f'Unhandled encoding {secret_element.attrib["encoding"]}.')

        encrypted_data = self.convert_bytes_to_encrypted_data(data)

        secret_element.attrib["encoding"] = "Hex"
        secret_element.attrib["encrypted"] = self.encode_encrypted_attribute(True)
        secret_element.attrib["key_name"] = self.wrap_key_name

        self.set_indent_element_text(
            element=secret_element, data=self.format_data(data=encrypted_data.hex())
        )

    def encrypt_ecc_public_key(self, secret_element: etree.Element):
        if sum(1 for _ in secret_element.iter()) > 1:
            raise ValueError(
                "Secret element has more than one node, which is not supported. Embedded comment?"
            )
        if secret_element.text is None:
            raise ValueError(f'Key Value field is empty for {secret_element.attrib["key_name"]} handle.')
        if secret_element.attrib["algorithm"] != "AES256_GCM":
            raise ValueError(f'Unsupported algorithm "{secret_element.attrib["algorithm"]}".')
        if secret_element.attrib["encrypted"].lower() != "false":
            raise ValueError(
                f'Unexpected encrypted attribute "{secret_element.attrib["encrypted"]}". Should be false.'
            )

        if secret_element.attrib["encoding"] == "Hex":
            if secret_element.attrib["format"] != "TA100_Write":
                raise ValueError(
                    (
                        f'Unexpected format attribute "{secret_element.attrib["format"]}"'
                        f' for "{secret_element.attrib["encoding"]}" encoding. Expected TA100_Write.'
                    )
                )
            data = bytes.fromhex(secret_element.text)
        elif secret_element.attrib["encoding"] == "Base64":
            if secret_element.attrib["format"] != "TA100_Write":
                raise ValueError(
                    (
                        f'Unexpected format attribute "{secret_element.attrib["format"]}"'
                        f' for "{secret_element.attrib["encoding"]}" encoding. Expected TA100_Write.'
                    )
                )
            data = b64decode(secret_element.text)
        elif secret_element.attrib["encoding"] == "PEM":
            if secret_element.attrib["format"] != "Subject_Public_Key_Info":
                raise ValueError(
                    (
                        f'Unexpected format attribute "{secret_element.attrib["format"]}"'
                        f' for "{secret_element.attrib["encoding"]}" encoding. Expected Subject_Public_Key_Info.'
                    )
                )
            public_key = serialization.load_pem_public_key(secret_element.text.encode("utf8"))
            if not isinstance(public_key, ec.EllipticCurvePublicKey):
                raise ValueError("Subject_Public_Key_Info is not for an ECC public key.")
            # Convert the public key to TA100_Write format (only one supported right now)
            data = public_key.public_bytes(
                encoding=serialization.Encoding.X962,
                format=serialization.PublicFormat.UncompressedPoint,
            )[1:]
        else:
            raise ValueError(f'Unsupported encoding "{secret_element.attrib["encoding"]}".')

        encrypted_data = self.convert_bytes_to_encrypted_data(data)

        secret_element.attrib["encoding"] = "Hex"
        secret_element.attrib["encrypted"] = self.encode_encrypted_attribute(True)
        secret_element.attrib["key_name"] = self.wrap_key_name

        self.set_indent_element_text(
            element=secret_element, data=self.format_data(data=encrypted_data.hex())
        )

    def encrypt_ecc_private_key(self, secret_element: etree.Element):
        if secret_element.text is None:
            raise ValueError(f'Key Value field is empty for {secret_element.attrib["key_name"]} handle.')
        if secret_element.attrib["algorithm"] != "AES256_GCM":
            raise ValueError(f'Unsupported algorithm "{secret_element.attrib["algorithm"]}".')
        if secret_element.attrib["encrypted"].lower() != "false":
            raise ValueError(
                f'Unexpected encrypted attribute "{secret_element.attrib["encrypted"]}". Should be false.'
            )

        if secret_element.attrib["encoding"] == "Hex":
            data = bytes.fromhex(secret_element.text)
        elif secret_element.attrib["encoding"] == "Base64":
            data = b64decode(secret_element.text)
        else:
            raise ValueError(f'Unhandled encoding {secret_element.attrib["encoding"]}.')

        if secret_element.attrib["format"] == "PKCS8":
            # Assume data is unencrypted PKCS#8 in DER encoding
            private_key = serialization.load_der_private_key(data=data, password=None)
            if not isinstance(private_key, ec.EllipticCurvePrivateKey):
                raise ValueError("Private key is not ECC")

            # We need to convert PKCS#8 private keys to TA100_Write format as that's the only encrypted private key
            # format supported right now.

            # Calculate number of bytes required to hold the private key value.
            # The +7 rounds the count up when the bit size isn't a multiple of 8 (e.g. 521)
            byte_count = (private_key.key_size + 7) // 8

            # TA100_Write ECC private key format is the private key value in big-endian format
            data = private_key.private_numbers().private_value.to_bytes(
                byte_count, byteorder="big", signed=False
            )
            secret_element.attrib["format"] = "TA100_Write"
        elif secret_element.attrib["format"] != "TA100_Write":
            raise ValueError(
                f'Unexpected format attribute "{secret_element.attrib["format"]}". Only expected TA100_Write.'
            )

        encrypted_data = self.convert_bytes_to_encrypted_data(data)

        secret_element.attrib["encoding"] = "Hex"
        secret_element.attrib["encrypted"] = self.encode_encrypted_attribute(True)
        secret_element.attrib["key_name"] = self.wrap_key_name

        self.set_indent_element_text(
            element=secret_element, data=self.format_data(data=encrypted_data.hex())
        )

    def encrypt_ed25519_public_key(self, secret_element: etree.Element):
        if sum(1 for _ in secret_element.iter()) > 1:
            raise ValueError(
                "Secret element has more than one node, which is not supported. Embedded comment?"
            )
        if secret_element.text is None:
            raise ValueError(f'Key Value field is empty for {secret_element.attrib["key_name"]} handle.')
        if secret_element.attrib["algorithm"] != "AES256_GCM":
            raise ValueError(f'Unsupported algorithm "{secret_element.attrib["algorithm"]}".')
        if secret_element.attrib["encrypted"].lower() != "false":
            raise ValueError(
                f'Unexpected encrypted attribute "{secret_element.attrib["encrypted"]}". Should be false.'
            )

        if secret_element.attrib["encoding"] == "Hex":
            if secret_element.attrib["format"] != "TA100_Write":
                raise ValueError(
                    (
                        f'Unexpected format attribute "{secret_element.attrib["format"]}"'
                        f' for "{secret_element.attrib["encoding"]}" encoding. Expected TA100_Write.'
                    )
                )
            data = bytes.fromhex(secret_element.text)
        elif secret_element.attrib["encoding"] == "PEM":
            if secret_element.attrib["format"] != "Subject_Public_Key_Info":
                raise ValueError(
                    (
                        f'Unexpected format attribute "{secret_element.attrib["format"]}"'
                        f' for "{secret_element.attrib["encoding"]}" encoding. Expected Subject_Public_Key_Info.'
                    )
                )
            public_key = serialization.load_pem_public_key(secret_element.text.encode("utf8"))
            if not isinstance(public_key, ed25519.Ed25519PublicKey):
                raise ValueError("Subject_Public_Key_Info is not for an Ed25519 public key.")
            # Convert the public key to TA100_Write format (only one supported right now)
            data = public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
        else:
            raise ValueError(
                f'Unsupported encoding "{secret_element.attrib["encoding"]}".'
            )

        encrypted_data = self.convert_bytes_to_encrypted_data(data)

        secret_element.attrib["encoding"] = "Hex"
        secret_element.attrib["encrypted"] = self.encode_encrypted_attribute(True)
        secret_element.attrib["key_name"] = self.wrap_key_name

        self.set_indent_element_text(
            element=secret_element, data=self.format_data(data=encrypted_data.hex())
        )

    def encrypt_ed25519_private_key(self, secret_element: etree.Element):
        if secret_element.text is None:
            raise ValueError(f'Key Value field is empty for {secret_element.attrib["key_name"]} handle.')
        if secret_element.attrib["algorithm"] != "AES256_GCM":
            raise ValueError(
                f'Unsupported algorithm "{secret_element.attrib["algorithm"]}".'
            )
        if secret_element.attrib["encrypted"].lower() != "false":
            raise ValueError(
                f'Unexpected encrypted attribute "{secret_element.attrib["encrypted"]}". Should be false.'
            )

        if secret_element.attrib["encoding"] != "Hex":
            raise ValueError(
                f'Unhandled encoding {secret_element.attrib["encoding"]}.'
            )

        if secret_element.attrib["format"] != "TA100_Write":
            raise ValueError(
                f'Unexpected format attribute "{secret_element.attrib["format"]}". Only expected TA100_Write.'
            )

        if secret_element.attrib["format"] == "TA100_Write":
            # Assume data is unencrypted TA100_Write in PEM encoding
            data = bytes.fromhex(secret_element.text)

        encrypted_data = self.convert_bytes_to_encrypted_data(data)

        secret_element.attrib["encoding"] = "Hex"
        secret_element.attrib["encrypted"] = self.encode_encrypted_attribute(True)
        secret_element.attrib["key_name"] = self.wrap_key_name

        self.set_indent_element_text(
            element=secret_element, data=self.format_data(data=encrypted_data.hex())
        )

    def encrypt_x25519_public_key(self, secret_element: etree.Element):
        if sum(1 for _ in secret_element.iter()) > 1:
            raise ValueError(
                "Secret element has more than one node, which is not supported. Embedded comment?"
            )
        if secret_element.text is None:
            raise ValueError(f'Key Value field is empty for {secret_element.attrib["key_name"]} handle.')
        if secret_element.attrib["algorithm"] != "AES256_GCM":
            raise ValueError(
                f'Unsupported algorithm "{secret_element.attrib["algorithm"]}".'
            )
        if secret_element.attrib["encrypted"].lower() != "false":
            raise ValueError(
                f'Unexpected encrypted attribute "{secret_element.attrib["encrypted"]}". Should be false.'
            )

        if secret_element.attrib["encoding"] == "Hex":
            if secret_element.attrib["format"] != "TA100_Write":
                raise ValueError(
                    (
                        f'Unexpected format attribute "{secret_element.attrib["format"]}"'
                        f' for "{secret_element.attrib["encoding"]}" encoding. Expected TA100_Write.'
                    )
                )
            data = bytes.fromhex(secret_element.text)
        elif secret_element.attrib["encoding"] == "PEM":
            if secret_element.attrib["format"] != "Subject_Public_Key_Info":
                raise ValueError(
                    (
                        f'Unexpected format attribute "{secret_element.attrib["format"]}"'
                        f' for "{secret_element.attrib["encoding"]}" encoding. Expected Subject_Public_Key_Info.'
                    )
                )
            public_key = serialization.load_pem_public_key(secret_element.text.encode("utf8"))
            if not isinstance(public_key, x25519.X25519PublicKey):
                raise ValueError("Subject_Public_Key_Info is not for an X25519 public key.")
            # Convert the public key to TA100_Write format (only one supported right now)
            data = public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
        else:
            raise ValueError(
                f'Unsupported encoding "{secret_element.attrib["encoding"]}".'
            )

        encrypted_data = self.convert_bytes_to_encrypted_data(data)

        secret_element.attrib["encoding"] = "Hex"
        secret_element.attrib["encrypted"] = self.encode_encrypted_attribute(True)
        secret_element.attrib["key_name"] = self.wrap_key_name

        self.set_indent_element_text(
            element=secret_element, data=self.format_data(data=encrypted_data.hex())
        )

    def encrypt_x25519_private_key(self, secret_element: etree.Element):
        if secret_element.text is None:
            raise ValueError(f'Key Value field is empty for {secret_element.attrib["key_name"]} handle.')
        if secret_element.attrib["algorithm"] != "AES256_GCM":
            raise ValueError(
                f'Unsupported algorithm "{secret_element.attrib["algorithm"]}".'
            )
        if secret_element.attrib["encrypted"].lower() != "false":
            raise ValueError(
                f'Unexpected encrypted attribute "{secret_element.attrib["encrypted"]}". Should be false.'
            )

        if secret_element.attrib["encoding"] != "Hex":
            raise ValueError(
                f'Unhandled encoding {secret_element.attrib["encoding"]}.'
            )

        if secret_element.attrib["format"] != "TA100_Write":
            raise ValueError(
                f'Unexpected format attribute "{secret_element.attrib["format"]}". Only expected TA100_Write.'
            )

        if secret_element.attrib["format"] == "TA100_Write":
            # Assume data is unencrypted TA100_Write in PEM encoding
            data = bytes.fromhex(secret_element.text)

        encrypted_data = self.convert_bytes_to_encrypted_data(data)

        secret_element.attrib["encoding"] = "Hex"
        secret_element.attrib["encrypted"] = self.encode_encrypted_attribute(True)
        secret_element.attrib["key_name"] = self.wrap_key_name

        self.set_indent_element_text(
            element=secret_element, data=self.format_data(data=encrypted_data.hex())
        )

    def parse_datasource_section(self):
        """
        Function iterate over datasource section and find the secret element.
        """
        for secret_element in self.tree.findall("//Secret", namespaces=self.root.nsmap):
            ns = f"{{{secret_element.nsmap[None]}}}"
            if secret_element.getparent().tag == f"{ns}Static_Bytes":
                self.encrypt_bytes(secret_element=secret_element)
            elif secret_element.getparent().tag == f"{ns}Static_RSA_Public_Key":
                self.encrypt_rsa_public_key(secret_element=secret_element)
            elif secret_element.getparent().tag == f"{ns}Static_RSA_Private_Key":
                self.encrypt_rsa_private_key(secret_element=secret_element)
            elif secret_element.getparent().tag == f"{ns}Static_ECC_Public_Key":
                self.encrypt_ecc_public_key(secret_element=secret_element)
            elif secret_element.getparent().tag == f"{ns}Static_ECC_Private_Key":
                self.encrypt_ecc_private_key(secret_element=secret_element)
            elif secret_element.getparent().tag == f"{ns}Static_Ed25519_Public_Key":
                self.encrypt_ed25519_public_key(secret_element=secret_element)
            elif secret_element.getparent().tag == f"{ns}Static_Ed25519_Private_Key":
                self.encrypt_ed25519_private_key(secret_element=secret_element)
            elif secret_element.getparent().tag == f"{ns}Static_X25519_Public_Key":
                self.encrypt_x25519_public_key(secret_element=secret_element)
            elif secret_element.getparent().tag == f"{ns}Static_X25519_Private_Key":
                self.encrypt_x25519_private_key(secret_element=secret_element)
            else:
                raise ValueError(f"Secret {secret_element.getparent().tag} is not supported.")

    def generate(self) -> bytes:
        """
        Function create new xml file with updated content
        """
        return etree.tostring(self.tree, pretty_print=True, xml_declaration=True, encoding="UTF-8")

    @staticmethod
    def set_indent_element_text(element: etree.Element, data: str, indent: str = "  ") -> None:
        level = 1
        parent = element.getparent()
        while parent is not None:
            level += 1
            parent = parent.getparent()
        data_indent = indent * level

        element.text = (
            "\n"
            + data_indent
            + data.replace("\n", f"\n{data_indent}")
            + "\n"
            + indent * (level - 1)
        )

    @staticmethod
    def format_data(data: str, split_len: int = 64) -> str:
        return "\n".join(data[i : i + split_len] for i in range(0, len(data), split_len))

    def add_wrapped_key(self):
        """
        Function encrypt the aes key with encryption key
        """

        encrypted_aes_key = self.rsa.encrypt(self.aes_key)
        # print(f'Wrapped AES Key - {self.format_data(encrypted_aes_key.hex())}')

        data_sources_element = self.root.find("Data_Sources", namespaces=self.root.nsmap)
        wrapped_key_element = etree.SubElement(data_sources_element, "Wrapped_Key")

        etree.SubElement(wrapped_key_element, "Name").text = self.wrap_key_name

        key_element = etree.SubElement(wrapped_key_element, "Key")
        key_element.attrib["algorithm"] = "RSA_OAEP_SHA256"
        key_element.attrib["encoding"] = "Hex"
        self.set_indent_element_text(
            element=key_element, data=self.format_data(encrypted_aes_key.hex())
        )

        wrapping_public_key_element = etree.SubElement(wrapped_key_element, "Wrapping_Public_Key")
        wrapping_public_key_element.attrib["encoding"] = "PEM"
        wrapping_public_key_element.attrib["format"] = "Subject_Public_Key_Info"
        self.set_indent_element_text(
            element=wrapping_public_key_element,
            data=self.rsa.rsa_public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            ).decode("utf8"),
        )


if __name__ == "__main__":
    parser = ArgumentParser(description="Encrypts static secret data in a provisioning config file.")
    parser.add_argument(
        "--in",
        help="Path to unencrypted provisioning config file with plain-text secrets.",
        required=True
    )
    parser.add_argument(
        "--out",
        help="Encrypted provisioning config file wil be saved to this path.",
        required=True
    )
    parser.add_argument(
        "--key",
        help="Path to the public key to wrap/encrypt the secret data with.",
        required=True
    )
    args = vars(parser.parse_args())

    xml = GenerateEncryptedXml(input_file=args["in"], encryption_key_file=args["key"])
    xml.parse_datasource_section()
    xml.add_wrapped_key()
    Path(args["out"]).write_bytes(xml.generate())
