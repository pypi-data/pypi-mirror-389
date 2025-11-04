# This file is governed by the terms outlined in the LICENSE file located in the root directory of
#  this repository. Please refer to the LICENSE file for comprehensive information.
import json
import logging
import traceback
from pathlib import Path
from argparse import ArgumentParser
from cryptography import x509
from .manifest.manifest import Manifest
from .generate_manifest_data import get_secure_element_data


def manifest_main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(levelname)s %(asctime)s] %(message)s",
        handlers=[logging.FileHandler("manifest.log"), logging.StreamHandler()],
    )

    parser = ArgumentParser(description="Decode or Generate secure element manifest")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Args for generating manifest
    generate_parser = subparsers.add_parser("generate", help="Generates Manifest for selected Secure Element")
    generate_parser.add_argument("--device", help="Select Device to generate Manifest", required=True)
    generate_parser.add_argument(
        "--interface",
        help="Select Interface of Device to generate Manifest",
        required=True,
    )
    generate_parser.add_argument("--address", help="Address of Device to generate Manifest", required=True)
    generate_parser.add_argument("--part_number", help="Part Number of Device to generate Manifest", required=True)
    generate_parser.add_argument("--ca_key", help="CA Private Key file path")
    generate_parser.add_argument("--ca_cert", help="CA Certificate file path")
    generate_parser.add_argument("--lite_manifest", action='store_true', help="Use this option to Generate Lite Manifet")

    # Args for decoding manifest
    decode_parser = subparsers.add_parser("decode", help="Decodes given Manifest using the given CA Certificate")
    decode_parser.add_argument(
        "--manifest",
        help="Manifest file path to process",
        required=True,
    )
    decode_parser.add_argument(
        "--cert",
        help="Verification certificate file path",
        required=True,
    )
    args = parser.parse_args()

    manifest = Manifest()
    if args.command == "decode":
        try:
            # Load manifest as JSON
            manifest_json = json.loads(Path(args.manifest).read_bytes())
            # Load verification certificate in PEM format
            verification_cert = x509.load_pem_x509_certificate(Path(args.cert).read_bytes())
            decoded = manifest.decode_manifest(manifest_json, verification_cert)
            logging.info(json.dumps(decoded, indent=4))
        except Exception as e:
            trace = traceback.format_exc()
            logging.debug(trace)
            logging.error(f"Manifest Decoding failed with error {e}")
    elif args.command == "generate":
        try:
            se = get_secure_element_data(
                device=args.device,
                interface=args.interface,
                address=args.address,
                is_lite_manifest=args.lite_manifest,
            )
            se.update({"PartNumber": args.part_number})
            sn = se.get("UniqueID")
            manifest.generate_manifest_json(se)
            manifest.encode_manifest(uniqueId=sn, ca_key_path=args.ca_key, ca_cert_path=args.ca_cert)
            manifest.write_signed_se_into_file(f"{args.device.upper()}_{sn}.json")
        except Exception as e:
            trace = traceback.format_exc()
            logging.debug(trace)
            logging.error(f"Manifest Generation Failed with error: \n{e}")
