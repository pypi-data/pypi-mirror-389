import os
import json
import random
import hashlib
import cryptoauthlib as cal
from tpds.flash_program import FlashProgram
from tpds.secure_element import SHA104
from tpds.proto_provision import SHA10xProvision
from tpds.tp_utils.tp_settings import TPSettings
from tpds.tp_utils.tp_print import print
from tpds.tp_utils.tp_input_dialog import TPInputDialog
from tpds.tp_utils.tp_utils import pretty_print_hex, get_c_hex_bytes
from symm_auth import TPSymmAuthUserInputs

class SymmetricAuthentication:
    """
    Authenticates a connected accessory device using Symmetric Key.
    """

    def __init__(self, boards, symm_key_slot=3):
        self.boards = boards
        self.symm_key_slot = symm_key_slot
        self.accessory_iface = None
        self.master_symm_key = None
        self.mac_mode = 0x00
        self.accessory_sn = None

    def generate_resources(self, b=None):
        self.__connect_to_SE(b)

        # Get user Inputs for Usecase options
        self.__get_user_input(b)

        #Ensure 104 is provisioned and load key into slot 3
        accessory_se = SHA10xProvision(
            device_cls=SHA104, interface=self.accessory_iface, address=0x31 << 1
        )
        #Ensure SHA104 is provisioned
        accessory_se_details = accessory_se.element.get_device_details()
        self.accessory_sn = bytearray.fromhex(accessory_se_details.get("serial_number"))
        print(f"Accessory device(SHA104) details: {accessory_se_details}")
        assert all(accessory_se_details.get('lock_status')[0]), "Accessory device should be provisioned first."
        self.__load_key(accessory_se, self.master_symm_key)
        print("OK", canvas=b)

    def generate_cr_pairs(self, b=None):
        print("Generating 5 Challenge/Response Pairs")
        self.challenges = []
        self.responses = []
        for i in range(0,5):
            new_challenge = os.urandom(32)
            new_response = bytearray(32)
            self.challenges.append(new_challenge)
            print(f"Challenge {i+1}")
            print(pretty_print_hex(new_challenge, li=10, indent=""))

            # generate response for the new challenge
            message = bytearray()
            message.extend(self.master_symm_key)
            message.extend(self.challenges[i])
            message.extend([0x08, 0x00, 0x03, 0x00])
            message.extend([0,0,0,0,0,0,0,0,0,0,0])
            message.append(self.accessory_sn[8])
            message.extend([0,0,0,0,0x01,0x23,0,0])

            # Calculate hash response using has lib
            hash_obj = hashlib.sha256()
            hash_obj.update(message)
            new_response = hash_obj.digest()
            self.responses.append(new_response)
            print(f"Response {i+1}")
            print(pretty_print_hex(new_response, li=10, indent=""))

        # write the user values into the project_config.h file
        project_config = os.path.join(os.getcwd(), 'project_config.h')
        with open(project_config, 'w') as f:
            
            f.write('#ifndef _PROJECT_CONFIG_H\n')
            f.write('#define _PROJECT_CONFIG_H\n\n')
            f.write('#ifdef __cplusplus\n')
            f.write('extern "C" {\n')
            f.write('#endif\n\n')
            f.write(f'#include <stdint.h>\n')
            is_swi_selected = 1 if self.accessory_iface == 'swi' else 0
            f.write(
                f'#define SELECTED_SHA104_SWI {is_swi_selected} \n\n')
            # write challenge array to c file
            f.write(f'uint8_t challenges[5][32] =\n')
            f.write('{\n')
            for i in range(0,4):
                f.write('\t{' + f'{get_c_hex_bytes(self.challenges[i])}' + '},\n')
            f.write('\t{' + f'{get_c_hex_bytes(self.challenges[4])}' + '}\n};\n\n')
            # write response array to c file
            f.write(f'uint8_t responses[5][32] =\n')
            f.write('{\n')
            for i in range(0,4):
                f.write('\t{' + f'{get_c_hex_bytes(self.responses[i])}' + '},\n')
            f.write('\t{' + f'{get_c_hex_bytes(self.responses[4])}' + '}\n};\n\n')
            f.write('#ifdef __cplusplus\n')
            f.write('}\n')
            f.write('#endif\n')
            f.write('#endif\n')
        print("OK", canvas=b)

    def send_random_challenge(self, b=None):
        accessory_se = SHA104(interface=self.accessory_iface, address=0x31 << 1)
        counter_value_pre_mac = accessory_se.get_monotonic_counter_value(0)
        print("Challenging accessory device...")
        self.chal_num = random.randint(0,4)
        self.accessory_mac = bytearray(32)
        status = cal.atcab_mac(
            self.mac_mode, self.symm_key_slot, self.challenges[self.chal_num], self.accessory_mac
        )
        assert (
            cal.Status.ATCA_SUCCESS == status
        ), f"Accessory response generation failed with error {status: 02X}"
        print("OK", canvas=b)
        
    def verify_accessory_response(self, b=None):
        print("Verifying accessory response...")
        print("Response received from accessory:")
        print(pretty_print_hex(self.accessory_mac, li=10, indent=""))
        print("Expected response:")
        print(pretty_print_hex(self.responses[self.chal_num], li=10, indent=""))
        assert(
            self.accessory_mac == self.responses[self.chal_num]
        ), f"Accessory response did not match expected response, not authenticated!"
        print("Accessory response authenticated!")

    def __load_key(self, secure_element, key_data):
        print(f"""Loading key into device's Slot{self.symm_key_slot}""")
        secure_element.perform_slot_write(self.symm_key_slot, key_data)
        print("OK")

    def __connect_to_SE(self, b=None):
        print("Connecting to Secure Element: ")
        assert self.boards, "Prototyping board MUST be selected!"
        assert self.boards.get_selected_board(), "Select board to run a Usecase"

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
