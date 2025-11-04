import os
import json
from pathlib import Path
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.primitives import hashes, hmac
from tpds.certs import Cert
import cryptoauthlib as cal
from tpds.proto_provision.ecc204_provision import ECC204Provision
from tpds.proto_provision.ta010_provision import TA010Provision
from tpds.tp_utils.tp_settings import TPSettings
from tpds.tp_utils.tp_utils import get_c_hex_bytes
from tpds.tp_utils.tp_keys import TPAsymmetricKey
from tpds.helper import log
import tpds.tp_utils.tp_input_dialog as tp_userinput
from wpc_pt_config.api.wpc_root import create_wpc_root_cert
from wpc_pt_config.api.wpc_mfg import create_wpc_mfg_cert
from wpc_pt_config.api.wpc_puc import create_wpc_puc_cert
from wpc_pt_config.api.certs_schema import WPCRootCertParams, WPCMfgCertParams
from .ecc204 import GenerateProvisioningPackage, AbortException


class ECC204TFLXWPCPackage(GenerateProvisioningPackage):
    """
    Generate Provisioning Package for ECC204 TFLXWPC
    """

    def __init__(self, config_string, device_name) -> None:
        try:
            super().__init__(config_string, device_name)
            self.process_xml()
            self.process_enc()
        except AbortException:
            self.response_msg = ""
            self.display_msg = "ABORT"
        except BaseException as e:
            if "EC key" in str(e):
                e = str(e).replace("EC key", "ECC key")
            self.display_msg = f"Provisioning Package process failed with:\n{e}"
        finally:
            self.cleanup()


def ecc204_tflxwpc_generate_fw_resources(fw_resource, base_folder, device_name):
    """
    Add inputs to Cryptoauth library
    """
    root_cert = fw_resource.get("root_cert")
    root_digest = fw_resource.get("root_digest")
    mfg_cert = fw_resource.get("mfg_cert")
    with open(os.path.join(base_folder, f"{device_name.lower()}.h"), "w") as f:
        f.write(f"#ifndef _{device_name}_DATA_H\n")
        f.write(f"#define _{device_name}_DATA_H\n\n")
        f.write("#ifdef __cplusplus\n")
        f.write('extern "C" {\n')
        f.write("#endif\n\n")
        f.write(f"""uint8_t root_cert[{len(root_cert)}] = \n""")
        f.write("{\n" + f"""{get_c_hex_bytes(root_cert)}""" + "};\n\n")
        f.write(f"""uint8_t root_digest[{len(root_digest)}] = \n""")
        f.write("{\n" + f"""{get_c_hex_bytes(root_digest)}""" + "};\n\n")
        f.write(f"""uint8_t mfg_cert[{len(mfg_cert)}] = \n""")
        f.write("{\n" + f"""{get_c_hex_bytes(mfg_cert)}""" + "};\n\n")
        f.write("#ifdef __cplusplus\n")
        f.write("}\n")
        f.write("#endif\n")
        f.write("#endif\n")


