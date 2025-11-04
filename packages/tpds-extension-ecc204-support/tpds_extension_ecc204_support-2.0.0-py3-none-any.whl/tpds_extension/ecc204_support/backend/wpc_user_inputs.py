import os
import sys

from PySide6.QtCore import QRegularExpression  # RegExp
from PySide6.QtGui import QRegularExpressionValidator  # QRegExpValidator
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QDialog,
    QFileDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
)
from tpds.tp_utils.tp_keys import TPAsymmetricKey

from tpds.helper import log


class WPCUserInputs(QDialog):
    """
    WPC provisional XML Dialog to get all the user input for processing
    """

    def __init__(self, parent=None, config_string=None):
        """
        Init class
        """
        super(WPCUserInputs, self).__init__(parent)
        self.setup_UI()
        self.show()

    def setup_UI(self):
        """
        Function to setup UI
        """
        self.setWindowTitle("WPC Authentication User Inputs")
        self.setMinimumSize(432, 234)
        self.layout = QGridLayout()
        self.row = self.column = 0
        self.user_data = {}

        # get PTMC CODE (4-digit Hex value)
        self.add_ptmc_code_input()

        # get Company Qi ID (6-digit Integer value)
        self.row += 1
        self.add_qi_id_input()

        # get Mfg CA Sequence ID (2-digit Hex value)
        self.row += 1
        self.add_ca_seqid_input()

        # Generate / Upload Root and Mfg Private Key
        self.row += 1
        self.add_key_input()

        # add accept/cancel button
        self.row += 1
        ok_button = QPushButton("OK", self)
        ok_button.clicked.connect(self.process_ok)
        self.layout.addWidget(ok_button, self.row, 0)
        cancel_button = QPushButton("Cancel", self)
        cancel_button.clicked.connect(self.process_cancel)
        self.layout.addWidget(cancel_button, self.row, 1)

        # add status label at bottom of widget
        self.row += 1
        self.status_label = QLabel("Select Inputs for WPC Authentication Usecase")
        self.layout.addWidget(self.status_label, self.row, 0, 1, 5)
        self.setLayout(self.layout)

    # add PTMC CODE (4-digit Hex value)
    def add_ptmc_code_input(self):
        self.ptmc_label = QLabel("PTMC Code:")
        self.layout.addWidget(self.ptmc_label, self.row, 0, 1, 5)
        self.ptmc_code = QLineEdit()
        self.ptmc_code.setPlaceholderText("PTMC Code, default: 004E")
        self.ptmc_code.setValidator(
            QRegularExpressionValidator(QRegularExpression("[0-9A-Fa-f]{4}"))
        )
        self.ptmc_code.textChanged.connect(self.cb_set_ptmc_code)
        self.layout.addWidget(self.ptmc_code, self.row, 1, 1, 5)

    def cb_set_ptmc_code(self, text):
        self.ptmc_code.setText(text.upper())
        self.user_data.update({"ptmc_code": text.upper()})

    # add Company Qi ID (6-digit Integer value)
    def add_qi_id_input(self):
        self.qi_label = QLabel("Qi ID:")
        self.layout.addWidget(self.qi_label, self.row, 0, 1, 5)
        self.qi_id = QLineEdit()
        self.qi_id.setPlaceholderText("Qi ID, default: 11430")
        self.qi_id.setValidator(QRegularExpressionValidator(QRegularExpression("[0-9]{6}")))
        self.qi_id.textChanged.connect(self.cb_set_qi_id)
        self.layout.addWidget(self.qi_id, self.row, 1, 1, 5)

    def cb_set_qi_id(self, text):
        self.qi_id.setText(text.upper())
        self.user_data.update({"qi_id": text.upper()})

    # add Mfg CA Sequence ID (2-digit Hex value)
    def add_ca_seqid_input(self):
        self.label = QLabel("CA Sequence ID:")
        self.layout.addWidget(self.label, self.row, 0, 1, 5)
        self.ca_seqid = QLineEdit()
        self.ca_seqid.setPlaceholderText("CA Sequence ID, default: 01")
        self.ca_seqid.setValidator(
            QRegularExpressionValidator(QRegularExpression("[0-9A-Fa-f]{2}"))
        )
        self.ca_seqid.textChanged.connect(self.cb_set_ca_seqid)
        self.layout.addWidget(self.ca_seqid, self.row, 1, 1, 5)

    def cb_set_ca_seqid(self, text):
        self.ca_seqid.setText(text.upper())
        self.user_data.update({"ca_seqid": text.upper()})

    # add Generate / Upload Root and Mfg Private Key
    def add_key_input(self):
        # add radio button
        self.add_rb_group(["Generate", "Upload"], "Root and Mfg. keys:", self.rb_key_handler)

        # add root key input
        self.row += 1
        self.root_key_label = QLabel("Root Key")
        self.layout.addWidget(self.root_key_label, self.row, 1)
        # add root key input text
        self.root_key_text = QLineEdit()
        self.layout.addWidget(self.root_key_text, self.row, 2)
        # root key upload
        self.root_key_button = QPushButton("Browse")
        self.root_key_button.clicked.connect(self.cb_root_key_upload)
        self.layout.addWidget(self.root_key_button, self.row, 3)

        # add mfg key label
        self.row += 1
        self.mfg_key_label = QLabel("Mfg. Key")
        self.layout.addWidget(self.mfg_key_label, self.row, 1)
        # add mfg key input text
        self.mfg_key_text = QLineEdit()
        self.layout.addWidget(self.mfg_key_text, self.row, 2)
        # mfg key upload
        self.mfg_key_button = QPushButton("Browse")
        self.mfg_key_button.clicked.connect(self.cb_mfg_key_upload)
        self.layout.addWidget(self.mfg_key_button, self.row, 3)
        self.setDisable(True)

    def add_rb_group(self, options, label, handler):
        bg = QButtonGroup(self)
        group_label = QLabel(label)
        self.layout.addWidget(group_label, self.row, self.column)
        for rb_option in options:
            rb = QRadioButton(rb_option, self)
            rb.setChecked(options.index(rb_option) == 0)
            rb.toggled.connect(handler)
            bg.addButton(rb)
            self.column += 1
            self.layout.addWidget(rb, self.row, self.column)

        self.row += 1
        self.column = 0

    def cb_root_key_upload(self):
        file_name = QFileDialog.getOpenFileName(
            None, caption="Select Root Key File", filter="*.pem, *.key"
        )
        if file_name[0] != "":
            try:
                self.root_key_text.setText(file_name[0])
                self.status_label.setText(f"Root key file: {os.path.basename(file_name[0])}")
                root_key = TPAsymmetricKey(key=file_name[0])
                self.user_data.update({"root_key": root_key.get_private_pem()})
            except BaseException as e:
                log(f'File upload failed with: "{e}"')
                self.status_label.setText("Upload is failed. Try again or check log for details...")

    def cb_mfg_key_upload(self):
        file_name = QFileDialog.getOpenFileName(
            None, caption="Select Mfg. Key File", filter="*.pem, *.key"
        )
        if file_name[0] != "":
            try:
                self.mfg_key_text.setText(file_name[0])
                self.status_label.setText(f"Mfg key file: {os.path.basename(file_name[0])}")
                mfg_key = TPAsymmetricKey(key=file_name[0])
                self.user_data.update({"mfg_key": mfg_key.get_private_pem()})
            except BaseException as e:
                log(f'''File upload failed with "{e}"''')
                self.status_label.setText("Upload is failed. Try again or check log for details...")

    def rb_key_handler(self):
        if self.sender().isChecked():
            selected = self.sender().text()
            if selected == "Generate":
                self.setDisable(True)
                self.user_data.update({"root_key": TPAsymmetricKey().get_private_pem()})
                self.user_data.update({"mfg_key": TPAsymmetricKey().get_private_pem()})
                self.status_label.setText("ECC P256 random keys will be generated...")
            elif selected == "Upload":
                self.setDisable(False)
                self.user_data.update({"root_key": "", "mfg_key": ""})
                self.status_label.setText("Upload ECC P256 development Key files in PEM format...")

    def process_ok(self):
        if not self.user_data.get("root_key"):
            self.user_data.update({"root_key": TPAsymmetricKey().get_private_pem()})
        if not self.user_data.get("mfg_key"):
            self.user_data.update({"mfg_key": TPAsymmetricKey().get_private_pem()})
        if not self.user_data.get("ptmc_code"):
            self.user_data.update({"ptmc_code": "004E"})
        if not self.user_data.get("qi_id"):
            self.user_data.update({"qi_id": "11430"})
        if not self.user_data.get("ca_seqid"):
            self.user_data.update({"ca_seqid": "01"})

        self.close()

    def process_cancel(self):
        self.user_data.clear()
        self.close()

    def setDisable(self, status):
        self.root_key_button.setDisabled(status)
        self.root_key_text.setDisabled(status)
        self.root_key_label.setDisabled(status)
        self.mfg_key_button.setDisabled(status)
        self.mfg_key_text.setDisabled(status)
        self.mfg_key_label.setDisabled(status)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    obj = WPCUserInputs()
    app.exec_()
    print(obj.user_data)
