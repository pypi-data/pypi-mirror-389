# This file is governed by the terms outlined in the LICENSE file located in the root directory of
#  this repository. Please refer to the LICENSE file for comprehensive information.

import os
import copy
import logging
import json
import jose.jws
from jose.utils import base64url_decode, long_to_bytes
from datetime import datetime, timezone
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, ed448, x25519, x448, rsa, types
from cryptography.hazmat.primitives.asymmetric import utils as crypto_utils
from cryptography.utils import int_to_bytes
from tpds.cert_tools.cert_utils import random_cert_sn
from ..helper import b64, jws_b64encode


# List out allowed verification algorithms for the JWS. Only allows
# public-key based ones.
verification_algorithms = [
    'RS256', 'RS384', 'RS512', 'ES256', 'ES384', 'ES512'
]
# EC Curve mapping
ecc_curve_map = {
    "secp224r1": "P-224",
    "secp256r1": "P-256",
    "secp384r1": "P-384",
    "secp521r1": "P-521",
    "secp256k1": "secp256k1",
    "brainpoolp256r1": "brainpoolP256r1",
    "brainpoolp384r1": "brainpoolP384r1",
    "brainpoolp512r1": "brainpoolP512r1",
}
# OKP (Octet Key Pair) types
okp_types = [
    (ed25519.Ed25519PublicKey, 'Ed25519'),
    (ed448.Ed448PublicKey, 'Ed448'),
    (x25519.X25519PublicKey, 'X25519'),
    (x448.X448PublicKey, 'X448'),
]


