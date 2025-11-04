import os
import json
import glob
import shutil
import cryptoauthlib as cal
from pathlib import Path
from zipfile import ZipFile
from cryptography.hazmat.primitives import serialization, hashes, hmac
from tpds.tp_utils.tp_utils import add_to_zip_archive
from tpds.certs.tflex_certs import TFLEXCerts
from tpds.tp_utils.tp_keys import TPAsymmetricKey
from tpds.proto_provision.ecc204_provision import ECC204Provision
from tpds.proto_provision.ta010_provision import TA010Provision
from tpds.helper import log
from tpds.tp_utils.tp_settings import TPSettings
import tpds.tp_utils.tp_input_dialog as tp_userinput
from tpds.certs.cert_utils import is_key_file_password_protected
from tpds.certs.sign_csr import SignCSR
import tpds.certs as tpds_certs
from .ecc204 import GenerateProvisioningPackage, AbortException


def ecc204_tflxauth_certs(
    cert_data, root_key=None, signer_key=None, device_sn=None, device_public_key=None
):
    if cert_data.get("cert_type") != "custCert":
        return None

    certs = TFLEXCerts(device_name="ECC204")
    certs.build_root(
        key=root_key,
        org_name=cert_data.get("signer_ca_org"),
        common_name=cert_data.get("signer_ca_cn"),
        validity=int(cert_data.get("s_cert_expiry_years")),
    )
    certs.build_signer_csr(
        key=signer_key,
        org_name=cert_data.get("s_cert_org"),
        common_name=cert_data.get("s_cert_cn"),
        signer_id="FFFF",
    )
    certs.build_signer(validity=int(cert_data.get("s_cert_expiry_years")))
    certs.build_device(
        device_sn=device_sn,
        device_public_key=device_public_key,
        org_name=cert_data.get("d_cert_org"),
        validity=int(cert_data.get("d_cert_expiry_years")),
    )
    # Verify new cert chain
    assert (
        certs.root.is_signature_valid(certs.root.certificate.public_key())
        and certs.signer.is_signature_valid(certs.root.certificate.public_key())
        and certs.device.is_signature_valid(certs.signer.certificate.public_key())
    ), "Certificate chain verification failed"
    certs.save_tflex_c_definitions()
    certs.save_tflex_py_definitions()
    certs_txt = "\n\n".join(
        [
            certs.root.get_certificate_in_text(),
            certs.signer.get_certificate_in_text(),
            certs.device.get_certificate_in_text(),
        ]
    )
    Path('certificates.txt').write_text(certs_txt)
    Path('root.crt').write_bytes(
        certs.root.get_certificate_in_pem())
    Path('signer.crt').write_bytes(
        certs.signer.get_certificate_in_pem())
    Path('device.crt').write_bytes(
        certs.device.get_certificate_in_pem())
    return certs


