import os
import sys

from PySide6.QtCore import QRegularExpression  # QRegExp
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
from tpds.tp_utils.tp_keys import TPSymmetricKey

from tpds.helper import log


class SymmAuthUserInputs(QDialog):
    """
    TrustFlex provisional XML Dialog to get all the user input for processing
    """

    def __init__(self, parent=None, config_string=None):
        """
        Init class
        """
        super(SymmAuthUserInputs, self).__init__(parent)
        self.setup_UI()
        self.show()

    def setup_UI(self):
        """
        Function to setup UI
        """
        self.setWindowTitle("Symmetric Authentication User Inputs")
        self.setMinimumSize(500, 250)

        self.layout = QGridLayout()
        self.row = self.column = 0
        self.user_data = {}
        self.add_device_interface()
        # self.add_authentication_scheme()
        self.add_auth_key_input()
        ok_button = QPushButton("OK", self)
        ok_button.clicked.connect(self.process_ok)
        self.layout.addWidget(ok_button, self.row, 1)
        cancel_button = QPushButton("Cancel", self)
        cancel_button.clicked.connect(self.process_cancel)
        self.layout.addWidget(cancel_button, self.row, 2)
        self.row += 1
        self.status_label = QLabel("Select Inputs for Symmetric Auth Usecase")
        self.layout.addWidget(self.status_label, self.row, 0, 1, 2)
        self.setLayout(self.layout)

    def add_device_interface(self):
        self.add_rb_group(["I2C", "SWI"], "Select device interface", self.rb_interface_handler)

    def add_authentication_scheme(self):
        self.add_rb_group(
            ["Diversified Key", "Master Key", "Challenge-Response"],
            "Select Authentication Scheme",
            self.rb_auth_scheme_handler,
        )

    def add_auth_key_input(self):
        self.add_rb_group(
            ["Generate", "Upload", "Type Hex"], "Select Key Input", self.rb_auth_key_handler
        )
        self.auth_key_line = QLineEdit()
        self.auth_key_line.setVisible(False)
        self.auth_key_line.setValidator(
            QRegularExpressionValidator(QRegularExpression("[0-9A-Fa-f]{64}"))
        )
        self.auth_key_line.textChanged.connect(self.cb_auth_key_type_hex)
        self.layout.addWidget(self.auth_key_line, self.row, 0, 1, 2)

        self.auth_key_button = QPushButton("Upload File")
        self.auth_key_button.setVisible(False)
        self.auth_key_button.clicked.connect(self.cb_auth_key_upload)
        self.layout.addWidget(self.auth_key_button, self.row, 0, 1, 2)
        self.row += 1

    def add_rb_group(self, options, label, handler):
        bg = QButtonGroup(self)
        group_label = QLabel(label)
        self.layout.addWidget(group_label, self.row, self.column)
        self.row += 1
        for rb_option in options:
            rb = QRadioButton(rb_option, self)
            # rb.setChecked(options.index(rb_option) == 0)
            rb.toggled.connect(handler)
            bg.addButton(rb)
            self.layout.addWidget(rb, self.row, self.column)
            self.column += 1
        self.row += 1
        self.column = 0

    def rb_interface_handler(self):
        if self.sender().isChecked():
            self.user_data.update({"interface": self.sender().text()})
        self.status_label.setText("Select Inputs for Symmetric Auth Usecase")

    def rb_auth_scheme_handler(self):
        if self.sender().isChecked():
            self.user_data.update({"auth_scheme": self.sender().text()})
        self.status_label.setText("Select Inputs for Symmetric Auth Usecase")

    def rb_auth_key_handler(self):
        if self.sender().isChecked():
            selected = self.sender().text()
            if selected == "Generate":
                self.auth_key_line.setVisible(False)
                self.auth_key_button.setVisible(False)
                self.user_data.update({"auth_key": os.urandom(32).hex().upper()[:64]})
                self.status_label.setText("32 byte random key will be generated...")

            elif selected == "Type Hex":
                self.auth_key_line.setVisible(True)
                self.auth_key_button.setVisible(False)
                self.status_label.setText("Enter 32 byte key in the text field...")

            elif selected == "Upload":
                self.auth_key_line.setVisible(False)
                self.auth_key_button.setVisible(True)
                self.status_label.setText("Upload 32-byte Symmetric key file in PEM format...")

    def cb_auth_key_upload(self):
        file_name = QFileDialog.getOpenFileName(
            None, caption="Select Symmetric Key File", filter="*.pem"
        )
        if file_name[0] != "":
            try:
                auth_key = TPSymmetricKey(file_name[0])
                self.status_label.setText(f"File selected: {file_name[0]}")
                self.user_data.update({"auth_key": auth_key.get_bytes().hex().upper()})
            except BaseException as e:
                log(f'''File upload failed with "{e}"''')
                self.status_label.setText("Upload is failed. Try again or check log for details...")

    def cb_auth_key_type_hex(self, text):
        self.auth_key_line.setText(text.upper())
        self.user_data.update({"auth_key": text.upper()})

    def process_ok(self):
        self.close()

    def process_cancel(self):
        self.user_data.clear()
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    obj = SymmAuthUserInputs()
    app.exec()
    print(obj.user_data)
