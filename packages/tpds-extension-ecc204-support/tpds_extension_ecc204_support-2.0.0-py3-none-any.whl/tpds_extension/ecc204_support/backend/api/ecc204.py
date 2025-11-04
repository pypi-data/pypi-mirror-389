import os
import json
import glob
from shutil import copyfile
from pathlib import Path
from datetime import datetime
from PySide6.QtCore import QDir
from tpds.helper import log, utils
from tpds.tp_utils.tp_input_dialog import TPInputDialog
from tpds.tp_utils.tp_input_dialog import TPMessageBox
from tpds.xml_handler.xml_processing import XMLProcessing
from tpds.tp_utils.tp_utils import add_to_zip_archive
from tpds.xml_handler.encrypt.encrypt import GenerateEncryptedXml


class GenerateProvisioningPackage():
    def __init__(self, config_string, device_name) -> None:
        self.display_msg = ''
        self.response_msg = 'Error'
        self.config_string = config_string
        self.data = config_string
        if isinstance(config_string, str):
            self.data = json.loads(config_string)
        log(f'Data for XML generation: {self.data}')

        self.curr_dir = os.getcwd()
        self.zip_file_list = []
        self.xml_type = self.data.get('xml_type')
        self.time_stamp = datetime.now().strftime("%m%d%H%M%S")
        self.device_name = device_name
        self.xml_file = f'{self.data.get("part_number")}_{self.time_stamp}.xml'
        self.cert_type = self.data.get("slot_info")[1].get("cert_type")

    def process_xml(self):
        if self.xml_type == "prod_xml":
            user_inputs = self.__get_user_inputs()
            if not user_inputs:
                raise AbortException("Abort the process")
            self.enc_key_file = user_inputs.get('enc_key_file')
            self.csr_zip_file = user_inputs.get('csr_zip_file')
            self.ca_key_file = user_inputs.get('ca_key_file')

            # get Enc key for production package
            assert os.path.exists(self.enc_key_file), \
                "Enc Key is must for Production package"
            self.provisioning_zip_file = f'{self.data.get("part_number")}_{self.time_stamp}_prod.zip'
        else:
            log("No encryption for Proto XML")
            self.provisioning_zip_file = f'{self.data.get("part_number")}_{self.time_stamp}_proto.zip'

        log("Setting output directory")
        self.provisioning_zip_dir = os.path.join(
            str(QDir.homePath()), 'Downloads', 'TPDS_Downloads')
        utils.make_dir(self.provisioning_zip_dir)
        os.chdir(self.provisioning_zip_dir)

        log("Processing configurator string")
        xml = XMLProcessing(self.data.get("base_xml"))
        xml.update_with_user_data(self.config_string)
        xml.save_root(self.xml_file)

        log("Archive Provisioning files to Zip")
        for extn in ['*.c', '*.h', '*.crt', '*.key', '*.txt']:
            self.zip_file_list.extend(glob.glob(extn))

    def process_enc(self):
        if self.xml_type == "prod_xml":
            if os.path.exists(self.enc_key_file):
                log("Encrypting XML File")
                self.__xml_encryption(self.xml_file, self.enc_key_file)
            else:
                raise ValueError("Enc Key is must for Production package")
        else:
            log("No XML encryption is taken place")

        log("Archive Provisioning files to Zip")
        if self.xml_type == "prod_xml":
            self.zip_file_list.extend(glob.glob("*.ENC.xml"))
        else:
            self.zip_file_list.extend(glob.glob("*.xml"))

        add_to_zip_archive(self.provisioning_zip_file, self.zip_file_list)

        path_link = os.path.join(
            self.provisioning_zip_dir, self.provisioning_zip_file).replace('\\', '/')
        self.response_msg = 'OK'
        self.display_msg = (
            f'<font color=#0000ff>'
            f'<b>Provisioning Package is saved </b></font>\n\n'
            f'''at <a href='{path_link}'>'''
            f'''{path_link}</a>\n'''
        )

    def get_response(self):
        if self.response_msg == "OK":
            msg_box = TPMessageBox(title=f"{self.device_name} Configurator", info=self.display_msg)
            msg_box.invoke_dialog()
        return {"response": self.response_msg, "status": self.display_msg}

    def cleanup(self):
        os.remove(self.xml_file) if os.path.exists(self.xml_file) else None
        for file in self.zip_file_list:
            os.remove(file) if os.path.exists(file) else None
        os.chdir(self.curr_dir)

    def __xml_encryption(self, xml_file, key_file, xml_out_file=''):
        """
        Add encryption to generted provisioning package
        Input(s):
            xml_file
            key_file
            xml_out_file
        Output:
            Encrypted provisioning package XML
        """
        if xml_out_file == '':
            xml_out_file = os.path.splitext(xml_file)[0] + '.ENC.xml'
        copyfile(xml_file, xml_out_file)
        xml = GenerateEncryptedXml(xml_file, encryption_key_file=key_file)
        xml.parse_datasource_section()
        xml.add_wrapped_key()
        Path(xml_out_file).write_bytes(xml.generate())

    def __get_user_inputs(self):
        """
        Get Provisioning User Inputs
        """
        user_inputs = ECC204ProvisionUserInputs(self.xml_type, self.cert_type)
        user_inputs.invoke_dialog()
        # get user input as json string
        user_inputs = user_inputs.user_inputs
        log(f'Selected option is: {user_inputs}')
        # convert Json to dict
        user_inputs = json.loads(user_inputs.replace("'", "\""))
        return user_inputs


class ECC204ProvisionUserInputs(TPInputDialog):
    '''
    Get inputs for ECC204 Provisioning Eg. Encryption key
    '''

    def __init__(self, xml_type="prod_xml", cert_type="custCert") -> None:
        self.user_inputs = None
        self.xml_type = xml_type
        self.cert_type = cert_type
        super().__init__(self.get_provision_inputs, self.process_response)

    def get_provision_inputs(self):
        self.client_c.send_message(
            'provision_inputs', [[self.xml_type, self.cert_type]])

    def process_response(self, message):
        self.user_inputs = message


class AbortException(Exception):
    pass
