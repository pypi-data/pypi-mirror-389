import json
import cryptoauthlib as cal
from tpds.proto_provision import SHA10xProvision as DeviceProvision
from tpds.secure_element import SHA104, SHA105, SHA106
from tpds.helper import log
import tpds.tp_utils.tp_input_dialog as tp_userinput
from .sha10x import GenerateProvisioningPackage, AbortException


class SHA10xTFLXAuthPackage(GenerateProvisioningPackage):
    """
    Generate Provisioning Package
    """

    def __init__(self, config_string) -> None:
        try:
            data = config_string
            if isinstance(config_string, str):
                data = json.loads(config_string)
            super().__init__(config_string, data.get("base_xml"))
            self.process_xml()
            self.process_enc()
        except AbortException:
            self.response_msg = ""
            self.display_msg = "ABORT"
        except BaseException as e:
            self.display_msg = f"Provisioning Package process has failed with:\n{e}"
        finally:
            self.cleanup()


def sha10x_tflxauth_proto_prov_handle(config_str):
    data = config_str
    if isinstance(config_str, str):
        data = json.loads(config_str)
    log(f"Data for Proto Provisioning: {data}")

    log(f"Provisioning {data.get('base_xml')}")
    response_msg = "Error"
    display_msg = (
        "<font color=#0000ff>\n<b>Proto provisioning observations:</b></font>\n\n"
    )

    try:
        log("Connecting to device...")
        user_device_address = int(data.get("device_address"), 16)
        is_device_connected = False
        device_prov = None

        base_xml = data.get("base_xml")

        if "SHA104" in base_xml:
            device_cls = SHA104
        elif "SHA105" in base_xml:
            device_cls = SHA105
        elif "SHA106" in base_xml:
            device_cls = SHA106
        else:
            device_cls = SHA104

        if "SHA105" in base_xml:
            device_default_addr = 0x32
        else:
            device_default_addr = 0x31

        for address in [user_device_address, device_default_addr]:
            try:
                device_proto_provision = DeviceProvision(
                    device_cls, data.get("interface"), address << 1
                )
                log(f"Device Connected with address 0x{address:02X}")
                is_device_connected = True
                break
            except BaseException as e:
                log(
                    f"Failed to connect device with address 0x{address:02X}: {e}")

        if is_device_connected:
            msg_box_info = (
                "<font color=#0000ff>You are about to proto provision a blank device."
                "Changes cannot be reverted once provisioning is done. Do you want to continue?"
            )
            device_prov = tp_userinput.TPMessageBox(
                title="Blank device Provisioning", info=msg_box_info
            )
            if not device_proto_provision.element.is_config_zone_locked():
                device_prov.invoke_dialog()
                if device_prov.user_select != "Cancel":
                    configBytes = bytearray.fromhex(
                        """
                        01 23 47 29 CA 9A 3B 7A  EE 35 00 00 00 00 00 00
                        0F 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00
                        00 00 00 00 FF FF FF FF  FF FF FF FF FF FF FF FF
                        31 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00
                        """
                    )
                    # CSZ0
                    # set device interface
                    configBytes[10] = 0x00 if (
                        data.get("interface") == "swi") else 0x01

                    # set Serial Number
                    sn01 = data.get("sn01")
                    sn8 = data.get("sn8")
                    configBytes[0] = int(sn01[0:2], base=16)
                    configBytes[1] = int(sn01[2:4], base=16)
                    configBytes[8] = int(sn8, base=16)

                    # CSZ1
                    # set Chip mode - Health Test Auto Clear
                    if data.get("health_test"):
                        configBytes[16] |= 1 << 3  # set 1 to 3-bit
                    else:
                        configBytes[16] &= ~(1 << 3)  # set 0 to 3-bit

                    # Set Chip mode - I/O levels to fixed reference
                    if data.get("fixed_reference"):
                        configBytes[16] = configBytes[16] & 0x0E

                    # Set ECC private key to monotonic counter
                    if data.get("limited_key_use") == "private":
                        configBytes[17] |= 0x01

                    # Set HMAC secret key to monotonic counter
                    if data.get("limited_key_use") == "secret":
                        configBytes[20] |= 0x02

                    # set Encrypt write enable/disable option
                    if data.get("encrypt_write"):
                        configBytes[20] |= 0x01  # set 1 to 0-bit
                    else:
                        configBytes[20] &= ~0x01  # set 0 to 0-bit

                    # CSZ2
                    # Set Counter Value
                    counterBytes = device_proto_provision.int_to_binary_linear(
                        data.get("counter_value")
                    )
                    log(f"Counter Data:{bytearray(counterBytes).hex().upper()}")
                    configBytes[32:48] = bytearray(counterBytes)

                    # CSZ3
                    # Set user device address to CSZ3 First Byte
                    configBytes[48] = user_device_address

                    # set compliance mode
                    configBytes[49] = 0x01 if (
                        data.get("compliance")) else 0x00

                    # provision config zone
                    device_proto_provision.element.load_tflx_test_config(
                        bytes(configBytes)
                    )
                else:
                    display_msg = "Device Protoprovisioning is aborted."
            else:
                log("Connected device is already configured and locked")
                msg_box_info = (
                    "<font color=#0000ff>Configuration Zone of the connected device is locked. <br />"
                    "Do you want to provision the Data Zone?"
                )
                device_prov = tp_userinput.TPMessageBox(
                    title="Device Provisioning", info=msg_box_info
                )
                device_prov.invoke_dialog()

            if device_prov.user_select != "Cancel":
                # read counter
                counter_value = cal.AtcaReference(0)
                assert (
                    cal.atcab_counter_read(
                        0, counter_value) == cal.Status.ATCA_SUCCESS
                ), "atcab_counter_read has failed"
                log(f"Counter value: {counter_value}")

                # read config zone
                device_config = bytearray(64)
                assert (
                    cal.atcab_read_config_zone(
                        device_config) == cal.Status.ATCA_SUCCESS
                ), "atcab_read_config_zone has failed"
                log(f"Config Data: {device_config.hex().upper()}")

                # read Serial Number
                device_sn = bytearray()
                assert (
                    cal.atcab_read_serial_number(
                        device_sn) == cal.Status.ATCA_SUCCESS
                ), "Reading Serial number failed"

                slot_info = data.get("slot_info")
                for slot in slot_info:
                    slot_msg = ""
                    slot_id = int(slot.get("slot_id"))
                    if slot.get("key_load_config") not in ["cert", "no_load"] and slot.get("data"):
                        slot_data = bytes.fromhex(slot.get("data"))
                        if slot_id == 3 and data.get("slot3_kdf_value") == "Crypto_Auth_Derive_Key":
                            slot_data = get_diversified_key(
                                device=device_proto_provision,
                                master_symm_key=slot_data,
                                device_sn=device_sn)
                        device_proto_provision.perform_slot_write(
                            slot_id, slot_data)
                        slot_msg = "User data loaded."
                    else:
                        slot_msg = (
                            "Pregenerated." if slot_id == 0 else "Skipped."
                        )
                    display_msg += f"<br/>Slot{int(slot.get('slot_id'))} ({slot.get('slot_type')}): {slot_msg}"
                display_msg += "<br/>Prototype board provisioning completed!"
                response_msg = "OK"
            else:
                response_msg = "Aborted"
                display_msg = "Device Protoprovisioning is aborted."
        else:
            display_msg = "Unable to connect to device, Check device address and connections before retrying"
    except BaseException as e:
        display_msg += f"\nDevice prototyping has failed with: {e}"

    finally:
        log(display_msg)
        if response_msg == "OK":
            msg_box = tp_userinput.TPMessageBox(
                title=f"{data.get('base_xml')} Configurator",
                info=(display_msg))
            msg_box.invoke_dialog()
    return {"response": response_msg, "status": display_msg}


def get_diversified_key(device, master_symm_key: bytes, device_sn: bytearray) -> bytes:
    log('Generate Diversified key From Master Key')
    sn801 = [device_sn[8], device_sn[0], device_sn[1]]
    fixed_data = bytes([0 for i in range(23)])
    other_data = bytes([0 for i in range(4)])
    fixed_data = device_sn + bytes(fixed_data)
    log(f"fixed data for GenDivKey: {fixed_data.hex().upper()}")
    log(f"Other data for GenDivKey: {other_data.hex().upper()}")
    diversified_key = device.element.get_diversified_key(
        master_symm_key, other_data, sn801, fixed_data
    )
    return diversified_key


if __name__ == "__main__":
    pass
