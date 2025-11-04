# Trust Platform Design Suite - Usecase Help - WPC Authentication – ECC204-TFLXWPC

This document helps to understand Pre and Post steps of Usecase transaction diagram.

## Setup requirements

- [DM320118](https://www.microchip.com/developmenttools/ProductDetails/DM320118)
- [ECC204 CRYPTOAUTH](https://www.microchip.com/en-us/development-tool/EV92R58A)
- [MPLAB X IDE](https://www.microchip.com/en-us/development-tools-tools-and-software/mplab-x-ide) 5.45 or above

## Pre Usecase transaction Steps

- Connect DM320118 + ECC204 CRYPTOAUTH board to PC running Trust Platform Design Suite.
- Open ECC204-TFLXWPC configurator, select the communication link (I2C or SWI) and the Limited Key Use (default "Disabled") then click on Provision prototype samples.
- Ensure _MPLAB X Path_ is set in _File_ -> _Preference_ under _System Settings_. This helps
  - To program the Usecase prototyping kit to factory reset application by TPDS
  - To open the embedded project of the Usecase
- Note that _~/.trustplatform/spg_ecc204_wpc_auth_ is the **Usecase working directory**. It contains the resources generated during transaction diagram execution.
  - ~ indicates home directory.
    - Windows home directory is \user\username
    - Mac home directory is /users/username
    - Most Linux/Unix home directory is /home/username

## Post Usecase transaction Steps

On completing Usecase steps execution on TPDS, it is possible to either run the embedded project or view C source files by clicking _MPLAB X Project_ or _C Source Folder_ button.

- Once the Usecase project is loaded on MPLAB X IDE,
  - Set the project as Main -> right click on Project and select _Set as Main Project_
  - Set the configuration -> right click on Project, expand _Set Configuration_ to select _default_
  - Build and Program the project -> right click on Project and select _Make and Program Device_
- Log from the embedded project can be viewed using applications like TeraTerm. Select the COM port and set baud rate as 115200-8-N-1
