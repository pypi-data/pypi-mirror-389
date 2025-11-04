# Trust Platform Design Suite - Usecase Help - Symmetric Authentication Challenge/Response pairs – SHA104-TFLXAUTH

This document helps to understand Pre and Post steps of Usecase transaction diagram.

## Setup requirements

- [DM320118](https://www.microchip.com/developmenttools/ProductDetails/DM320118)
- [EV97M19A SHA104/SHA105 Evaluation Board](https://www.microchip.com/en-us/development-tool/EV97M19A)
- [MPLAB X IDE](https://www.microchip.com/en-us/development-tools-tools-and-software/mplab-x-ide) 5.45 or above

## Pre Usecase transaction Steps

- Connect DM320118 + EV97M19A SHA104/SHA105 Evaluation Board board to PC running Trust Platform Design Suite
- Factory program must be present on the DM320118 board. If the factory firmware is not present do the following
    - Open TPDS Utilites 
    - Open "Device interactions" tab
    - Select the "Supported boards"
    - Click "Factory Program"
    - Note: "You can use "Scan for H/W changes" button to refresh connected hardware
- Open SHA104 configurator
    - Select the communication link ("Device interface") (I2C or SWI) 
    - Set "Limited Key Use" as "Disabled"
    - Leave all options other options as default, no changes are required from the default preset other than "Limited Key Use"    
    - Click on "Provision prototype samples"
- Ensure _MPLAB X Path_ is set in _File_ -> _Preference_ under _System Settings_. This helps
    - to program the Usecase prototyping kit to factory reset application by TPDS
    - to open the embedded project of the Usecase
- Note that _~/.trustplatform/spg_sha10x_cr_auth is the **Usecase working directory**. It contains the resources generated during transaction diagram execution.
  - ~ indicates home directory.
    - Windows home directory is \user\username
    - Mac home directory is /users/username
    - Most Linux/Unix home directory is /home/username

## Post Usecase transaction Steps

The usecase has three embedded projects, representing the following microcontroller boards

- [DM320118](https://www.microchip.com/developmenttools/ProductDetails/DM320118) (SAMD21E18A Microcontroller)
- [EV66E56A](https://www.microchip.com/en-us/development-tool/EV66E56A) (AVR64EA48 Microcontroller)
- [EV01G21A](https://www.microchip.com/en-us/development-tool/EV01G21A) (PIC18F56Q71 Microcontroller)

The usecase steps must first be run on DM320118 + EV97M19A to provision the SHA104 device and to generate the required files for the embedded projects. After the usecase steps are completed, any of the embedded projects can be evaluated as the SHA104 device is provisioned with the correct keys and the required ".h" files used by all embedded projects are generated.
### Post Usecase transaction Steps for DM320118 + EV97M19A - (SAMD21E18A Microcontroller)

On completing Usecase steps execution on TPDS, it is possible to either run the embedded project or view C source files by clicking _MPLAB X Project_ or _C Source Folder_ button.

- Once the Usecase project is loaded on MPLAB X IDE,
  - Set the project as Main -> right click on Project and select _Set as Main Project_
  - Set the configuration -> right click on Project, expand _Set Configuration_ to select _default_
  - Build and Program the project -> right click on Project and select _Make and Program Device_
- Log from the embedded project can be viewed using applications like TeraTerm. Select the COM port and set baud rate as 115200-8-N-1

### Post Usecase transaction Steps for DM320118 + EV66E56A - (AVR64EA48 Microcontroller)
#### Setup requirements
- [EV66E56A](https://www.microchip.com/en-us/development-tool/EV66E56A) (AVR64EA48 Microcontroller)
- [EV97M19A SHA104/SHA105 Evaluation Board](https://www.microchip.com/en-us/development-tool/EV97M19A)

On completing Usecase steps execution on TPDS, navigate to **Usecase working directory**. The embedded project would be available under firmware/SharedKey-SmallMCU-AVR64EA directory.

- Note that _~/.trustplatform/spg_sha10x_cr_auth is the **Usecase working directory**. It contains the resources generated during transaction diagram execution.
  - ~ indicates home directory.
    - Windows home directory is \user\username
    - Mac home directory is /users/username
    - Most Linux/Unix home directory is /home/username

- Once the Usecase project is loaded on MPLAB X IDE,
  - Set the project as Main -> right click on Project and select _Set as Main Project_
  - Set the configuration -> right click on Project, expand _Set Configuration_ to select _default_
  - Build and Program the project -> right click on Project and select _Make and Program Device_
- Log from the embedded project can be viewed using applications like TeraTerm. Select the COM port and set baud rate as 115200-8-N-1

### Post Usecase transaction Steps for DM320118 + EV01G21A - (PIC18F56Q71 Microcontroller)
#### Setup requirements
- [EV01G21A](https://www.microchip.com/en-us/development-tool/EV01G21A) (PIC18F56Q71 Microcontroller)
- [EV97M19A SHA104/SHA105 Evaluation Board](https://www.microchip.com/en-us/development-tool/EV97M19A)

On completing Usecase steps execution on TPDS, navigate to **Usecase working directory**. The embedded project would be available under firmware/SharedKey-SmallMCU-PIC18F directory.

- Note that _~/.trustplatform/spg_sha10x_cr_auth is the **Usecase working directory**. It contains the resources generated during transaction diagram execution.
  - ~ indicates home directory.
    - Windows home directory is \user\username
    - Mac home directory is /users/username
    - Most Linux/Unix home directory is /home/username

- Once the Usecase project is loaded on MPLAB X IDE,
  - Set the project as Main -> right click on Project and select _Set as Main Project_
  - Set the configuration -> right click on Project, expand _Set Configuration_ to select _default_
  - Build and Program the project -> right click on Project and select _Make and Program Device_
- Log from the embedded project can be viewed using applications like TeraTerm. Select the COM port and set baud rate as 115200-8-N-1
