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
from pathlib import Path
import json
import cryptoauthlib as cal

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, utils
from cryptography.hazmat.primitives import hashes

import tpds.tp_utils.tp_input_dialog as tp_userinput
from tpds.flash_program import FlashProgram
from tpds.secure_element import ECC204, ECC608A
from tpds.tp_utils.tp_settings import TPSettings
from tpds.tp_utils.tp_print import print
from tpds.tp_utils.tp_utils import pretty_print_hex
from tpds.certs.tflex_certs import TFLEXCerts
from tpds.certs.cert_utils import get_backend, get_cert_print_bytes


class JSONAuth():
    """
    Authenticates a connected accessory device using Symmetric Key.
    """

    def __init__(self, boards):
        self.boards = boards
        self.ser_num = None
        self.signer_def = None
        self.device_def = None
        self.meter_private_key_slot = 0
        self.pub_key = bytearray()
        self.json_msg = None
        self.json_dgst_204 = bytearray()
        self.signature = bytearray()
        self.verify_mode = 0x02
        self.key_id = 0x04
        self.accessory_sernum = None
        self.accessory_iface = "i2c"

# Generate public key of ECC204 Slot 0 private key
    def generate_resources(self, b=None):
        self.__connect_to_SE(b)

        # Get a public key from the ECC204
        print('Generating public key on Accessory device...')
        assert cal.atcab_get_pubkey(0, self.pub_key) == cal.Status.ATCA_SUCCESS, 'Failed to generate a public key.'
        print(pretty_print_hex(self.pub_key))
        print('OK', canvas=b)

        print('Generating crypto assets for Usecase...', canvas=b)
        root_crt = 'root.crt'
        root_key = 'root.key'
        signer_crt = 'signer.crt'
        signer_key = 'signer.key'
        device_crt = f'device_{self.ser_num.hex().upper()}.crt'

        # ToDo: Handle MCHP standard certificate backup process
        text_box_desc = (
            '''<font color=#0000ff><b>Enter Org Name for Custom PKI</b></font><br>
            <br>The organization name entered here would be used to
            generate TFLXTLS certificates.<br>''')
        custom_org = tp_userinput.TPInputTextBox(
            desc=text_box_desc,
            dialog_title='CustomPKI Org')
        custom_org.invoke_dialog()
        print(f'User Org Name: {custom_org.user_text}', canvas=b)
        assert (
            (custom_org.user_text is not None) and (len(custom_org.user_text))), \
            'Enter valid custom Org name'

        custom_certs = TFLEXCerts(device_name='ECC204')
        if os.path.exists(root_crt) and os.path.exists(root_key):
            custom_certs.root.set_certificate(root_crt)
            custom_certs.root.key.set_private_key(root_key)
            if (custom_certs.root.certificate.subject.get_attributes_for_oid(
                    x509.oid.NameOID.ORGANIZATION_NAME)[0].value != custom_org.user_text):
                custom_certs.build_root(org_name=custom_org.user_text)
        else:
            custom_certs.build_root(org_name=custom_org.user_text)
        Path(root_crt).write_bytes(custom_certs.root.get_certificate_in_pem())
        custom_certs.root.key.get_private_pem(root_key)
        print(get_cert_print_bytes(custom_certs.root.certificate.public_bytes(
            encoding=serialization.Encoding.PEM)))

        if os.path.exists(signer_crt) and os.path.exists(signer_key):
            custom_certs.signer.set_certificate(signer_crt)
            custom_certs.signer.key.set_private_key(signer_key)
            if (custom_certs.root.certificate.subject.get_attributes_for_oid(
                x509.oid.NameOID.ORGANIZATION_NAME)[0].value != custom_certs.signer.certificate.issuer.get_attributes_for_oid(
                    x509.oid.NameOID.ORGANIZATION_NAME)[0].value):
                custom_certs.build_signer_csr(org_name=custom_org.user_text)
                custom_certs.build_signer()
        else:
            custom_certs.build_signer_csr(org_name=custom_org.user_text)
            custom_certs.build_signer()
        Path(signer_crt).write_bytes(
            custom_certs.signer.get_certificate_in_pem())
        custom_certs.signer.key.get_private_pem(signer_key)
        print(get_cert_print_bytes(custom_certs.signer.certificate.public_bytes(
            encoding=serialization.Encoding.PEM)))

        custom_certs.build_device(device_sn=self.ser_num,
                                  device_public_key=self.pub_key,
                                  org_name=custom_org.user_text)
        Path(device_crt).write_bytes(
            custom_certs.device.get_certificate_in_pem())
        print(get_cert_print_bytes(custom_certs.device.certificate.public_bytes(
            encoding=serialization.Encoding.PEM)))

        # Validate and write the certificate chain
        assert custom_certs.is_certificate_chain_valid(), \
            'Cert chain validation failed'
        crt_template = custom_certs.get_tflex_py_definitions()
        self.signer_def = 'signer_pydef.txt'
        self.device_def = f'device_{self.ser_num.hex().upper()}_pydef.txt'
        custom_certs.save_tflex_c_definitions()
        custom_certs.save_tflex_py_definitions(
            signer_def_file='signer_pydef.txt',
            device_def_file=f'device_{self.ser_num.hex().upper()}_pydef.txt')
        assert cal.atcacert_write_cert(
            crt_template['signer'],
            custom_certs.signer.get_certificate_in_der(),
            len(custom_certs.signer.get_certificate_in_der())) \
            == cal.Status.ATCA_SUCCESS, \
            "Loading signer certificate into slot failed"
        assert cal.atcacert_write_cert(
            crt_template['device'],
            custom_certs.device.get_certificate_in_der(),
            len(custom_certs.device.get_certificate_in_der())) \
            == cal.Status.ATCA_SUCCESS, \
            "Loading device certificate into slot failed"
        self.dev_certs = TFLEXCerts(device_name='ECC204')
        self.dev_certs.root.set_certificate(root_crt)

    # Authenticate the meter ECC204
    def authenticate_meter(self, b=None):
        crt_template = self.dev_certs.get_tflex_py_definitions(
            signer_def_file=self.signer_def,
            device_def_file=self.device_def)

        print('Reading certificates from device: ', canvas=b)
        signer_cert_der_len = cal.AtcaReference(0)
        assert cal.CertStatus.ATCACERT_E_SUCCESS == cal.atcacert_max_cert_size(
            crt_template['signer'],
            signer_cert_der_len)
        signer_cert_der = bytearray(signer_cert_der_len.value)
        assert cal.CertStatus.ATCACERT_E_SUCCESS == cal.atcacert_read_cert(
            crt_template['signer'],
            self.dev_certs.root.certificate.public_key().public_bytes(
                format=serialization.PublicFormat.UncompressedPoint,
                encoding=serialization.Encoding.X962)[1:],
            signer_cert_der,
            signer_cert_der_len)
        signer_cert = x509.load_der_x509_certificate(
            bytes(signer_cert_der), get_backend())
        self.dev_certs.signer.set_certificate(signer_cert)

        device_cert_der_len = cal.AtcaReference(0)
        assert cal.CertStatus.ATCACERT_E_SUCCESS == cal.atcacert_max_cert_size(
            crt_template['device'],
            device_cert_der_len)
        device_cert_der = bytearray(device_cert_der_len.value)
        assert cal.CertStatus.ATCACERT_E_SUCCESS == cal.atcacert_read_cert(
            crt_template['device'],
            self.dev_certs.signer.certificate.public_key().public_bytes(
                format=serialization.PublicFormat.UncompressedPoint,
                encoding=serialization.Encoding.X962)[1:],
            device_cert_der,
            device_cert_der_len)
        device_cert = x509.load_der_x509_certificate(
            bytes(device_cert_der), get_backend())
        self.dev_certs.device.set_certificate(device_cert)

        print('Verifying Root certificate signature...', end='', canvas=b)
        is_cert_valid = self.dev_certs.root.is_signature_valid(
            self.dev_certs.root.certificate.public_key())
        assert is_cert_valid, 'Root certificate verification is failed'
        print('Valid', canvas=b)

        print('Verifying Signer certificate...', end='', canvas=b)
        is_cert_valid = self.dev_certs.signer.is_signature_valid(
            self.dev_certs.root.certificate.public_key())
        assert is_cert_valid, 'Signer certificate verification is failed'
        print('Valid', canvas=b)

        print('Verifying Device certificate...', end='', canvas=b)
        is_cert_valid = self.dev_certs.device.is_signature_valid(
            self.dev_certs.signer.certificate.public_key())
        assert is_cert_valid, 'Device certificate verification is failed'
        print('Valid', canvas=b)

        # Send verification challenge
        print('\nSending authentication challenge...')
        self.challenge = os.urandom(32)
        print(f'Challenge: {self.challenge.hex().upper()}')
        print('Get response from SE...', canvas=b)
        self.response = bytearray(64)
        assert cal.atcacert_get_response(
            crt_template['device'].private_key_slot,
            self.challenge, self.response) == cal.CertStatus.ATCACERT_E_SUCCESS
        print('OK', canvas=b)
        print(f'Response: {self.response.hex().upper()}')
        print('Verify response from SE...', canvas=b)
        r = int.from_bytes(self.response[0:32],
                           byteorder='big', signed=False)
        s = int.from_bytes(self.response[32:64],
                           byteorder='big', signed=False)
        sign = utils.encode_dss_signature(r, s)
        try:
            self.dev_certs.device.certificate.public_key().verify(
                sign, self.challenge, ec.ECDSA(
                    utils.Prehashed(hashes.SHA256())))
            print('OK', canvas=b)
        except Exception as err:
            raise ValueError(err)

    # Get a message from the user to use in a JSON message
    # Get SHA256 hash of the message for signing
    def generate_json_msg_on_host(self, b=None):
        input_selection = tp_userinput.TPInputDropdown(
            dialog_title='Select JSON input method',
            desc='JSON Input Selection',
            item_list=['Message String', 'JSON File Upload']
        )
        input_selection.invoke_dialog()
        assert input_selection.user_option is not None or input_selection.user_option != '', 'Must make a valid selection'
        if input_selection.user_option == 'Message String':
            text_box_desc = (
                '''
                <font color=#0000ff><b>Enter any string that will be converted into a JSON message</b></font>
                '''
            )
            msg_text = tp_userinput.TPInputTextBox(
                desc=text_box_desc,
                dialog_title='JSON Input'
            )
            msg_text.invoke_dialog()
            if msg_text.user_text is None or msg_text.user_text == "":
                raise ValueError("Message cannot be empty.")
            # Create JSON text
            self.json_msg = '{"msg" : "' + msg_text.user_text + '"}'
        elif input_selection.user_option == 'JSON File Upload':
            file_upload = tp_userinput.TPInputFileUpload(
                file_filter='',
                dialog_title='JSON File Input',
                nav_dir=os.getcwd()
            )
            file_upload.invoke_dialog()
            print(f'selected: {file_upload.file_selection}')
            json_in = None
            with open(file_upload.file_selection) as f:
                try:
                    json_in = json.load(f)
                except Exception:
                    assert False, 'Invalid JSON file selected.\nCheck JSON syntax and ensure correct file is selected'
            self.json_msg = str(json_in)

        send_msg = bytearray(self.json_msg, 'utf-8')
        print(f'JSON Message:\n{self.json_msg}\n')
        # Compute SHA digest on 204
        print('Computing message digest...')
        assert cal.atcab_sha_start() == cal.Status.ATCA_SUCCESS, 'Failed to start SHA engine on ECC204.'
        while len(send_msg) > 64:
            assert cal.atcab_sha_update(send_msg[0:64]) == cal.Status.ATCA_SUCCESS, 'Failed to send ECC204 message for SHA Hash.'
            send_msg = send_msg[64:]
        assert cal.atcab_sha_end(self.json_dgst_204, len(send_msg), send_msg) == cal.Status.ATCA_SUCCESS, 'Failed to end ECC204 SHA Hash.'
        print("SHA256 Hash of the JSON Message:\n%s" % (pretty_print_hex(self.json_dgst_204)))
        # Write JSON as a C string to project config header file
        self.write_project_config_h()
        print('OK', canvas=b)

