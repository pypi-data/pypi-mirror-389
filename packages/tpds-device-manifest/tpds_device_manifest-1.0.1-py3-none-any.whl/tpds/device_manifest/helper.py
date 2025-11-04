# This file is governed by the terms outlined in the LICENSE file located in the root directory of
#  this repository. Please refer to the LICENSE file for comprehensive information.
from enum import Enum
from jose.utils import base64url_encode
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import ec, rsa, ed25519, x25519
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.types import PUBLIC_KEY_TYPES
from cryptography.hazmat.primitives.serialization import Encoding
from tpds.cert_tools.cert import Cert


def b64(x):
    return base64url_encode(x).decode('ascii')


def jws_b64encode(source):
    """Simple helper function to remove base64 padding"""
    return base64url_encode(source).decode("ascii").rstrip("=")


class KeyAlgorithms(str, Enum):
    """Key Algorithms supported by the Secure Elements
    """
    ECC_P224 = "ECC_P224"
    ECC_P256 = "ECC_P256"
    ECC_P384 = "ECC_P384"
    ECC_P521 = "ECC_P521"
    RSA_1024 = "RSA_1024"
    RSA_2048 = "RSA_2048"
    RSA_3072 = "RSA_3072"
    RSA_4096 = "RSA_4096"
    HMAC_SHA256 = "HMAC_SHA256"
    ECC_SECP256_K1 = "ECC_SECP256K1"
    ECC_BRAINPOOL_P256_R1 = "ECC_Brainpool_P256R1"
    AES128 = "AES128"
    AES256 = "AES256"
    ED25519 = "Ed25519"
    X25519 = "X25519"


def get_public_key_from_numbers(key_type: KeyAlgorithms, pub_num: bytes) -> PUBLIC_KEY_TYPES:
    """
    Generates a public key object from the given key type and public numbers.

    Args:
        key_type (str): The type of the key. Supported values are 'ECCP521', 'ECCP384', 'ECCP256', 'ED25519',
            'RSA4096', 'RSA3072', and 'RSA2048'.
        pub_num (bytes): The public numbers in bytes format.

    Returns:
        PUBLIC_KEY_TYPES: The generated public key object corresponding to the provided key type and public numbers.

    Raises:
        ValueError: If the key_type is not supported.
    """
    if key_type.startswith('ECC'):
        curve_map = {
            KeyAlgorithms.ECC_P224: ec.SECP224R1(),
            KeyAlgorithms.ECC_P256: ec.SECP256R1(),
            KeyAlgorithms.ECC_SECP256_K1: ec.SECP256K1(),
            KeyAlgorithms.ECC_BRAINPOOL_P256_R1: ec.BrainpoolP256R1(),
            KeyAlgorithms.ECC_P384: ec.SECP384R1(),
            KeyAlgorithms.ECC_P521: ec.SECP521R1(),
        }
        if not (curve := curve_map.get(key_type)):
            raise ValueError(f"Unsupported ECC key type: {key_type}")
        split_size = len(pub_num) // 2
        x = int.from_bytes(pub_num[:split_size], 'big')
        y = int.from_bytes(pub_num[split_size:], 'big')
        public_key = ec.EllipticCurvePublicNumbers(x, y, curve).public_key()
    elif key_type in [KeyAlgorithms.RSA_1024, KeyAlgorithms.RSA_2048, KeyAlgorithms.RSA_3072, KeyAlgorithms.RSA_4096]:
        n = int.from_bytes(pub_num, 'big')
        public_key = rsa.RSAPublicNumbers(e=65537, n=n).public_key()
    elif key_type == KeyAlgorithms.ED25519:
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_num)
    elif key_type == KeyAlgorithms.X25519:
        public_key = x25519.X25519PublicKey.from_public_bytes(pub_num)
    else:
        raise ValueError(f"Unsupported key type: {key_type}")
    return public_key


def get_public_der(public_key: PUBLIC_KEY_TYPES):
    """
    Convert a public key to PEM format.

    This function takes a public key object and converts it to a PEM-formatted string.

    Args:
        public_key (PUBLIC_KEY_TYPES): The public key object to be converted to PEM format.

    Returns:
        str: The PEM-formatted string representation of the public key.
    """
    public_pem = public_key.public_bytes(
        Encoding.DER, format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return public_pem


def is_certificate_chain_valid(
        root_cert: x509.Certificate,
        signer_cert: x509.Certificate,
        device_cert: x509.Certificate):
    """
    Validate a certificate chain consisting of a root certificate, a signer certificate, and a device certificate.

    Args:
        root_cert (x509.Certificate): The root certificate in the chain.
        signer_cert (x509.Certificate): The signer certificate, issued by the root certificate.
        device_cert (x509.Certificate): The device certificate, issued by the signer certificate.

    Returns:
        bool: True if the certificate chain is valid, i.e., all signatures are verified successfully;
              False otherwise.
    """
    root = Cert()
    root.set_certificate(root_cert)

    signer = Cert()
    signer.set_certificate(signer_cert)

    device = Cert()
    device.set_certificate(device_cert)

    return (
        root.is_signature_valid(root_cert.public_key())
        and signer.is_signature_valid(root_cert.public_key())
        and device.is_signature_valid(signer_cert.public_key())
    )
