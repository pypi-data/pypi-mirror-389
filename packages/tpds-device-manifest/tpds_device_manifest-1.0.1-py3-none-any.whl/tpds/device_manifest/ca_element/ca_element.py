# This file is governed by the terms outlined in the LICENSE file located in the root directory of
#  this repository. Please refer to the LICENSE file for comprehensive information.

import logging
import cryptoauthlib as cal
from datetime import datetime, timezone
from tpds.cert_tools.cert import Cert
from tpds.device_manifest.helper import get_public_key_from_numbers, get_public_der, is_certificate_chain_valid
from tpds.device_manifest.connect import Connect


class CAElement(Connect):
    def __init__(
        self,
        device: str = "ATECC608",
        interface: str = "I2C",
        address: str = "0x6C",
        is_lite_manifest: bool = False,
    ):
        super().__init__(devtype=cal.get_device_type_id(device), address=address, interface=interface)
        # To Build JSON for ATECC608 TFLX or TNG to build full Manifest
        self.is_ecc608_tflx_tng = "ATECC608" in device and int(address, 16) in [0x6C, 0x6A] and not is_lite_manifest
        self.data = {}
        self.device_cert = None

    def build_json(self) -> dict:
        self.set_uniqueid()
        self.update_part_model()
        if self.is_ecc608_tflx_tng:
            self.update_keys()
            self.update_certs()
        self.set_provisioning_time()
        return self.data

    def update_certs(self):
        try:
            self.get_certs_from_device()
            logging.info("MCHP Certs are available on the device!")
        except Exception as e:
            logging.info(f"Failed to read MCHP Certs from on the device with error {e}.")

    def update_part_model(self):
        revision = bytearray(4)
        status = cal.atcab_info(revision)
        assert cal.Status.ATCA_SUCCESS == status, f"Read Devices Revision Failed with satatus {status:02X}"
        self.data.update({"PartModel": cal.get_device_name(revision)})

    def set_uniqueid(self):
        ser_num = bytearray(9)
        status = cal.atcab_read_serial_number(ser_num)
        assert cal.Status.ATCA_SUCCESS == status, f"Reading Serial Number failed with status {status:02X}"
        ser_num_hex = ser_num.hex().upper()
        self.data.update({"UniqueID": ser_num_hex})

    def update_keys(self):
        keys = []
        for slot in range(5):
            try:
                public_key = bytearray()
                status = cal.atcab_get_pubkey(slot, public_key)
                assert cal.Status.ATCA_SUCCESS == status, \
                    f"Reading Pub key from slot {slot} failed with status {slot:02X}"
                key_data = get_public_der(get_public_key_from_numbers("ECC_P256", public_key))
                keys.append({"KeyLocation": str(slot), "KeyData": key_data})
            except Exception:
                continue
        self.data.update({"Keys": keys}) if len(keys) else None

    def get_certs_from_device(self):
        certs = []
        root = Cert()
        signer = Cert()
        device = Cert()

        # Helper to read cert and size
        def read_cert(size_func, read_func, cert_obj, cert_name):
            size_ref = cal.AtcaReference(0)
            status = size_func(size_ref)
            assert status == cal.Status.ATCA_SUCCESS, f"Read {cert_name} size failed with status {status:02X}"
            cert_der = bytearray(size_ref.value)
            status = read_func(cert_der, size_ref)
            assert status == cal.Status.ATCA_SUCCESS, f"Read {cert_name} failed with status {status:02X}"
            cert_obj.load_cert(bytes(cert_der))
            return cert_der

        read_cert(cal.tng_atcacert_root_cert_size, cal.tng_atcacert_root_cert, root, "Root Cert")
        signer_cert_der = read_cert(
            cal.tng_atcacert_max_signer_cert_size, cal.tng_atcacert_read_signer_cert, signer, "Signer Cert"
        )
        device_cert_der = read_cert(
            cal.tng_atcacert_max_device_cert_size, cal.tng_atcacert_read_device_cert, device, "Device Cert"
        )
        assert is_certificate_chain_valid(
            root.certificate, signer.certificate, device.certificate
        ), "Invalid Certificate Chain"

        certs.append({
            "KeyLocation": "0",
            "CertificatesData": [device_cert_der, signer_cert_der],
        })
        self.data.update({"Certificates": certs})
        self.device_cert = device.certificate

    def set_provisioning_time(self):
        if self.device_cert:
            provTime = self.device_cert.not_valid_before
        else:
            provTime = datetime.now(timezone.utc)
        self.data.update({"provisioningTimestamp": provTime})