# Sign the message hash
    def sign_json_msg(self, b=None):
        print("Signing JSON message...")
        assert cal.atcab_sign(self.meter_private_key_slot, self.json_dgst_204, self.signature) == cal.Status.ATCA_SUCCESS, 'Failed to sign message digest.'
        print('Message Signature:')
        print(pretty_print_hex(self.signature))
        print('OK', canvas=b)

# Rehash the message on the ECC608B
# Verify signature on the ECC608B
    def verify_json_msg(self, b=None):
        json_dgst_608 = bytearray()
        print('Verifying signature using the ECC608B...')
        ECC608A(address=0x6C)
        # perform SHA hash of message on 608
        send_msg = bytearray(self.json_msg, 'utf-8')
        assert cal.atcab_sha_start() == cal.Status.ATCA_SUCCESS, 'Failed to start SHA engine on ECC608B.'
        while len(send_msg) > 64:
            assert cal.atcab_sha_update(send_msg[0:64]) == cal.Status.ATCA_SUCCESS, 'Failed to send ECC608B message for SHA Hash.'
            send_msg = send_msg[64:]
        assert cal.atcab_sha_end(json_dgst_608, len(send_msg), send_msg) == cal.Status.ATCA_SUCCESS, 'Failed to end ECC608B SHA Hash.'
        # verify the signature
        assert cal.atcab_verify(self.verify_mode, self.key_id, self.signature, self.pub_key, None, None), 'Verification of the signature failed.'
        print('OK', canvas=b)

    def __connect_to_SE(self, b=None):
        print('Connecting to Secure Element: ')
        assert self.boards, \
            'Prototyping board MUST be selected!'
        assert self.boards.get_selected_board(), \
            'Select board to run a the usecase'

        kit_parser = FlashProgram()
        print(kit_parser.check_board_status())
        assert kit_parser.is_board_connected(), \
            'Check the Kit parser board connections'
        factory_hex = self.boards.get_kit_hex()
        if not kit_parser.is_factory_programmed():
            assert factory_hex, \
                'Factory hex is unavailable to program'
            print('Programming factory hex...')
            tp_settings = TPSettings()
            path = os.path.join(
                tp_settings.get_tpds_core_path(),
                'assets', 'Factory_Program.X',
                factory_hex)
            print(f'Programming {path} file')
            kit_parser.load_hex_image(path)

        # Get device interface selection from user
        input_selection = tp_userinput.TPInputDropdown(
            dialog_title='Device Comm',
            desc='Select Device communication protocol',
            item_list=['I2C', 'SWI']
        )
        input_selection.invoke_dialog()
        assert input_selection.user_option is not None or input_selection.user_option != '', 'Must make a valid selection'

        self.accessory_iface = 'i2c' if input_selection.user_option == 'I2C' else 'swi'

        element = ECC204(interface=self.accessory_iface, address=0x39 << 1)
        self.ser_num = element.get_device_serial_number()
        print('Device details: {}'.format(element.get_device_details()))
        print('OK')

    def write_project_config_h(self):
        # convert JSON message to C-style string
        _c_str_trans = str.maketrans({"\n": "\\n", "\"": "\\\"", "\\": "\\\\"})
        self.json_msg = self.json_msg.replace("'", '"')
        json_cstr = self.json_msg.translate(_c_str_trans)
        print(f'cstring:\n{json_cstr}')
        # write the user values into the project_config.h file
        project_config = os.path.join(os.getcwd(), 'project_config.h')
        with open(project_config, 'w') as f:
            f.write('#ifndef _PROJECT_CONFIG_H\n')
            f.write('#define _PROJECT_CONFIG_H\n\n')
            f.write('#ifdef __cplusplus\n')
            f.write('extern "C" {\n')
            f.write('#endif\n\n')
            f.write(f'#define SELECTED_ECC204_SWI {1 if self.accessory_iface == "swi" else 0}\n\n')
            f.write(
                f'#define JSON_MESSAGE_STRING "{json_cstr}"\n\n')
            f.write('#ifdef __cplusplus\n')
            f.write('}\n')
            f.write('#endif\n')
            f.write('#endif\n')
