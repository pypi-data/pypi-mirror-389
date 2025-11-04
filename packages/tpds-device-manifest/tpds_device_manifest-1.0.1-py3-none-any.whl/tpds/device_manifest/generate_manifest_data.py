# This file is governed by the terms outlined in the LICENSE file located in the root directory of
#  this repository. Please refer to the LICENSE file for comprehensive information.
import os
import sys
import importlib
import yaml
import logging
import jsonschema
from pathlib import Path

supported_devices = {}


def get_secure_element_data(
    device: str = "ATECC608",
    interface: str = "I2C",
    address: str = "0x6C",
    is_lite_manifest: bool = False,
):
    """
    Returns the JSON manifest for the specified secure element device.
    For TAx devices, attempts to import and use the TAx NDA package.
    For other devices, uses the standard SecureElement class.
    """
    if device not in supported_devices:
        load_packages()
    se_class = supported_devices.get(device)
    assert se_class, (
        f"Manifest package for {device} is not available. "
        "Please contact MCHP for the tpds-device-manifest NDA package.")
    logging.info(f"Generating Manifet For {device}")
    return se_class(device, interface, address, is_lite_manifest).build_json()


def load_packages():
    preset_file_dir = os.path.dirname(os.path.abspath(__file__))
    for entry in os.scandir(preset_file_dir):
        if entry.is_dir():
            info_yaml_path = os.path.join(entry.path, 'info.yaml')
            init_py_path = os.path.join(entry.path, '__init__.py')
            if not (os.path.isfile(info_yaml_path) and os.path.isfile(init_py_path)):
                continue

            try:
                info = _validate(info_yaml_path)
            except Exception as e:
                print(f"Failed to load {info_yaml_path} with error : {e}")
                continue

            try:
                spec = importlib.util.spec_from_file_location(info.get("name"), init_py_path)
                module_inst = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module_inst
                spec.loader.exec_module(module_inst)
            except Exception as e:
                logging.info(f"Failed to load {info.get('name')} module with error: {e}")
                continue
            se_class = getattr(module_inst, info.get("class"))
            for device in info.get("devices", []):
                supported_devices.update({device: se_class})


def _validate(config: str | os.PathLike[str]):
    schema = os.path.join(os.path.dirname(__file__), "info_schema.yaml")
    schema = yaml.safe_load(Path(schema).read_text())

    info = yaml.safe_load(Path(config).read_text())
    jsonschema.validate(instance=info, schema=schema)
    return info
