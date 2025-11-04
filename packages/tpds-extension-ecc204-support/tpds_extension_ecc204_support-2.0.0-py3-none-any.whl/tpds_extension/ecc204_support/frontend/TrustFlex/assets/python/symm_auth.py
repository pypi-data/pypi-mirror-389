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
from tpds.resource_generation import TFLXResources, TFLXSlotConfig
import cryptoauthlib as cal
from cryptography.hazmat.primitives import hashes, hmac
from tpds.flash_program import FlashProgram
from tpds.secure_element import ECC204, ECC608A
from tpds.tp_utils.tp_settings import TPSettings
from tpds.tp_utils.tp_print import print
from tpds.tp_utils.tp_input_dialog import TPInputDialog
from tpds.tp_utils.tp_utils import pretty_print_hex


class SymmetricAuthentication():
    """
    Authenticates a connected accessory device using Symmetric Key.
    """

    def __init__(self, boards, accessory_symm_key_slot, host_symm_key_slot):
        self.boards = boards
        self.accessory_symm_key_slot = accessory_symm_key_slot
        self.host_symm_key_slot = host_symm_key_slot
        self.auth_key = None
        self.accessory_sernum = None
        self.accessory_iface = None

    def generate_resources(self, b=None):
        self.__connect_to_SE(b)

        # Get user Inputs for Usecase options
        self.__get_user_input(b)

        # Generate Host_SE resources
        ecc608 = ECC608A(address=0x6C)
        print(f'Host device(ECC608) details: {ecc608.get_device_details()}')
        self.__load_master_key()

        # Generate Accessory_SE resources
        ecc204 = ECC204(interface=self.accessory_iface, address=0x39 << 1)
        print(
            f'Accessory device(ECC204) details : {ecc204.get_device_details()}')

        # Generate and load diversified key
        print(
            f'''Generating diversified key and loading to device's Slot{self.accessory_symm_key_slot}...''')
        self.accessory_sernum = bytes.fromhex(
            ecc204.get_device_serial_number().hex())
        diversified_key = self.__generate_diversified_key(
            salt=self.accessory_sernum, input_key=self.auth_key)
        assert cal.atcab_write_zone(
            zone=0x02,
            slot=self.accessory_symm_key_slot,
            data=diversified_key,
            block=0, offset=0, length=32) == cal.Status.ATCA_SUCCESS, \
            f'Failed to load diversified key into Accessory device slot {self.accessory_symm_key_slot}'
        print('OK', canvas=b)

    def generate_challenge_on_host(self, b=None):
        print('Generating random challenge on Host...')
        self.challenge = os.urandom(32)
        print(pretty_print_hex(self.challenge, li=10, indent=''))
        print('OK', canvas=b)

    def get_hmac_from_accessory_device(self, b=None):
        ecc204 = ECC204(interface=self.accessory_iface, address=0x39 << 1)
        counter_value = ecc204.get_monotonic_counter_value(0)
        print(f'ECC204 Monotonic counter value: {counter_value}')
        print('Calculating HMAC on accessory device...')
        self.device_hmac = bytearray(32)
        assert cal.atcab_sha_hmac(
            data=self.challenge,
            data_size=32,
            digest=self.device_hmac,
            target=0x00,
            key_slot=self.accessory_symm_key_slot) == cal.Status.ATCA_SUCCESS, \
            "HMAC response generation failed"
        print("HMAC received from accessory device:")
        print(pretty_print_hex(self.device_hmac, li=10, indent=''))
        counter_value = ecc204.get_monotonic_counter_value(0)
        print(f'ECC204 Monotonic counter value: {counter_value}')
        print('OK', canvas=b)

    def compare_host_hmac_with_accessory_hmac(self, b=None):
        self.__calculate_hmac_on_host(b)
        if self.host_hmac == self.device_hmac:
            print('Accessory device has authenticated successfully!', canvas=b)
        else:
            print('Accessory device authentication failed...', canvas=b)

    def __calculate_hmac_on_host(self, b=None):
        print('Calculating HMAC on Host Device...')
        diversified_key = self.__generate_diversified_key(
            salt=self.accessory_sernum, input_key=self.auth_key)
        h = hmac.HMAC(diversified_key, hashes.SHA256())
        h.update(self.challenge)
        self.host_hmac = h.finalize()
        print('HMAC calculated on host device:')
        print(pretty_print_hex(self.host_hmac, li=10, indent=''))
        print('OK', canvas=b)

    def __generate_diversified_key(self, salt, input_key):
        h = hmac.HMAC(input_key, hashes.SHA256())
        h.update(salt)
        return h.finalize()

    def __load_master_key(self):
        print(
            f'''Loading Master key into host device's Slot{self.host_symm_key_slot}''')
        resources = TFLXResources()
        tflex_slot_config = TFLXSlotConfig().tflex_slot_config

        symm_slot = self.host_symm_key_slot
        symm_key_slot_config = tflex_slot_config.get(symm_slot)
        assert symm_key_slot_config.get('type') == 'secret', \
            "Invalid Slot, It is expected to be secret"

        # Load encrypted Key... For dev env, loading IO protection every time.
        enc_slot = symm_key_slot_config.get('enc_key', 0x06)
        enc_key = os.urandom(32)
        assert resources.load_secret_key(
            enc_slot,
            enc_key,
            None,
            None) == cal.Status.ATCA_SUCCESS, \
            f"Loading encrypted key into Slot{enc_slot} has failed"

        # Load symmetric Key
        secret_key = self.auth_key
        assert resources.load_secret_key(
            symm_slot,
            secret_key,
            enc_slot,
            enc_key) == cal.Status.ATCA_SUCCESS, \
            f"Loading secret key into slot {enc_slot} failed"
        print('OK')

    def __connect_to_SE(self, b=None):
        print('Connecting to Secure Element: ')
        assert self.boards, \
            'Prototyping board MUST be selected!'
        assert self.boards.get_selected_board(), \
            'Select board to run an Usecase'

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
        print('OK')

    def __get_user_input(self, b=None):
        user_inputs = TPSymmAuthUserInputs()
        user_inputs.invoke_dialog()
        user_inputs = user_inputs.user_inputs  # get user input as json string
        print(f'Selected option is: {user_inputs}', canvas=b)
        user_inputs = json.loads(user_inputs.replace(
            "'", "\""))  # convert Json to dict

        self.accessory_iface = 'i2c' if 'I2C' == user_inputs.get(
            'interface') else 'swi'
        self.auth_key = user_inputs.get('auth_key')
        assert self.accessory_iface and self.auth_key, 'Please select valid inputs to run the usecase'
        # convert hex to bytes
        self.auth_key = bytes.fromhex(self.auth_key)

        # write the user values into the project_config.h file
        project_config = os.path.join(os.getcwd(), 'project_config.h')
        with open(project_config, 'w') as f:
            f.write('#ifndef _PROJECT_CONFIG_H\n')
            f.write('#define _PROJECT_CONFIG_H\n\n')
            f.write('#ifdef __cplusplus\n')
            f.write('extern "C" {\n')
            f.write('#endif\n\n')
            is_swi_selected = 1 if self.accessory_iface == 'swi' else 0
            f.write(
                f'#define SELECTED_ECC204_SWI {is_swi_selected} \n\n')
            f.write('#ifdef __cplusplus\n')
            f.write('}\n')
            f.write('#endif\n')
            f.write('#endif\n')


class TPSymmAuthUserInputs(TPInputDialog):
    def __init__(self) -> None:
        self.user_inputs = None
        super().__init__(self.get_symm_auth_inputs, self.process_response)

    def get_symm_auth_inputs(self):
        self.client_c.send_message('symm_auth_inputs', [''])

    def process_response(self, message):
        self.user_inputs = message