def ecc204_tflxwpc_proto_prov_handle(config_str, device_name):
    """
    Load config and data slots to ECC204 device
    Input:
        config_string
    Output:
        Configures config and data slots of ECC204 device
    """
    data = config_str
    if isinstance(config_str, str):
        data = json.loads(config_str)
    log(f"Data for Proto Provisioning: {data}")

    log(f"Provisioning {device_name}")
    display_msg = (
        "<font color=#0000ff>" "<b>Proto provisioning observations:</b></font><br/></br>"
    )
    response_msg = "Error"

    base_folder = os.path.join(TPSettings().get_base_folder(), "ecc204_wpc_proto_provision")
    os.makedirs(base_folder, exist_ok=True)

    # Generate certificates from User WPC parameters
    key_file = os.path.join(base_folder, "wpc_root.key")
    cert_file = os.path.join(base_folder, "wpc_root.crt")

    root_ca_key = TPAsymmetricKey(key_file if os.path.exists(key_file) else "")
    root_params = WPCRootCertParams(ca_key="")

    if os.path.exists(cert_file):
        cert = Cert()
        cert.set_certificate(cert_file)
        root_cert = cert.certificate
    else:
        root_cert = create_wpc_root_cert(
            root_ca_key.get_private_key(), root_params.root_cn, root_params.root_sn
        )
    root_ca_key.get_private_pem(key_file)
    Path(cert_file).write_text(
        root_cert.public_bytes(encoding=Encoding.PEM).decode("utf-8")
    )

    key_file = os.path.join(
        base_folder, f"""wpc_mfg_{data.get('ptmc')}-{data.get('ca_seq_id')}.key"""
    )
    cert_file = os.path.join(
        base_folder, f"""wpc_mfg_{data.get('ptmc')}-{data.get('ca_seq_id')}.crt"""
    )

    mfg_ca_key = TPAsymmetricKey(key_file if os.path.exists(key_file) else "")
    mfg_params = WPCMfgCertParams(ca_key="", ca_cert="")

    if os.path.exists(cert_file):
        cert = Cert()
        cert.set_certificate(cert_file)
        mfg_cert = cert.certificate
    else:
        mfg_cert = create_wpc_mfg_cert(
            int(data.get("ptmc"), 16),
            int(data.get("ca_seq_id"), 16),
            mfg_params.qi_policy,
            mfg_ca_key.get_public_key(),
            root_ca_key.get_private_key(),
            root_cert,
        )
    mfg_ca_key.get_private_pem(key_file)
    Path(cert_file).write_text(
        mfg_cert.public_bytes(encoding=Encoding.PEM).decode("utf-8")
    )

    try:
        log(f"Connecting {device_name} device...")
        is_device_connected = False
        user_device_address = int(data.get("device_address"), 16)
        device_prov = None

        for address in [0x33, 0x38, user_device_address]:
            try:
                if device_name == "TA010_TFLXWPC":
                    proto_provision = TA010Provision(
                        data.get("interface"), address << 1
                    )
                else:
                    proto_provision = ECC204Provision(
                        data.get("interface"), address << 1
                    )
                log(f"Device Connected with address 0x{address:02X}")
                is_device_connected = True
                break
            except BaseException as e:
                log(f"Failed to connect device with address 0x{address:02X}: {e}")

        if is_device_connected:
            msg_box_info = f"<font color=#0000ff>You are about to proto provision a blank {device_name} device. Changes cannot be reverted once provisioning is done. Do you want to continue?"
            device_prov = tp_userinput.TPMessageBox(
                title=f"{device_name} Blank device Provisioning", info=msg_box_info
            )
            if not proto_provision.element.is_config_zone_locked():
                device_prov.invoke_dialog()

                if device_prov.user_select != "Cancel":
                    configBytes = bytearray.fromhex(
                        """
                        8F F3 19 8B A3 3A E2 B2  58 00 01 00 00 00 00 00
                        0F 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00
                        00 00 00 00 FF FF FF FF  FF FF FF FF FF FF FF FF
                        38 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00
                        """
                    )

                    # set Serial Number
                    sn01 = data.get("sn01")
                    sn8 = data.get("sn8")
                    configBytes[0] = int(sn01[0:2], base=16)
                    configBytes[1] = int(sn01[2:4], base=16)
                    configBytes[8] = int(sn8, base=16)

                    # Set Counter
                    counter_bytes = proto_provision.int_to_binary_linear(
                        data.get("counter_value")
                    )
                    configBytes[32:48] = bytearray(counter_bytes)

                    # Set user device address to CSZ3 First Byte
                    configBytes[48] = user_device_address

                    # Set Limited Key Use
                    # set CSZ1 4th Byte 1-bit ON for  HMAC secret key to monotonic counter
                    if data.get("limited_key_use") == "HMAC":
                        configBytes[20] = configBytes[20] | 0x02

                    # set I/O levels to Fixed Reference
                    if data.get("fixed_reference"):  # set CSZ1 0th Byte 0-bit OFF
                        configBytes[16] = configBytes[16] & 0x0E

                    # write Config slot
                    proto_provision.element.load_tflx_test_config(
                        bytes(configBytes)
                    )
                else:
                    display_msg = f"{device_name} Proto provisioning aborted."
            else:
                log("Connected device is already configured and locked")
                msg_box_info = (
                    "<font color=#0000ff>Configuration Zone of the connected device is locked. <br />"
                    "Do you want to provision the Data Zone?"
                )
                device_prov = tp_userinput.TPMessageBox(
                    title="Device Provisioning", info=msg_box_info
                )
                device_prov.invoke_dialog()

            if device_prov.user_select != "Cancel":
                # read Counter
                counter_value = cal.AtcaReference(0)
                assert (
                    cal.atcab_counter_read(
                        0, counter_value) == cal.Status.ATCA_SUCCESS
                ), "atcab_counter_read has failed"
                log(f"Counter Value: {counter_value}")

                # read config zone
                ecc204_config = bytearray(64)
                assert (
                    cal.atcab_read_config_zone(
                        ecc204_config) == cal.Status.ATCA_SUCCESS
                ), "atcab_read_config_zone has failed"
                log(f"Config zone value: {ecc204_config.hex().upper()}")

                # read public key
                puc_pubkey = proto_provision.element.read_device_public_key(
                    0)
                device_sn = proto_provision.element.get_device_serial_number()

                key_file = os.path.join(
                    base_folder, f"wpc_puc_{device_name.lower()}_{device_sn.hex().upper()}.key"
                )
                cert_file = os.path.join(
                    base_folder, f"wpc_puc_{device_name.lower()}_{device_sn.hex().upper()}.crt"
                )

                puc_cert = create_wpc_puc_cert(
                    qi_id=int(data.get("qi_id")),
                    rsid=int.from_bytes(os.urandom(4), byteorder="big"),
                    public_key=puc_pubkey,
                    ca_private_key=mfg_ca_key.private_key,
                    ca_certificate=mfg_cert,
                )

                puc_key = TPAsymmetricKey()
                puc_key.set_public_key(puc_pubkey)
                puc_key.get_public_pem(key_file)
                Path(cert_file).write_text(
                    puc_cert.public_bytes(encoding=Encoding.PEM).decode("utf-8")
                )

                # Generate resources for firmware projects
                fw_resource = proto_provision.provision_wpc_slots(
                    root_cert, mfg_cert, puc_cert
                )
                ecc204_tflxwpc_generate_fw_resources(fw_resource, base_folder, device_name)

                # Storage for a secret key
                slot_info = data.get("slot_info")
                for slot in slot_info:
                    slot_id = int(slot.get("slot_id"))
                    if slot.get("key_load_config") not in ["cert", "no_load"] and slot.get("data"):
                        slot_data = bytes.fromhex(slot.get("data"))
                        if slot_id == 3 and data.get("diversified_key"):
                            sernum = bytes(device_sn)
                            slot_data = get_diversified_key(slot_data, sernum)
                        proto_provision.perform_slot_write(slot_id, slot_data)

                display_msg += (
                    f"""WPC Proto device provisioning is completed."""
                    """<br/>Proto Root, Mfg certs, keys and header files are stored at:"""
                    f"""<br/><a href='{base_folder}'>"""
                    f"""{base_folder}</a>"""
                )
                response_msg = "OK"
            else:
                response_msg = "Aborted"
                display_msg = "Device Protoprovisioning is aborted."
        else:
            display_msg = f"Unable to connect to {device_name} device, Please try with different device address"
    except BaseException as e:
        display_msg += f"\nPrototyping device failed with:{e}"

    finally:
        log(display_msg)
        if response_msg == "OK":
            msg_box = tp_userinput.TPMessageBox(
                title=f"{device_name} Configurator",
                info=(display_msg))
            msg_box.invoke_dialog()

    return {"response": response_msg, "status": display_msg}


def get_diversified_key(input_key: bytes, salt: bytes) -> bytes:
    h = hmac.HMAC(input_key, hashes.SHA256())
    h.update(salt)
    return h.finalize()