class ECC204TFLXAuthPackage(GenerateProvisioningPackage):
    """
    Generate Provisioning Package for ECC204 TFLXAuth
    """

    def __init__(self, config_string, device_name) -> None:
        try:
            super().__init__(config_string, device_name)
            self.process_xml()
            self.process_enc()
            self.process_csr()
        except AbortException:
            self.response_msg = ""
            self.display_msg = "ABORT"
        except BaseException as e:
            if "EC key" in str(e):
                e = str(e).replace("EC key", "ECC key")
            self.display_msg = f"Provisioning Package process failed with:\n{e}"
        finally:
            self.cleanup()

    def process_csr(self):
        log("Processing CSRs")
        ca_key = csr_zip = sign_csr_zip = signed_crt_zip = None
        if self.xml_type == "prod_xml" and self.cert_type == "custCert":
            log("CustomPKI and Production XML is selected by user")
            csr_zip = self.csr_zip_file
            ca_key = self.ca_key_file
            if (ca_key and os.path.exists(ca_key) and csr_zip and os.path.exists(csr_zip)):
                log("Processing CSR signing request")
                ca_key_password = None
                if is_key_file_password_protected(ca_key):
                    log("Processing ca_key password")
                    tB = accept = None
                    if accept:
                        ca_key_password = tB.encode("utf-8")
                log("Reading CSRs zip file")
                with ZipFile(csr_zip) as zf:
                    for file_name in zf.namelist():
                        with open(file_name, "wb") as kf:
                            kf.write(zf.read(file_name))
                        obj = SignCSR(file_name)
                        obj.sign_csr("signer.crt", ca_key, ca_key_password)
                        os.remove(file_name)
                        file_name = Path(file_name).stem.replace("_CSR", "") + ".cer"
                        Path(file_name).write_bytes(
                            obj.signer_crt.public_bytes(
                                encoding=serialization.Encoding.DER
                            )
                        )
                    ca_cert_zip_list = glob.glob("*.cer")
                    signed_crt_zip = f"{self.device_name}_{self.time_stamp}_ca_cert.zip"
                    add_to_zip_archive(signed_crt_zip, ca_cert_zip_list)
                    for file in ca_cert_zip_list:
                        os.remove(file)
            else:
                log("Generating sign_CSR zip for offline processing")
                sign_csr_zip = f"{self.device_name}_{self.time_stamp}_sign_csr.zip"
                shutil.copy(os.path.join(os.path.dirname(tpds_certs.__file__), "sign_csr.zip"), sign_csr_zip)
                z = ZipFile(sign_csr_zip, "a")
                z.write("signer.crt")
                z.close()
        else:
            log("No CSR processing for non CustomPKI-ProdXML")

        if sign_csr_zip:
            path_link = os.path.join(self.provisioning_zip_dir, sign_csr_zip).replace(
                "\\", "/"
            )
            self.display_msg += (
                f"""Scripts to Sign CSRs: <a href='{path_link}'>"""
                f"""{path_link}</a>"""
            )
        elif signed_crt_zip:
            path_link = os.path.join(self.provisioning_zip_dir, signed_crt_zip).replace(
                "\\", "/"
            )
            self.display_msg += (
                f"""Signed Certs: <a href='{path_link}'>""" f"""{path_link}</a>"""
            )