class Manifest:
    def __init__(self):
        self.json_manifest_data = {}
        self.signed_se = {}

        self.device_entry_template: dict = {
            'version': 2,  # Lite Manifest until it's updated later
            'model': 'Unknown',  # Default until it's updated later
            'partNumber': 'Unknown',  # Default until it's updated later
            'manufacturer': {
                'organizationName': 'Microchip Technology Inc',
                'organizationalUnitName': 'Secure Computing Group'
            },
            'provisioner': {
                'organizationName': 'Microchip Technology Inc',
                'organizationalUnitName': 'Secure Computing Group'
            },
            'distributor': {
                'organizationName': 'Microchip Technology Inc',
                'organizationalUnitName': 'Microchip Direct'
            },
            'provisioningTimestamp': 'Unknown',
            'uniqueId': 'Unknown'
        }

    def generate_manifest_json(self, device_data: dict) -> dict:
        """Generates the Full/Lite manifest file JSON-encoded device data.

        :param manifest_device_data:  The manifest device data (list of dict)
                                    Dict data in each list item:
                                        'UniqueID' (str)              - The device serial number (lowercase)
                                        'provisioningTimestamp' (datetime)      - The device test time (UTC)
                                        'PartModel' (str)             - The device part model (uppercase) (e.g. 'ATECC608C')
                                        'PartNumber' (str)            - The device part number (uppercase)
                                        'Keys' (list of dict)         - The device public keys
                                            'KeyData' (bytes)                - DER-encoded SubjectPublicKeyInfo key data
                                            'KeyLocation' (str)              - The device key location (e.g. device slot)
                                        'Certificates' (list of dict) - The device certificates
                                            'KeyLocation' (str)              - The certificate key location (e.g. device slot)
                                            'CertificatesData' (list)  - The List of DER-encoded certificates

        :rtype: dict
        :return: The manifest file JSON-encoded device data.
        """
        device_entry = copy.deepcopy(self.device_entry_template)

        device_entry.update(
            {
                # Update the device part model
                "model": device_data.get("PartModel"),
                # Update the device unique ID (serial number)
                "partNumber": device_data.get("PartNumber"),
                # Update the device provisioning test time (UTC)
                "provisioningTimestamp": device_data.get("provisioningTimestamp").strftime(
                    "%Y-%m-%dT%H:%M:%S.%f"
                )[:-3]
                + "Z",
                # Update the device unique ID (serial number)
                "uniqueId": device_data.get("UniqueID"),
            }
        )
        if groupId := device_data.get("groupId", None):
            # Update the deviec groupId
            device_entry.update({"groupId": groupId})

        if keys := device_data.get("Keys", []):
            # Update JSON version to Full Manifest Version
            device_entry.update({"version": 3})

        device_keys = []
        # Add the device public keys to the device entry
        for key_data in keys:
            key_entry = self.update_manifest_key(key_data)
            # Add the certificate information to the device key information
            for certificate_data in device_data.get("Certificates", []):
                # Add the certificates to the key with the same location
                if key_data.get("KeyLocation") == certificate_data.get("KeyLocation"):
                    certificates = []
                    for cert in certificate_data.get("CertificatesData", []):
                        certificates.append(b64(cert))
                    key_entry.update({'x5c': certificates})

            # Append the key data to the device key information
            device_keys.append(key_entry)

            # Add the device key data to the device data
            if len(device_keys) > 0:
                device_entry.update({'publicKeySet': {'keys': device_keys}})
        self.json_manifest_data = copy.deepcopy(device_entry)

        # Return the JSON encoded manifest data
        return self.json_manifest_data

    def update_manifest_key(self, key_data):
        # Get the device public key from the key data
        public_key: types.PublicKeyTypes = serialization.load_der_public_key(
            data=key_data.get("KeyData"), backend=default_backend()
        )

        if isinstance(public_key, ec.EllipticCurvePublicKey):
            key_entry = {}
            # Set the EC manifest device public key data
            key_entry.update({
                'kid': key_data.get("KeyLocation"),
                'kty': 'EC'  # Key type is elliptic curve
            })

            # Set the EC curve
            assert (crv := ecc_curve_map.get(public_key.curve.name.lower(), None)), (
                'Unable to generate the manifest file. The EC public key uses an '
                f'unsupported curve (EC curve name = {public_key.curve.name}).'
            )
            key_entry.update({'crv': crv})

            # Set the EC public key x/y components
            key_entry.update({
                'x': b64(long_to_bytes(public_key.public_numbers().x)),
                'y': b64(long_to_bytes(public_key.public_numbers().y))
            })
            return key_entry

        # Set OKP (Octet Key Pair) types
        for key_cls, crv in okp_types:
            if isinstance(public_key, key_cls):
                return {
                    "kid": key_data.get("KeyLocation"),
                    "kty": "OKP",
                    "crv": crv,
                    "x": b64(
                        public_key.public_bytes(
                            serialization.Encoding.Raw, serialization.PublicFormat.Raw
                        )
                    ),
                }

        # Set RSA Public Key
        if isinstance(public_key, rsa.RSAPublicKey):
            numbers = public_key.public_numbers()
            return {
                'kid': key_data.get("KeyLocation"),
                'kty': 'RSA',
                'n': b64(long_to_bytes(numbers.n)),
                'e': b64(long_to_bytes(numbers.e))
            }

        raise ValueError(
            'Unable to generate the manifest file. The public key is not a supported '
            f'key type (public key type = {type(public_key)}).'
        )

    @staticmethod
    def decode_manifest(manifest, verification_cert: x509.Certificate) -> list:
        decoded_manifests = []
        # Convert verification certificate public key to PEM format
        verification_public_key_pem = verification_cert.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode(encoding='ascii')

        # Get the base64url encoded subject key identifier for the verification cert
        ski_ext = verification_cert.extensions.get_extension_for_class(
            extclass=x509.SubjectKeyIdentifier
        )
        verification_cert_kid_b64 = b64(
            ski_ext.value.digest
        )

        # Get the base64url encoded sha-256 thumbprint for the verification cert
        verification_cert_x5t_s256_b64 = b64(
            verification_cert.fingerprint(hashes.SHA256())
        )

        # Process all the entries in the manifest
        for _, signed_se in enumerate(manifest):
            # Decode the protected header
            protected = json.loads(base64url_decode(signed_se["protected"].encode("ascii")))

            if protected['kid'] != verification_cert_kid_b64:
                raise ValueError('kid does not match certificate value')
            if protected['x5t#S256'] != verification_cert_x5t_s256_b64:
                raise ValueError('x5t#S256 does not match certificate value')

            # Convert JWS to compact form as required by python-jose
            jws_compact = ".".join(
                [signed_se["protected"], signed_se["payload"], signed_se["signature"]]
            )

            # Verify and decode the payload. If verification fails an exception will be raised.
            se_objects = jose.jws.verify(
                token=jws_compact,
                key=verification_public_key_pem,
                algorithms=verification_algorithms,
            )

            se = json.loads(se_objects)
            if se['uniqueId'] != signed_se['header']['uniqueId']:
                raise ValueError(
                    (
                        'uniqueId in header "{}" does not match version in' + ' payload "{}"'
                    ).format(
                        signed_se['header']['uniqueId'],
                        se['uniqueId']
                    )
                )
            decoded_manifests.append(se)
        return decoded_manifests

    def encode_manifest(self, uniqueId, ca_key_path=None, ca_cert_path=None):
        """
        Function generate secure signed element object which contains payload,
        protected, header and signature.

        Inputs:
              ca_key_path        log signer key path which sign the jws data
              ca_cert_path       log signer cert path which contains cert
                                 extension and cert fingerprint

        Outputs:
              signed_se          return encoded manifest which contains
                                 securesignedelement object
              ca_key_path        log signer key path which sign the jws data
              ca_cert_path       log signer cert path which contains cert
                                 extension and cert fingerprint
        """
        # Read ca key
        if ca_key_path is None:
            ca_cert_path = None

        ca_key_path, ca_key = self.__load_ca_key(ca_key_path)
        ca_cert_path, ca_cert = self.__load_ca_cert(ca_key, ca_cert_path)

        # Precompute the JWT header
        sse_protected_header = {
            "typ": "JWT",
            "alg": "ES256",
            "kid": jws_b64encode(
                ca_cert.extensions.get_extension_for_class(x509.SubjectKeyIdentifier).value.digest
            ),
            "x5t#S256": jws_b64encode(ca_cert.fingerprint(hashes.SHA256())),
        }

        self.signed_se = {
            "payload": jws_b64encode(json.dumps(self.json_manifest_data).encode("ascii")),
            "protected": jws_b64encode(json.dumps(sse_protected_header).encode("ascii")),
            "header": {"uniqueId": uniqueId},
        }

        # Sign sse object
        tbs = self.signed_se["protected"] + "." + self.signed_se["payload"]
        signature = ca_key.sign(tbs.encode("ascii"), ec.ECDSA(hashes.SHA256()))
        r_int, s_int = crypto_utils.decode_dss_signature(signature)
        self.signed_se["signature"] = jws_b64encode(
            int_to_bytes(r_int, 32) + int_to_bytes(s_int, 32)
        )

        return {"ca_key_path": ca_key_path, "ca_cert_path": ca_cert_path}

    def __load_ca_cert(self, ca_key, ca_cert_path):
        """
        Function load manifest certificate
        create a new manifest certificate if not passed
        Inputs:
              ca_cert_path       manifest signer cert path
        Outputs:
              ca_cert_path       manifest signer cert path
              ca_cert            contains manifest signer cert
        """
        defalut_cert_path = "manifest_ca.crt"
        if ca_cert_path:
            cert_data = Path(ca_cert_path).read_bytes()
            ca_cert = x509.load_pem_x509_certificate(cert_data, default_backend())
        elif os.path.exists(defalut_cert_path):
            ca_cert_path = defalut_cert_path
            cert_data = Path(ca_cert_path).read_bytes()
            ca_cert = x509.load_pem_x509_certificate(cert_data, default_backend())
        else:
            ca_cert_path = defalut_cert_path
            # Create root CA certificate
            builder = x509.CertificateBuilder()
            builder = builder.serial_number(random_cert_sn(16))

            name = x509.Name(
                [
                    x509.NameAttribute(
                        x509.NameOID.ORGANIZATION_NAME, self.json_manifest_data.get("provisioner").get("organizationName")
                    ),
                    x509.NameAttribute(
                        x509.NameOID.COMMON_NAME, self.json_manifest_data.get("provisioner").get("organizationName")
                    ),
                ]
            )
            valid_date = datetime.now(timezone.utc)

            builder = builder.issuer_name(name)
            builder = builder.not_valid_before(valid_date)
            builder = builder.not_valid_after(datetime(9999, 12, 31, 23, 59, 59))
            builder = builder.subject_name(name)
            builder = builder.public_key(ca_key.public_key())
            builder = builder.add_extension(
                x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()), critical=False
            )
            builder = builder.add_extension(
                x509.BasicConstraints(ca=True, path_length=None), critical=True
            )
            # Self-sign certificate
            ca_cert = builder.sign(
                private_key=ca_key, algorithm=hashes.SHA256(), backend=default_backend()
            )
            # Write CA certificate to file
            ca_cert_pem = ca_cert.public_bytes(encoding=serialization.Encoding.PEM)
            Path(ca_cert_path).write_bytes(ca_cert_pem)

        return ca_cert_path, ca_cert

    def __load_ca_key(self, ca_key_path):
        """
        Function create new ca key if given path is not found or load a key
        from existing path
        Inputs:
              ca_key_path       manifest signer key path which sign the
              secure element
        Outputs:
              ca_key            manifest signer key
              ca_key_path       manifest signer key path which sign the
                                secure element
        """
        defalut_key_path = "manifest_ca.key"

        if ca_key_path:
            ca_key = Path(ca_key_path).read_bytes()
            ca_key = serialization.load_pem_private_key(ca_key, None, default_backend())
        elif os.path.exists(defalut_key_path):
            ca_key_path = defalut_key_path
            ca_key = Path(ca_key_path).read_bytes()
            ca_key = serialization.load_pem_private_key(ca_key, None, default_backend())
        else:
            ca_key_path = defalut_key_path
            ca_key = ec.generate_private_key(
                curve=ec.SECP256R1(), backend=default_backend()
            )
            ca_key_pem = ca_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
            Path(ca_key_path).write_bytes(ca_key_pem)

        return ca_key_path, ca_key

    def write_signed_se_into_file(self, file):
        """
        Write signed manifest data (SecureSignedElement object) into given file

        Inputs:
                signed_se           contains SignedSecureElement Object
                file                path to JSON file to dump the SignedSecureElement object
        """
        file_manifest = json.dumps([self.signed_se], indent=2).encode("ascii")
        Path(file).write_bytes(file_manifest)
        logging.info(f"Manifest Saved in {os.path.abspath(file)}")
