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
import cryptoauthlib as cal
from tpds.flash_program import FlashProgram
from tpds.secure_element import SHA104, SHA105
from tpds.proto_provision import SHA10xProvision
from tpds.tp_utils.tp_settings import TPSettings
from tpds.tp_utils.tp_print import print
from tpds.tp_utils.tp_input_dialog import TPInputDialog
from tpds.tp_utils.tp_utils import pretty_print_hex, get_c_hex_bytes


class SymmetricAuthentication:
    """
    Authenticates a connected accessory device using Symmetric Key.
    """

    def __init__(self, boards, symm_key_slot=3):
        self.boards = boards
        self.symm_key_slot = symm_key_slot
        self.accessory_iface = None
        self.master_symm_key = None
        self.fixed_data = bytes([0 for i in range(23)])
        self.other_data = bytes([0 for i in range(4)])
        self.mac_mode = 0x40
        self.accessory_sn = None

    def generate_resources(self, b=None):
        self.__connect_to_SE(b)

        # Get user Inputs for Usecase options
        self.__get_user_input(b)

        # Generate Host_SE resources
        host_se = SHA10xProvision(device_cls=SHA105, address=0x32 << 1)
        host_se_details = host_se.element.get_device_details()
        print(f"Host device(SHA105) details: {host_se_details}")
        assert all(host_se_details.get('lock_status')[0]), "Host device should be provisioned first."
        self.__load_key(host_se, self.master_symm_key)

        # Generate Accessory_SE resources... Diversity master key and load to slot
        accessory_se = SHA10xProvision(
            device_cls=SHA104, interface=self.accessory_iface, address=0x31 << 1
        )
        accessory_se_details = accessory_se.element.get_device_details()
        self.accessory_sn = bytearray.fromhex(accessory_se_details.get("serial_number"))
        print(f"Accessory device(SHA104) details: {accessory_se_details}")

        assert all(accessory_se_details.get('lock_status')[0]), "Accessory device should be provisioned first."

        sn801 = [self.accessory_sn[8], self.accessory_sn[0], self.accessory_sn[1]]
        fixed_data = self.accessory_sn + bytearray(self.fixed_data)

        print(f"fixed data for GenDivKey: {fixed_data.hex().upper()}")
        print(f"Other data for GenDivKey: {self.other_data.hex().upper()}")

        diversified_key = accessory_se.element.get_diversified_key(
            self.master_symm_key, self.other_data, sn801, fixed_data
        )
        self.__load_key(accessory_se, diversified_key)

        # write the user values into the project_config.h file
        project_config = os.path.join(os.getcwd(), 'project_config.h')
        with open(project_config, 'w') as f:
            f.write('#ifndef _PROJECT_CONFIG_H\n')
            f.write('#define _PROJECT_CONFIG_H\n\n')
            f.write('#ifdef __cplusplus\n')
            f.write('extern "C" {\n')
            f.write('#endif\n\n')
            is_swi_selected = 1 if self.accessory_iface == 'swi' else 0
            f.write(f'#define SELECTED_SHA104_SWI {is_swi_selected} \n\n')
            f.write('uint8_t fixed_data[] = \n')
            f.write('{\n' + f'{get_c_hex_bytes(self.fixed_data)}' + '};\n\n')
            f.write('uint8_t other_data[] = \n')
            f.write('{\n' + f'{get_c_hex_bytes(self.other_data)}' + '};\n\n')
            f.write('#ifdef __cplusplus\n')
            f.write('}\n')
            f.write('#endif\n')
            f.write('#endif\n')

    def generate_challenge_on_host(self, b=None):
        print("Generating random challenge on Host...")
        SHA105(address=0x32 << 1)
        self.challenge = bytearray(32)
        num_in = bytearray(20)
        status = cal.atcab_nonce_rand(num_in, self.challenge)
        assert (status == cal.Status.ATCA_SUCCESS), \
            f"atcab_random has failed with: {status: 02X}"
        print(pretty_print_hex(self.challenge, li=10, indent=""))
        print("OK", canvas=b)

    def get_mac_from_accessory_device(self, b=None):
        accessory_se = SHA104(interface=self.accessory_iface, address=0x31 << 1)
        counter_value_pre_mac = accessory_se.get_monotonic_counter_value(0)
        print("Calculating MAC on accessory device...")
        self.accessory_mac = bytearray(32)
        status = cal.atcab_mac(
            self.mac_mode, self.symm_key_slot, self.challenge, self.accessory_mac
        )
        assert (
            cal.Status.ATCA_SUCCESS == status
        ), f"MAC response generation has failed with {status: 02X}"
        print("MAC received from accessory device:")
        print(pretty_print_hex(self.accessory_mac, li=10, indent=""))
        counter_value_post_mac = accessory_se.get_monotonic_counter_value(0)
        print(
            f"Accessory Monotonic counter value(pre_mac:post_mac): {counter_value_pre_mac}:{counter_value_post_mac}"
        )
        print("OK", canvas=b)

    def verify_mac_using_host_checkmac(self, b=None):
        host_se = SHA105(address=0x32 << 1)
        fixed_data = self.accessory_sn + bytes(self.fixed_data)
        status = cal.atcab_nonce_base(0x03, 0, fixed_data, bytearray())
        assert (
            cal.Status.ATCA_SUCCESS == status
        ), f"atcab_nonce_base has failed with {status:02X}"

        status = cal.get_cryptoauthlib().atcab_gendivkey(bytes(self.other_data))
        assert (
            cal.Status.ATCA_SUCCESS == status
        ), f"atcab_gendivkey has failed with {status:02X}"

        checkmac_other_data = host_se.build_checkmac_other_data(
            self.mac_mode, self.accessory_sn
        )
        status = cal.atcab_checkmac(
            0x06,
            self.symm_key_slot,
            self.challenge,
            self.accessory_mac,
            checkmac_other_data,
        )
        assert (
            cal.Status.ATCA_SUCCESS == status
        ), f"atcab_checkmac has failed with {status:02X}"
        print("Accessory / Disposable authentication is successful using mac-checkmac...", canvas=b)

    def __load_key(self, secure_element, key_data):
        print(f"""Loading key into device's Slot{self.symm_key_slot}""")
        secure_element.perform_slot_write(self.symm_key_slot, key_data)
        print("OK")

    def __connect_to_SE(self, b=None):
        print("Connecting to Secure Element: ")
        assert self.boards, "Prototyping board MUST be selected!"
        assert self.boards.get_selected_board(), "Select board to run an Usecase"

        kit_parser = FlashProgram()
        print(kit_parser.check_board_status())
        assert kit_parser.is_board_connected(), "Check the Kit parser board connections"
        factory_hex = self.boards.get_kit_hex()
        if not kit_parser.is_factory_programmed():
            assert factory_hex, "Factory hex is unavailable to program"
            print("Programming factory hex...")
            tp_settings = TPSettings()
            path = os.path.join(
                tp_settings.get_tpds_core_path(),
                "assets",
                "Factory_Program.X",
                factory_hex,
            )
            print(f"Programming {path} file")
            kit_parser.load_hex_image(path)
        print("OK")

    def __get_user_input(self, b=None):
        user_inputs = TPSymmAuthUserInputs()
        user_inputs.invoke_dialog()
        user_inputs = user_inputs.user_inputs  # get user input as json string
        print(f"Selected option is: {user_inputs}", canvas=b)
        user_inputs = json.loads(user_inputs.replace("'", '"'))  # convert Json to dict

        self.accessory_iface = "i2c" if "I2C" == user_inputs.get("interface") else "swi"
        self.master_symm_key = user_inputs.get("auth_key")
        assert (
            self.accessory_iface and self.master_symm_key
        ), "Please select valid inputs to run the usecase"
        # convert hex to bytes
        self.master_symm_key = bytes.fromhex(self.master_symm_key)

        # write the user values into the project_config.h file
        project_config = os.path.join(os.getcwd(), "project_config.h")
        with open(project_config, "w") as f:
            f.write("#ifndef _PROJECT_CONFIG_H\n")
            f.write("#define _PROJECT_CONFIG_H\n\n")
            f.write("#ifdef __cplusplus\n")
            f.write('extern "C" {\n')
            f.write("#endif\n\n")
            is_swi_selected = 1 if self.accessory_iface == "swi" else 0
            f.write(f"#define SELECTED_SHA104_SWI {is_swi_selected} \n\n")
            f.write("#ifdef __cplusplus\n")
            f.write("}\n")
            f.write("#endif\n")
            f.write("#endif\n")


class TPSymmAuthUserInputs(TPInputDialog):
    def __init__(self) -> None:
        self.user_inputs = None
        super().__init__(self.get_symm_auth_inputs, self.process_response)

    def get_symm_auth_inputs(self):
        self.client_c.send_message("sha10x_symm_auth_inputs", [""])

    def process_response(self, message):
        self.user_inputs = message
