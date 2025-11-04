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

import warnings

from cryptography import utils

warnings.filterwarnings(action="ignore", category=utils.CryptographyDeprecationWarning)
import os
import re
from datetime import datetime, timezone

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import ec

from tpds.tp_utils.tp_keys import TPAsymmetricKey

from .cert import Cert
from .cert_utils import (
    add_signer_extensions,
    get_backend,
    get_device_public_key,
    get_device_sn_number,
    pubkey_cert_sn,
    random_cert_sn,
)
from .create_cert_defs import CertDef
from .ext_builder import TimeFormat


class TFLEXCerts:
    def __init__(self, device_name=""):
        self.device_name = device_name
        self.root = Cert()
        self.signer_csr = Cert()
        self.signer = Cert()
        self.device = Cert()

        self.root.key = TPAsymmetricKey()
        self.signer_csr.key = TPAsymmetricKey()
        self.signer.key = TPAsymmetricKey()
        self.device.key = TPAsymmetricKey()

    def build_root(
        self,
        key=None,
        org_name="Microchip Technology Inc",
        common_name="Crypto Authentication Root CA 002",
        validity=40,
        user_pub_key=None,
    ):
        """
        Function to build the root certificate

        Inputs:
            key           the private key used for generating the root
                            certificate.
            org_name      Organisation name to be set in the certificate
            common_name   Common name to be set in the certificate
            validity      Validity to be set in the certificate
        """

        if key:
            self.root.key.set_private_key(key)

        self.root.builder = self.root.builder.subject_name(
            x509.Name(
                [
                    x509.NameAttribute(x509.oid.NameOID.ORGANIZATION_NAME, org_name),
                    x509.NameAttribute(x509.oid.NameOID.COMMON_NAME, common_name),
                ]
            )
        )
        # Names are the same for a self-signed certificate
        self.root.builder = self.root.builder.issuer_name(self.root.builder._subject_name)
        self.root.builder = self.root.builder.not_valid_before(
            datetime.utcnow().replace(tzinfo=timezone.utc)
        )
        self.root.builder = self.root.builder.not_valid_after(
            self.root.builder._not_valid_before.replace(
                year=self.root.builder._not_valid_before.year + 40
            )
        )
        if user_pub_key:
            root_pub_key = ec.EllipticCurvePublicNumbers(
                x=int(user_pub_key[:64], 16), y=int(user_pub_key[64:], 16), curve=ec.SECP256R1()
            ).public_key(get_backend())
            self.root.builder = self.root.builder.public_key(root_pub_key)
        else:
            self.root.builder = self.root.builder.public_key(self.root.key.get_public_key())
        self.root.builder = self.root.builder.serial_number(random_cert_sn(16))
        self.root.builder = self.root.builder.add_extension(
            x509.SubjectKeyIdentifier.from_public_key(self.root.builder._public_key), critical=False
        )
        self.root.builder = self.root.builder.add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(self.root.builder._public_key),
            critical=False,
        )
        self.root.builder = self.root.builder.add_extension(
            x509.BasicConstraints(ca=True, path_length=None), critical=True
        )

        self.root.sign_builder(self.root.key.private_key)

    def build_signer_csr(
        self,
        key=None,
        org_name="Microchip Technology Inc",
        common_name="Crypto Authentication Signer ",
        signer_id="FFFF",
    ):
        """
        Function to build the signer csr certificate

        Inputs:
            key           the private key used for generating the signer csr.
            org_name      Organisation name to be set in the certificate
            common_name   Common name to be set in the certificate
            signer_id     Signer ID to be set in the certificate
        """

        if key:
            self.signer_csr.key.set_private_key(key)

        if re.search("^[0-9A-F]{4}$", signer_id) is None:
            raise ValueError("signer_id={} must be 4 uppercase hex digits".format(signer_id))

        self.signer_csr.builder = x509.CertificateSigningRequestBuilder()
        self.signer_csr.builder = self.signer_csr.builder.subject_name(
            x509.Name(
                [
                    x509.NameAttribute(x509.oid.NameOID.ORGANIZATION_NAME, org_name),
                    x509.NameAttribute(x509.oid.NameOID.COMMON_NAME, common_name + signer_id),
                ]
            )
        )
        # Add extensions
        self.signer_csr.builder = add_signer_extensions(
            builder=self.signer_csr.builder, public_key=self.signer_csr.key.get_public_key()
        )

        self.signer_csr.sign_builder(self.signer_csr.key.private_key)

    def build_signer(self, key=None, validity=31, use_extended_date: bool = True):
        """
        Function to build the signer certificate

        Inputs:
            key           the private key used for generating the signer.
            validity      the validity to be set for the signer certificate.
        """

        if key:
            self.signer.key.set_private_key(key)
        else:
            self.signer.key.private_key = self.signer_csr.key.private_key

        if not self.root.certificate:
            raise ValueError("Root cert MUST be built/set before Signer")
        if not self.signer_csr.certificate:
            raise ValueError("Signer csr MUST be built/set before Signer")

        self.signer.builder = self.signer.builder.issuer_name(self.root.certificate.subject)
        self.signer.builder = self.signer.builder.not_valid_before(
            datetime.utcnow().replace(minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
        )
        # If validity is set to zero the code should fix the max possible
        # date and time under Generalized time format according to RFC5280
        if validity == 0:
            self.signer.builder = self.signer.builder.not_valid_after(
                datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
                format=TimeFormat.GENERALIZED_TIME,
            )
        else:
            self.signer.builder = self.signer.builder.not_valid_after(
                self.signer.builder._not_valid_before.replace(
                    year=self.signer.builder._not_valid_before.year + validity
                ),
                format=TimeFormat.GENERALIZED_TIME,
            )
        self.signer.builder = self.signer.builder.subject_name(self.signer_csr.certificate.subject)
        self.signer.builder = self.signer.builder.public_key(
            self.signer_csr.certificate.public_key()
        )
        self.signer.builder = self.signer.builder.serial_number(
            pubkey_cert_sn(16, self.signer.builder, use_extended_date)
        )
        self.signer.builder = add_signer_extensions(
            builder=self.signer.builder, authority_cert=self.root.certificate
        )

        self.signer.sign_builder(self.root.key.private_key)

    def build_device(
        self,
        device_sn=None,
        device_public_key=None,
        org_name="Microchip Technology Inc",
        validity=28,
        use_extended_date: bool = True
    ):
        """
        Function to build the device certificate

        Inputs:
            device_sn         the device serial number to be used for
                                certificate
            device_public_key the device public key to be used for certificate
            org_name          Organisation name to be set in the certificate
            validity          the validity to be set for the certificate.
        """

        if not self.signer.certificate:
            raise ValueError("Signer cert MUST be built/set before Device")

        device_sn = get_device_sn_number(device_sn)
        device_public_key = get_device_public_key(device_public_key)
        public_key = ec.EllipticCurvePublicNumbers(
            x=int(device_public_key[:64], 16),
            y=int(device_public_key[64:], 16),
            curve=ec.SECP256R1(),
        ).public_key(get_backend())

        self.device.builder = self.device.builder.issuer_name(self.signer.certificate.subject)
        self.device.builder = self.device.builder.not_valid_before(
            datetime.utcnow().replace(tzinfo=timezone.utc, minute=0, second=0)
        )
        # If validity is set to zero the code should fix the max possible
        # date and time under Generalized time format according to RFC5280
        if validity == 0:
            self.device.builder = self.device.builder.not_valid_after(
                datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
                format=TimeFormat.GENERALIZED_TIME,
            )
        else:
            self.device.builder = self.device.builder.not_valid_after(
                self.device.builder._not_valid_before.replace(
                    year=self.device.builder._not_valid_before.year + validity
                ),
                format=TimeFormat.GENERALIZED_TIME,
            )
        self.device.builder = self.device.builder.subject_name(
            x509.Name(
                [
                    x509.NameAttribute(x509.oid.NameOID.ORGANIZATION_NAME, org_name),
                    x509.NameAttribute(x509.oid.NameOID.COMMON_NAME, device_sn),
                ]
            )
        )
        self.device.builder = self.device.builder.public_key(public_key)
        # Device certificate is generated from certificate dates and public key
        self.device.builder = self.device.builder.serial_number(
            pubkey_cert_sn(16, self.device.builder, use_extended_date)
        )
        # Add in extensions
        self.device.builder = self.device.builder.add_extension(
            x509.BasicConstraints(ca=False, path_length=None), critical=True
        )
        self.device.builder = self.device.builder.add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=True,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        self.device.builder = self.device.builder.add_extension(
            x509.SubjectKeyIdentifier.from_public_key(public_key), critical=False
        )
        issuer_ski = self.signer.certificate.extensions.get_extension_for_class(
            x509.SubjectKeyIdentifier
        )
        self.device.builder = self.device.builder.add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(issuer_ski.value),
            critical=False,
        )

        self.device.sign_builder(self.signer.key.private_key)

    def set_tflex_certificates(self, root_cert=None, signer_cert=None, device_cert=None):
        """
        Sets TrustFLEX certificates to be processed
        """
        if root_cert:
            self.root.set_certificate(root_cert)

        if signer_cert:
            self.signer.set_certificate(signer_cert)

        if device_cert:
            self.device.set_certificate(device_cert)

    def is_certificate_chain_valid(self):
        """
        Function to verify the certificate chain
        and return the status of it.
        """
        return (
            self.root.is_signature_valid(self.root.key.get_public_key())
            and self.signer.is_signature_valid(self.root.key.get_public_key())
            and self.device.is_signature_valid(self.signer.key.get_public_key())
        )

    def get_tflex_py_definitions(self, signer_def_file="", device_def_file=""):
        py_def = dict()

        cert_def = CertDef(self.device_name)
        if signer_def_file and os.path.exists(signer_def_file):
            py_def.update({"signer": cert_def.get_py_definition(signer_def_file)})
        elif self.signer.certificate and self.root.certificate:
            cert_def.set_certificate(self.signer.certificate, self.root.certificate, 1)
            py_def.update({"signer": cert_def.get_py_definition()})
        else:
            raise ValueError("Neither Signer certificate set nor def file passed")

        cert_def = CertDef(self.device_name)
        if device_def_file and os.path.exists(device_def_file):
            py_def.update({"device": cert_def.get_py_definition(device_def_file)})
        elif self.device.certificate and self.signer.certificate:
            cert_def.set_certificate(self.device.certificate, self.signer.certificate, 3)
            py_def.update({"device": cert_def.get_py_definition()})
        else:
            raise ValueError("Neither Device certificate set nor def file passed")
        return py_def

    def get_signer_c_definition_string(self):
        cert_def = CertDef(self.device_name)
        if self.signer.certificate and self.root.certificate:
            cert_def.set_certificate(self.signer.certificate, self.root.certificate, 1)
            return cert_def.get_c_definition(False)
        else:
            raise ValueError("Signer and Root should be set first")

    def get_device_c_definition_string(self):
        cert_def = CertDef(self.device_name)
        if self.device.certificate and self.signer.certificate:
            cert_def.set_certificate(self.device.certificate, self.signer.certificate, 3)
            return cert_def.get_c_definition(False)
        else:
            raise ValueError("Device and Signer should be set first")

    def save_tflex_c_definitions(self):
        cert_def = CertDef(self.device_name)
        if self.signer.certificate and self.root.certificate:
            cert_def.set_certificate(self.signer.certificate, self.root.certificate, 1)
            cert_def.get_c_definition(True)
        else:
            raise ValueError("Signer and Root should be set first")

        cert_def = CertDef(self.device_name)
        if self.device.certificate and self.signer.certificate:
            cert_def.set_certificate(self.device.certificate, self.signer.certificate, 3)
            cert_def.get_c_definition(True)
        else:
            raise ValueError("Device and Signer should be set first")

    def save_tflex_py_definitions(self, signer_def_file="", device_def_file=""):
        if signer_def_file:
            cert_def = CertDef(self.device_name)
            if self.signer.certificate and self.root.certificate:
                cert_def.set_certificate(self.signer.certificate, self.root.certificate, 1)
                cert_def.get_py_definition(dest_def_file=signer_def_file)
            else:
                raise ValueError("Signer and Root should be set first")

        if device_def_file:
            cert_def = CertDef(self.device_name)
            if self.device.certificate and self.signer.certificate:
                cert_def.set_certificate(self.device.certificate, self.signer.certificate, 3)
                cert_def.get_py_definition(dest_def_file=device_def_file)
            else:
                raise ValueError("Device and Signer should be set first")


__all__ = ["TFLEXCerts"]
