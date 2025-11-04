# 2018 to present - Copyright Microchip Technology Inc. and its subsidiaries.
#
# Subject to your compliance with these terms, you may use Microchip software
# and any derivatives exclusively with Microchip products. It is your
# responsibility to comply with third party license terms applicable to your
# use of third party software (including open source software) that may
# accompany Microchip software.
#
# THIS SOFTWARE IS SUPPLIED BY MICROCHIP "AS IS".  NO WARRANTIES, WHETHER
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
from pathlib import Path

from asn1crypto import pem
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.hashes import HashAlgorithm
from cryptography.hazmat.primitives.asymmetric import ec, rsa, ed25519
from cryptography.hazmat.primitives.asymmetric.padding import AsymmetricPadding
from cryptography.hazmat.primitives.serialization import Encoding
from OpenSSL import crypto

from .ext_builder import ExtBuilder
from .timefix_backend import backend

_backend = None


class Cert:
    """
    Class with methods for the certificate
    """

    def __init__(self):
        self.builder = ExtBuilder()

    def sign_builder(
        self,
        private_key,
        hash_algo: HashAlgorithm = hashes.SHA256()
    ):
        """
        Signs the builder using Private key and adds to certificate

        Inputs:
        private_key       the private key used to sign the certificate
        hash_algo         the hash algorithm to be used. Defaults to SHA-256
        """
        if not isinstance(
            private_key, (ec.EllipticCurvePrivateKey, rsa.RSAPrivateKey, ed25519.Ed25519PrivateKey)
        ):
            raise ValueError("Invalid private key received")

        if isinstance(private_key, ed25519.Ed25519PrivateKey):
            hash_algo = None

        self.certificate = self.builder.sign(
            private_key=private_key, algorithm=hash_algo, backend=self.__get_backend()
        )

    def set_certificate(self, cert):
        """
        Loads the certificate into class for processing

        Args:
            cert: certificate to set, can be x509 cert instance or path to cert or cert in str or cert bytes
        """
        self.certificate = None
        if isinstance(cert, x509.Certificate):
            self.certificate = cert
        elif cert and os.path.exists(cert):
            cert_data = Path(cert).read_bytes()
            self.load_cert(cert_data)
        elif cert and isinstance(cert, str):
            cert_data = cert.encode("utf-8")
            self.load_cert(cert_data)
        elif cert and isinstance(cert, bytes):
            self.load_cert(cert)

        if self.certificate is None:
            raise ValueError("found unknown format in {}".format(cert))

    def load_cert(self, cert_data: bytes):
        if pem.detect(cert_data):
            self.certificate = x509.load_pem_x509_certificate(cert_data, self.__get_backend())
        else:
            self.certificate = x509.load_der_x509_certificate(cert_data, self.__get_backend())

    def get_certificate_in_pem(self):
        """
        Returns the certificate in the PEM format
        """
        return self.certificate.public_bytes(encoding=Encoding.PEM)

    def get_certificate_in_der(self):
        """
        Returns the certificate in the Der format
        """
        return self.certificate.public_bytes(encoding=Encoding.DER)

    def get_certificate_in_text(self):
        """
        Return string contains certificate TEXT format
        """
        # collect certificate text
        cert_object = crypto.load_certificate(
            crypto.FILETYPE_PEM, self.certificate.public_bytes(encoding=Encoding.PEM)
        )
        cert_content = crypto.dump_certificate(crypto.FILETYPE_TEXT, cert_object)

        return cert_content.decode("utf-8")

    def is_signature_valid(self, public_key, rsa_padding: AsymmetricPadding = None):
        """
        Verifies the certificate with the public key

        Inputs:
            public_key       the public used to verify the certificate
        Outputs:
            True/False       The status of the verify operation
        """
        if not isinstance(
            public_key, (ec.EllipticCurvePublicKey, rsa.RSAPublicKey, ed25519.Ed25519PublicKey)
        ):
            raise ValueError("Invalid public key received")

        try:
            if isinstance(public_key, ec.EllipticCurvePublicKey):
                public_key.verify(
                    signature=self.certificate.signature,
                    data=self.certificate.tbs_certificate_bytes,
                    signature_algorithm=ec.ECDSA(self.certificate.signature_hash_algorithm),
                )
            elif isinstance(public_key, rsa.RSAPublicKey):
                public_key.verify(
                    signature=self.certificate.signature,
                    data=self.certificate.tbs_certificate_bytes,
                    padding=rsa_padding,
                    algorithm=self.certificate.signature_hash_algorithm
                )
            else:
                public_key.verify(
                    signature=self.certificate.signature,
                    data=self.certificate.tbs_certificate_bytes,
                )
            return True

        except Exception as e:
            print(e)
            return False

    def __get_backend(self):
        global _backend
        if not _backend:
            _backend = backend
        return _backend


# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == "__main__":
    pass
