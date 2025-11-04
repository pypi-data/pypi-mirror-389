# Trust Platform Design Suite - Usecase Help - JSON Message Authentication – ECC204-TFLXAUTH

This document helps to understand transaction diagram, and pre- and post-steps of the usecase transaction diagram.

## Setup requirements

- [DM320118](https://www.microchip.com/developmenttools/ProductDetails/DM320118)
- [ECC204 CRYPTOAUTH](https://www.microchip.com/en-us/development-tool/EV92R58A)
- [MPLAB X IDE](https://www.microchip.com/en-us/development-tools-tools-and-software/mplab-x-ide) 5.45 or above

## Pre-Usecase Transaction Steps

- Connect DM320118 + ECC204 CRYPTOAUTH board to PC running Trust Platform Design Suite
  - Set DM320118 Switch 1 = ON, Switch 2 = OFF
- Open ECC204-TFLXAUTH configurator, select the communication link (I2C or SWI) and the Limited Key Use (default "Disabled") then click on Provision prototype samples.
- Ensure _MPLAB X Path_ is set in _File_ -> _Preference_ under _System Settings_. This helps
  - To program the usecase prototyping kit to factory reset application by TPDS
  - To open the embedded project after running the usecase
- Note that _~/.trustplatform/spg_json_auth_ecc204 is the **Usecase working directory**. It contains the resources generated during transaction diagram execution.
  - ~ indicates home directory.
    - Windows home directory is \user\username
    - Mac home directory is /users/username
    - Most Linux/Unix home directory is /home/username

## Transaction Diagram Steps

### Step 1

The first step of the use case will generate the Public Key Insfrastructure (PKI) required to authenticate the ECC204 device prior to accepting messages signed by it.  The only required input will be the organization name for the certificate, which can be any value for development.  The certificate chain's purpose is to securely deliver the device public key to the Data Concentrator and authenticate the device. This authentication can be a one-time process when the device's public key is stored in the Data Concentrator, or it may need to be repeated each time when the key is not stored or recurrent authentication is necessary.  The signer and device certificates are provisioned into Slot 1 of the ECC204 as compressed certificates, which are easily decompressed on the target MCU when using CryptoAuthLib.  For more information about these certificates and how they are validated, please check out the ECC204 Asymmetric Authentication use case on TPDS.  An ECC608, which is provided on the ECC204 CRYPTOAUTH Click Board, will be used to authenticate the ECC204 certificates and the JSON message.

### Step 2

The second step of the usecase will read the certificates from the device and validate them.  The host will also send a random challenge to ECC204 and validate the response using the device public key from the certificate to ensure that it is indeed the holder of the corresponding private key.  Once this step is performed, the validated public key can be used to verify the authenticity of any JSON messages sent to the host. The reading, decompression, and verification of these certificates on the embedded side is also demonstrated in the MPLAB X project included with the use case in the _~/.trustplatform/spg_json_auth_ecc204 folder, or by clicking the 'MPLAB X Project' button above the transaction diagram.

### Step 3

The third step of the use case will prompt you for the JSON input message.  The dropdown menu will allow selection of either a string input or a JSON file input.  When selected, the string input option will ask you to enter a short message string, which will then be converted into a very simple JSON message to be used for the remainder of the usecase.  The JSON file input option will ask you to provide a VALID JSON file to be used for message authentication during the use case.  Note that this JSON message will ultimately be converted into a C-string and written to a header file called 'project_config.h' in the _~/.trustplatform/spg_json_auth_ecc204 folder for use in the embedded project.

Once a valid JSON message is provided as input, the SHA256 digest of the message will also be computed by the ECC204 to be signed.

### Step 4

In the fourth step of the use case, the ECC204 will sign the message digest computed in Step 3 using the private key stored in Slot 0 of the device.  The JSON message and the resulting signature can then be sent to the host/data concentrator for verification.

### Step 5

In the fifth and final step of the use case, the message signature and the device public key are used to verify the message by the host/data concentrator.  The host must first compute the SHA256 hash of the message to use for validating the signature.  In this use case, the Crypto Module on the host side is the ECC608 that is provided on the ECC204 CRYPTOAUTH board.

## Post-Usecase Transaction Steps

On completing Usecase steps execution on TPDS, it is possible to either run the embedded project or view C source files by clicking _MPLAB X Project_ or _C Source Folder_ button.

- Once the Usecase project is loaded on MPLAB X IDE,
  - Set the project as Main -> right click on Project and select _Set as Main Project_
  - Set the configuration -> right click on Project, expand _Set Configuration_ to select _default_
  - Build and Program the project -> right click on Project and select _Make and Program Device_
- Log from the embedded project can be viewed using applications like TeraTerm. Select the COM port and set baud rate as 115200-8-N-1
