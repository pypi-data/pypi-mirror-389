# -*- coding: utf-8 -*-
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

import os
import json
import asn1crypto
from pathlib import Path
import cryptoauthlib as cal
import cryptography
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec, utils
from cryptography.hazmat.primitives import hashes

from tpds.secure_element import ECC204, CAElement
from tpds.tp_utils.tp_print import print
import tpds.tp_utils.tp_input_dialog as tp_userinput
from tpds.tp_utils.tp_input_dialog import TPInputDialog
from tpds.tp_utils.tp_utils import get_c_hex_bytes, calculate_wpc_digests
from tpds.tp_utils.tp_keys import TPAsymmetricKey
from tpds.certs import Cert
from tpds.certs.cert_utils import get_cert_print_bytes, is_signature_valid
from tpds.certs.x509_find_elements import (
    public_key_location,
    signature_location,
    tbs_location,
)
from tpds.proto_provision.ecc204_provision import ECC204Provision

from wpc_pt.backend.api.certs_schema import WPCRootCertParams
from wpc_pt.backend.api.wpc_root import create_wpc_root_cert
from wpc_pt.backend.api.wpc_mfg import create_wpc_mfg_cert
from wpc_pt.backend.api.wpc_puc import create_wpc_puc_cert


class WpcAuthentication:
    def __init__(self, boards):
        self.boards = boards
        self.ptmc_code = ""
        self.qi_id = ""
        self.ca_seqid = ""
        self.root_key = None
        self.mfg_key = None
        self.root_crt = None
        self.mfg_crt = None
        self.puc_crt = None
        self.chain_digest = None

    def generate_resources(self, b=None):
        CAElement().connect_to_SE(self.boards)

        # Get user Inputs for Usecase options
        self.__get_user_input(b)

        # Generate Accessory_SE resources
        ecc204 = ECC204(interface="i2c", address=(0x38 << 1))
        print(
            f"\nPower Transmitter(PT - ECC204) details: {ecc204.get_device_details()}"
        )

        # Generate crypto asserts for Usecase
        pu_ser_num = ecc204.get_device_serial_number()
        pu_pubkey = ecc204.read_device_public_key(0)
        self.__generate_crypto_asserts(pu_ser_num, pu_pubkey, b)

    def read_certs_from_device(self, b=None):
        print("Read Product Unit Certificate...", canvas=b)
        slot_bytes = bytearray(320)
        status = cal.atcab_read_bytes_zone(0x02, 0x01, 0, slot_bytes, len(slot_bytes))
        assert (
            status == cal.Status.ATCA_SUCCESS
        ), f"Reading product unit certificate has failed with {status:02X}"

        cert_size = int.from_bytes(slot_bytes[2:4], "big") + 4
        assert cert_size <= len(
            slot_bytes
        ), f"Invalid cert size({cert_size}) is received"
        self.puc_crt = cryptography.x509.load_der_x509_certificate(
            bytes(slot_bytes[0:cert_size])
        )
        print(
            get_cert_print_bytes(
                self.puc_crt.public_bytes(encoding=serialization.Encoding.PEM)
            )
        )

    def verify_cert_chain(self, b=None):
        print("Select Root certificate...", end="", canvas=b)
        root_crt_input = tp_userinput.TPInputFileUpload(
            file_filter=["*.crt"],
            nav_dir=os.getcwd(),
            dialog_title="Upload WPC Root Cert",
        )
        root_crt_input.invoke_dialog()
        assert root_crt_input.file_selection, "Select valid root certificate"
        print(f"{root_crt_input.file_selection}", canvas=b)
        temp_crt = Cert()
        temp_crt.set_certificate(root_crt_input.file_selection)
        print(temp_crt.get_certificate_in_text())
        self.root_crt = temp_crt.certificate
        print("Verifying Root certificate against root public key...", end="", canvas=b)
        assert is_signature_valid(self.root_crt, self.root_crt.public_key()), "Failed"
        print("OK")
        print("Verifying Mfg certificate against root public key...", end="", canvas=b)
        assert is_signature_valid(self.mfg_crt, self.root_crt.public_key()), "Failed"
        print("OK")
        print(
            "Verifying Product Unit certificate against Mfg public key...",
            end="",
            canvas=b,
        )
        assert is_signature_valid(self.puc_crt, self.mfg_crt.public_key()), "Failed"
        print("OK")

    def read_wpc_chain_digest(self, b=None):
        print("Read WPC Chain digest...", end="", canvas=b)
        self.chain_digest = bytearray(32)
        status = cal.atcab_read_bytes_zone(
            0x02, 0x02, 0, self.chain_digest, len(self.chain_digest)
        )
        assert (
            status == cal.Status.ATCA_SUCCESS
        ), f"Reading has failed with {status:02X}"
        print(f"{self.chain_digest.hex().upper()}")
        print("OK", canvas=b)

    def verify_wpc_chain_digest(self, b=None):
        print("Verifying WPC chain digest...", end="", canvas=b)
        root_bytes = self.root_crt.public_bytes(encoding=serialization.Encoding.DER)
        mfg_bytes = self.mfg_crt.public_bytes(encoding=serialization.Encoding.DER)
        puc_bytes = self.puc_crt.public_bytes(encoding=serialization.Encoding.DER)
        wpc_digests = calculate_wpc_digests(root_bytes, mfg_bytes, puc_bytes)
        assert self.chain_digest == wpc_digests.get(
            "chain_digest"
        ), "Chain digest verification has failed"
        print("OK", canvas=b)

    def send_random_challenge_to_PT(self, b=None):
        print("Generate challenge...", end="", canvas=b)
        self.challenge = os.urandom(32)
        print(f"{self.challenge.hex().upper()}")

        print("Response from PT...", end="", canvas=b)
        sign_bytes = bytearray(64)
        status = cal.atcab_sign(0, self.challenge, sign_bytes)
        assert (
            status == cal.Status.ATCA_SUCCESS
        ), f"Sign operation has failed with {status:02X}"
        print(f"{sign_bytes.hex().upper()}")
        r = int.from_bytes(sign_bytes[0:32], byteorder="big", signed=False)
        s = int.from_bytes(sign_bytes[32:64], byteorder="big", signed=False)
        self.response = utils.encode_dss_signature(r, s)
        print("OK", canvas=b)

    def verify_PT_response(self, b=None):
        print("Verify response from PT...", end="", canvas=b)
        try:
            self.puc_crt.public_key().verify(
                self.response,
                self.challenge,
                ec.ECDSA(utils.Prehashed(hashes.SHA256())),
            )
            print("OK", canvas=b)
        except Exception as err:
            raise ValueError(err)

    def __generate_crypto_asserts(self, pu_ser_num, puc_pubkey, b=None):
        print("Generating crypto assets for Usecase...", canvas=b)
        wpc_root_crt_file = "wpc_root_cert.crt"
        wpc_root_key_file = "wpc_root_key.key"
        wpc_mfg_crt_file = f"wpc_mfg_{self.ptmc_code}-{self.ca_seqid}.crt"
        wpc_mfg_key_file = f"wpc_mfg_{self.ptmc_code}-{self.ca_seqid}.key"
        wpc_puc_crt_file = f"wpc_puc_ecc204_{pu_ser_num.hex().upper()}.crt"
        wpc_puc_key_file = f"wpc_puc_ecc204_{pu_ser_num.hex().upper()}.key"

        # Generate root certificate
        root_key = TPAsymmetricKey(key=self.root_key)
        root_key.get_private_pem(wpc_root_key_file)

        wpc_root_crt = self.__get_cert_to_reuse(wpc_root_crt_file, root_key)
        if wpc_root_crt is None:
            root_params = WPCRootCertParams(ca_key=root_key.get_private_pem())
            wpc_root_crt = create_wpc_root_cert(
                root_key.get_private_key(), root_params.root_cn, root_params.root_sn
            )
            Path(wpc_root_crt_file).write_text(
                wpc_root_crt.public_bytes(encoding=serialization.Encoding.PEM).decode(
                    "utf-8"
                )
            )
        self.root_crt = wpc_root_crt
        print(
            get_cert_print_bytes(
                wpc_root_crt.public_bytes(encoding=serialization.Encoding.PEM)
            )
        )

        # Generate Manufacturer certificate
        mfg_key = TPAsymmetricKey(key=self.mfg_key)
        mfg_key.get_private_pem(wpc_mfg_key_file)

        wpc_mfg_crt = self.__get_cert_to_reuse(wpc_mfg_crt_file, mfg_key)
        if wpc_mfg_crt is None:
            wpc_mfg_crt = create_wpc_mfg_cert(
                int(self.ptmc_code, 16),
                int(self.ca_seqid, 16),
                int(self.qi_id),
                mfg_key.get_public_key(),
                root_key.get_private_key(),
                wpc_root_crt,
            )
            Path(wpc_mfg_crt_file).write_text(
                wpc_mfg_crt.public_bytes(encoding=serialization.Encoding.PEM).decode(
                    "utf-8"
                )
            )
        self.mfg_crt = wpc_mfg_crt
        print(
            get_cert_print_bytes(
                wpc_mfg_crt.public_bytes(encoding=serialization.Encoding.PEM)
            )
        )

        # Generate Product Unit certificate
        wpc_puc_crt = create_wpc_puc_cert(
            qi_id=int(self.qi_id),
            rsid=int.from_bytes(os.urandom(4), byteorder="big"),
            public_key=puc_pubkey,
            ca_private_key=mfg_key.private_key,
            ca_certificate=wpc_mfg_crt,
        )

        puc_key = TPAsymmetricKey()
        puc_key.set_public_key(puc_pubkey)
        puc_key.get_public_pem(wpc_puc_key_file)
        Path(wpc_puc_crt_file).write_text(
            wpc_puc_crt.public_bytes(encoding=serialization.Encoding.PEM).decode(
                "utf-8"
            )
        )
        print(
            get_cert_print_bytes(
                wpc_puc_crt.public_bytes(encoding=serialization.Encoding.PEM)
            )
        )

        # Write product unit certificate(Slot 1) and WPC chain digest (Slot 2) in to ECC204 device
        ecc204_provision = ECC204Provision(interface="i2c", address=(0x38 << 1))
        fw_resource = ecc204_provision.provision_wpc_slots(
            wpc_root_crt, wpc_mfg_crt, wpc_puc_crt
        )

        root_cert = fw_resource.get("root_cert")
        root_digest = fw_resource.get("root_digest")
        mfg_cert = fw_resource.get("mfg_cert")
        puc_cert = fw_resource.get("puc_cert")

        with open(os.path.join("ecc204_tflxwpc.h"), "w") as f:
            f.write("#ifndef _ECC204_TFLXWPC_DATA_H\n")
            f.write("#define _ECC204_TFLXWPC_DATA_H\n\n")
            f.write("#ifdef __cplusplus\n")
            f.write('extern "C" {\n')
            f.write("#endif\n\n")

            asn1_cert = asn1crypto.x509.Certificate().load(root_cert, strict=True)
            pk_offset, pk_count = public_key_location(asn1_cert)
            sig_offset, sig_count = signature_location(asn1_cert)
            tbs_offset, tbs_count = tbs_location(asn1_cert)
            f.write(f"#define ROOT_PUBLIC_KEY_OFFSET        {pk_offset}\n")
            f.write(f"#define ROOT_PUBLIC_KEY_SIZE          {pk_count}\n")
            f.write(f"#define ROOT_SIGNATURE_OFFSET         {sig_offset}\n")
            f.write(f"#define ROOT_SIGNATURE_SIZE           {sig_count}\n")
            f.write(f"#define ROOT_TBS_OFFSET               {tbs_offset}\n")
            f.write(f"#define ROOT_TBS_SIZE                 {tbs_count}\n")
            f.write("\n\n")

            asn1_cert = asn1crypto.x509.Certificate().load(mfg_cert, strict=True)
            pk_offset, pk_count = public_key_location(asn1_cert)
            sig_offset, sig_count = signature_location(asn1_cert)
            tbs_offset, tbs_count = tbs_location(asn1_cert)
            f.write(f"#define MFG_PUBLIC_KEY_OFFSET         {pk_offset}\n")
            f.write(f"#define MFG_PUBLIC_KEY_SIZE           {pk_count}\n")
            f.write(f"#define MFG_SIGNATURE_OFFSET          {sig_offset}\n")
            f.write(f"#define MFG_SIGNATURE_SIZE            {sig_count}\n")
            f.write(f"#define MFG_TBS_OFFSET                {tbs_offset}\n")
            f.write(f"#define MFG_TBS_SIZE                  {tbs_count}\n")
            f.write("\n\n")

            asn1_cert = asn1crypto.x509.Certificate().load(puc_cert, strict=True)
            pk_offset, pk_count = public_key_location(asn1_cert)
            sig_offset, sig_count = signature_location(asn1_cert)
            tbs_offset, tbs_count = tbs_location(asn1_cert)
            f.write(f"#define PUC_PUBLIC_KEY_OFFSET         {pk_offset}\n")
            f.write(f"#define PUC_PUBLIC_KEY_SIZE           {pk_count}\n")
            f.write(f"#define PUC_SIGNATURE_OFFSET          {sig_offset}\n")
            f.write(f"#define PUC_SIGNATURE_SIZE            {sig_count}\n")
            f.write(f"#define PUC_TBS_OFFSET                {tbs_offset}\n")
            f.write(f"#define PUC_TBS_SIZE                  {tbs_count}\n")
            f.write("\n\n")

            # Root Cert
            f.write(f"const uint8_t root_cert[{len(root_cert)}] = \n")
            f.write("{\n" + f"{get_c_hex_bytes(root_cert)}" + "};\n\n")
            # mfg cert
            f.write(f"const uint8_t mfg_cert[{len(mfg_cert)}] = \n")
            f.write("{\n" + f"{get_c_hex_bytes(mfg_cert)}" + "};\n\n")
            # Root digest
            f.write(f"const uint8_t root_digest[{len(root_digest)}] = \n")
            f.write("{\n" + f"{get_c_hex_bytes(root_digest)}" + "};\n\n")

            f.write("#ifdef __cplusplus\n")
            f.write("}\n")
            f.write("#endif\n")
            f.write("#endif\n")

    def __get_user_input(self, b=None):
        user_inputs = TPWPCAuthUserInputs()
        user_inputs.invoke_dialog()
        user_inputs = json.loads(user_inputs.user_inputs.replace("'", '"'))
        assert len(user_inputs), "Please provide WPC inputs to run the Usecase"
        print("WPC User Inputs", canvas=b)
        for k, v in user_inputs.items():
            print(f"{k}: {v}")
        self.root_key = serialization.load_pem_private_key(
            data=user_inputs.get("root_key").encode(),
            password=None,
            backend=default_backend(),
        )
        self.mfg_key = serialization.load_pem_private_key(
            data=user_inputs.get("mfg_key").encode(),
            password=None,
            backend=default_backend(),
        )
        self.ptmc_code = (
            user_inputs.get("ptmc_code") if user_inputs.get("ptmc_code") else "004E"
        )
        self.qi_id = user_inputs.get("qi_id") if user_inputs.get("qi_id") else "11430"
        self.ca_seqid = (
            user_inputs.get("ca_seqid") if user_inputs.get("ca_seqid") else "01"
        )

    def __get_cert_to_reuse(self, crt_file, cert_key):
        wpc_cert = None
        if os.path.exists(crt_file):
            wpc_cert = Cert()
            wpc_cert.set_certificate(crt_file)
            cert_pubkey = wpc_cert.certificate.public_key().public_bytes(
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
                encoding=serialization.Encoding.DER,
            )
            input_pubkey = (
                cert_key.get_private_key()
                .public_key()
                .public_bytes(
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                    encoding=serialization.Encoding.DER,
                )
            )
            wpc_cert = None if (cert_pubkey != input_pubkey) else wpc_cert.certificate

        return wpc_cert


class TPWPCAuthUserInputs(TPInputDialog):
    def __init__(self) -> None:
        self.user_inputs = None
        super().__init__(self.get_wpc_auth_inputs, self.process_response)

    def get_wpc_auth_inputs(self):
        self.client_c.send_message("wpc_user_inputs", [""])

    def process_response(self, message):
        self.user_inputs = message