def ecc204_tflxauth_proto_prov_handle(config_str, device_name):
    data = config_str
    if isinstance(config_str, str):
        data = json.loads(config_str)
    log(f"Data for Proto Provisioning: {data}")

    log(f"Provisioning {device_name}")
    response_msg = "Error"
    display_msg = (
        "<font color=#0000ff>\n<b>Proto provisioning observations:</b></font>\n\n"
    )
    curr_dir = os.getcwd()
    base_folder = os.path.join(TPSettings().get_base_folder(), f"{device_name}_proto_provision".lower())
    os.makedirs(base_folder, exist_ok=True)
    os.chdir(base_folder)
    try:
        log(f"Connecting {device_name} device...")
        user_device_address = int(data.get("device_address"), 16)
        is_device_connected = False
        device_prov = None

        for address in [0x33, 0x39, user_device_address]:
            try:
                if device_name == "TA010_TFLXAUTH":
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
            msg_box_info = (
                f"<font color=#0000ff>You are about to proto provision a blank {device_name} device."
                "Changes cannot be reverted once provisioning is done. Do you want to continue?"
            )
            device_prov = tp_userinput.TPMessageBox(
                title=f"{device_name} Blank device Provisioning", info=msg_box_info
            )
            if not proto_provision.element.is_config_zone_locked():
                device_prov.invoke_dialog()
                if device_prov.user_select != "Cancel":
                    configBytes = bytearray.fromhex(
                        """
                                                    01 23 19 8B A3 3A E2 B2  01 5A 01 00 00 00 00 00
                                                    0F 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00
                                                    00 00 00 00 FF FF FF FF  FF FF FF FF FF FF FF FF
                                                    39 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00"""
                    )
                    # CSZ0
                    # set device interface
                    configBytes[10] = 0x00 if (data.get("interface") == "swi") else 0x01

                    # set Serial Number
                    sn01 = data.get("sn01")
                    sn8 = data.get("sn8")
                    configBytes[0] = int(sn01[0:2], base=16)
                    configBytes[1] = int(sn01[2:4], base=16)
                    configBytes[8] = int(sn8, base=16)

                    # CSZ1
                    # set Chip mode - Health Test Auto Clear
                    if data.get("health_test"):
                        configBytes[16] |= 1 << 3  # set 1 to 3-bit
                    else:
                        configBytes[16] &= ~(1 << 3)  # set 0 to 3-bit

                    # Set Chip mode - I/O levels to fixed reference
                    if data.get("fixed_reference"):
                        configBytes[16] = configBytes[16] & 0x0E

                    # Set ECC private key to monotonic counter
                    if data.get("limited_key_use") == "private":
                        configBytes[17] |= 0x01

                    # Set HMAC secret key to monotonic counter
                    if data.get("limited_key_use") == "secret":
                        configBytes[20] |= 0x02

                    # set Encrypt write enable/disable option
                    if data.get("encrypt_write"):
                        configBytes[20] |= 0x01  # set 1 to 0-bit
                    else:
                        configBytes[20] &= ~0x01  # set 0 to 0-bit

                    # CSZ2
                    # Set Counter Value
                    counterBytes = proto_provision.int_to_binary_linear(
                        data.get("counter_value")
                    )
                    log(f"Counter Data:{bytearray(counterBytes).hex().upper()}")
                    configBytes[32:48] = bytearray(counterBytes)

                    # CSZ3
                    # Set user device address to CSZ3 First Byte
                    configBytes[48] = user_device_address

                    # set compliance mode
                    configBytes[49] = 0x01 if (data.get("compliance")) else 0x00

                    # provision ECC204 config zone
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
                # read counter
                counter_value = cal.AtcaReference(0)
                assert cal.atcab_counter_read(0, counter_value) == cal.Status.ATCA_SUCCESS, "atcab_counter_read has failed"
                log(f"Counter value: {counter_value}")

                # read config zone
                ecc204_config = bytearray(64)
                assert cal.atcab_read_config_zone(ecc204_config) == cal.Status.ATCA_SUCCESS, "atcab_read_config_zone has failed"
                log(f"Config Data: {ecc204_config.hex().upper()}")

                # read Serial Number
                device_sn = bytearray()
                assert cal.atcab_read_serial_number(device_sn) == cal.Status.ATCA_SUCCESS, "Reading Serial number failed"

                # read public key
                device_public_key = bytearray()
                assert cal.atcab_get_pubkey(0, device_public_key) == cal.Status.ATCA_SUCCESS, "Reading Public Key failed"

                signer_ca_key = "root.key"
                device_ca_key = "signer.key"
                certs = None
                cert_data = data.get("slot_info")[1]
                if cert_data.get("cert_type") == "custCert":
                    if not os.path.exists(signer_ca_key):
                        key = TPAsymmetricKey()
                        key.get_private_pem(signer_ca_key)

                    if not os.path.exists(device_ca_key):
                        key = TPAsymmetricKey()
                        key.get_private_pem(device_ca_key)

                    log("Generating custom certificates for device")
                    if cert_data.get("d_cert_cn") != "sn0123030405060708EE":
                        device_sn = cert_data.get("d_cert_cn")
                    certs = ecc204_tflxauth_certs(
                        cert_data,
                        root_key=signer_ca_key,
                        signer_key=device_ca_key,
                        device_sn=device_sn,
                        device_public_key=device_public_key,
                    )

                slot_info = data.get("slot_info")
                for slot in slot_info:
                    slot_msg = ""
                    slot_id = int(slot.get("slot_id"))
                    if slot.get("key_load_config") not in ["cert", "no_load"] and slot.get("data"):
                        slot_data = bytes.fromhex(slot.get("data"))
                        if slot_id == 3 and data.get("diversified_key"):
                            sernum = bytes(device_sn)
                            slot_data = get_diversified_key(slot_data, sernum)

                        proto_provision.perform_slot_write(slot_id, slot_data)
                        slot_msg = "User data loaded."
                    elif certs and slot.get("key_load_config") == "cert":
                        proto_provision.provision_cert_slot(
                            certs.root.certificate,
                            certs.signer.certificate,
                            certs.device.certificate,
                        )
                        slot_msg = "Certs data loaded."
                    else:
                        slot_msg = (
                            "Pregenerated." if int(slot.get("slot_id")) == 0 else "Skipped."
                        )
                    display_msg += f"<br/>Slot{int(slot.get('slot_id'))} ({slot.get('slot_type')}): {slot_msg}"
                display_msg += "<br/>Prototype board provisioning completed!"
                response_msg = "OK"
            else:
                response_msg = "Aborted"
                display_msg = "Device Protoprovisioning is aborted."
        else:
            display_msg = f"Unable to connect to {device_name} device, Check device address and connections before retrying"
    except BaseException as e:
        display_msg += f"\nPrototyping device failed with:{e}"

    finally:
        os.chdir(curr_dir)
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


if __name__ == "__main__":
    pass
