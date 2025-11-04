# -*- coding: utf-8 -*-
# 2019 to present - Copyright Microchip Technology Inc. and its subsidiaries.

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
from pathlib import Path
from lxml import etree
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig
from tpds.schema import get_sha104_xsd_path, get_sha105_xsd_path
from tpds.schema.models.sha104_1_0 import sha104_config_1_0
from tpds.schema.models.sha105_1_0 import sha105_config_1_0


class SHA10x_XMLUpdates:
    BASE_XML_MAP = {
        "SHA104": {
            "xml": "SHA104_base.xml",
            "xsd": get_sha104_xsd_path(),
            "config_module": sha104_config_1_0,
            "config_class": sha104_config_1_0.Sha104Config,
            "config_file": "SHA104_Config_1.0"
        },
        "SHA105": {
            "xml": "SHA105_base.xml",
            "xsd": get_sha105_xsd_path(),
            "config_module": sha105_config_1_0,
            "config_class": sha105_config_1_0.Sha105Config,
            "config_file": "SHA105_Config_1.0"
        },
        "SHA106": {
            "xml": "SHA104_base.xml",
            "xsd": get_sha104_xsd_path(),
            "config_module": sha104_config_1_0,
            "config_class": sha104_config_1_0.Sha106Config,
            "config_file": "SHA104_Config_1.0"
        }
    }

    def __init__(self, base_xml) -> None:
        self.base_xml = base_xml
        base_device = next((key for key in self.BASE_XML_MAP if key in base_xml), None)
        assert base_device, f"Unknown device '{self.base_xml}'"
        base_info = self.BASE_XML_MAP.get(base_device)
        self.xsd_path = Path(base_info.get("xsd"))
        self.sha10x_config = base_info.get("config_module")
        self.config_file = base_info.get("config_file")
        self.xml_path = os.path.join(os.path.dirname(__file__), "base", base_info.get("xml"))
        self.xml_obj = XmlParser().from_string(Path(self.xml_path).read_text(encoding="utf-8"), base_info.get("config_class"))

    def save_root(self, dest_xml):
        config = SerializerConfig(pretty_print=True)
        serializer = XmlSerializer(config=config)
        dest_path = Path(dest_xml)
        with dest_path.open("w", encoding="utf-8") as fp:
            serializer.write(out=fp, obj=self.xml_obj, ns_map={
                "": f"https://www.microchip.com/schema/{self.config_file}"})

        status = self.__validate_xml(dest_xml)
        if (status != "valid"):
            dest_path.unlink(missing_ok=True)
            raise BaseException(f"XML generation failed with: {status}")

    def __validate_xml(self, xml_path: str):
        '''
        checks xml against it's xsd file
        '''
        with self.xsd_path.open(encoding="utf-8") as f_schema:
            schema_doc = etree.parse(f_schema)
            schema = etree.XMLSchema(schema_doc)
            parser = etree.XMLParser(schema=schema)

            with Path(xml_path).open(encoding="utf-8") as f_source:
                try:
                    etree.parse(f_source, parser)
                except etree.XMLSyntaxError as e:
                    return e
        return "valid"


class SHA10x_TFLXAUTH_XMLUpdates(SHA10x_XMLUpdates):
    def update_with_user_data(self, user_data):
        user_data = json.loads(user_data)
        self.__process_slot_config(user_data)
        self.__process_slot_data(user_data)

    def __process_slot_config(self, user_data):
        '''
        process config slots to provisiong XML
        '''
        self.xml_obj.config_name = f"{user_data.get('part_number')} {user_data.get('xml_type')}"

        # configuration_subzone_0
        configuration_subzone_0 = self.xml_obj.configuration_subzone_0
        configuration_subzone_0.io_options.interface = "SWI_PWM" if (
            user_data.get("interface") == "swi") else "I2C"
        if user_data.get("sn01"):
            configuration_subzone_0.sn_0_1.value = user_data.get("sn01")
        if user_data.get("sn8"):
            configuration_subzone_0.sn_8.value = user_data.get("sn8")

        # configuration_subzone_1
        configuration_subzone_1 = self.xml_obj.configuration_subzone_1
        configuration_subzone_1.chip_mode.cmos_en = "Fixed_Reference" if user_data.get(
            "fixed_reference") else "VCC_Referenced"
        configuration_subzone_1.chip_mode.clock_divider = "0b11"
        configuration_subzone_1.chip_mode.rng_nrbg_health_test_auto_clear = "True" if user_data.get(
            "health_test") else "False"
        configuration_subzone_1.slot_config3.limited_use = "True" if (
            user_data.get("limited_key_use") == "secret") else "False"
        configuration_subzone_1.slot_config3.write_mode = "Encrypted" if user_data.get(
            "encrypt_write") else "Clear"
        configuration_subzone_1.lock = "True"

        # configuration_subzone_2
        configuration_subzone_2 = self.xml_obj.configuration_subzone_2
        configuration_subzone_2.counts_remaining = 10000 - \
            user_data.get("counter_value")
        configuration_subzone_2.lock = "True"

        # configuration_subzone_3
        configuration_subzone_3 = self.xml_obj.configuration_subzone_3
        configuration_subzone_3.device_address = f'0x{user_data.get("device_address")}'
        configuration_subzone_3.lock = "True"
        configuration_subzone_3.self_test = "True" if user_data.get(
            "compliance") else "False"

    def __process_slot_data(self, user_data):
        '''
        Process data slots to provisioning XML
        '''
        slot_info = user_data.get("slot_info")

        # slot locks
        for slot in slot_info:
            setattr(self.xml_obj.slot_locks, f'''slot_{slot.get("slot_id")}''',
                    "True" if slot.get("slot_lock") == "enabled" else "False")

        # Data Sources and Writers
        self.xml_obj.data_sources.data_source = []
        self.xml_obj.data_sources.writer = []

        # Slot 0 - IO Protection Key
        if slot := next((slot for slot in slot_info if slot.get('slot_id') == 0 and slot.get('data')), None):
            ds = self.sha10x_config.DataSourceType(name="Slot_0_Client_Data",
                                                   description="Slot 0 IO Protection Key (32 bytes)")
            ds.static_bytes = self.sha10x_config.StaticBytesType(
                public=self.sha10x_config.BinaryDataOrStringType(
                    value=slot.get("data"), encoding="Hex"))
            self.xml_obj.data_sources.data_source.append(ds)
            self.xml_obj.data_sources.writer.append(
                self.sha10x_config.DataSourcesWriterType(
                    source_name="Slot_0_Client_Data", target="Slot 0"))

        # Slot 1 - General
        if slot := next((slot for slot in slot_info if slot.get('slot_id') == 1 and slot.get('data')), None):
            ds = self.sha10x_config.DataSourceType(name="Slot_1_Client_Data",
                                                   description="Slot 1 general public data storage (320 bytes)")
            ds.static_bytes = self.sha10x_config.StaticBytesType(
                public=self.sha10x_config.BinaryDataOrStringType(
                    value=slot.get("data"), encoding="Hex"))
            self.xml_obj.data_sources.data_source.append(ds)
            self.xml_obj.data_sources.writer.append(
                self.sha10x_config.DataSourcesWriterType(
                    source_name="Slot_1_Client_Data", target="Slot 1"))

        # Slot 2 - General
        if slot := next((slot for slot in slot_info if slot.get('slot_id') == 2 and slot.get('data')), None):
            ds = self.sha10x_config.DataSourceType(name="Slot_2_Client_Data",
                                                   description="Slot 2 general public data storage (64 bytes)")
            ds.static_bytes = self.sha10x_config.StaticBytesType(
                public=self.sha10x_config.BinaryDataOrStringType(
                    value=slot.get("data"), encoding="Hex"))
            self.xml_obj.data_sources.data_source.append(ds)
            self.xml_obj.data_sources.writer.append(
                self.sha10x_config.DataSourcesWriterType(
                    source_name="Slot_2_Client_Data", target="Slot 2"))

        # Slot 3 - Secret
        if slot := next((slot for slot in slot_info if slot.get('slot_id') == 3 and slot.get('data')), None):
            if user_data.get('slot3_kdf_value') != "no_kdf":
                name_value, true_false = ("IKM", "False") if user_data.get(
                    'slot3_kdf_value') == "HKDF_Extract" else (
                        ("PRK", "False") if user_data.get('slot3_kdf_value') == "HKDF_Expand" else ("Parent_Key", "False"))
            else:
                name_value, true_false = "Slot_3_Client_Data", "False"
            ds = self.sha10x_config.DataSourceType(name=name_value, description="Slot 3 Storage for a secret key")
            ds.static_bytes = self.sha10x_config.StaticBytesType(secret=self.sha10x_config.SecretBinaryDataType(encoding="Hex", key_name="WrapKey1", algorithm="AES256_GCM"), encrypted=true_false)
            ds.static_bytes.secret.encrypted = true_false
            ds.static_bytes.secret.value = slot.get("data")
            self.xml_obj.data_sources.data_source.append(ds)

            # Add Process_Info and KDF_Seed if diversified key is checked and Crypto_Auth_Derive_Key selected
            if user_data.get('slot3_kdf_value') in ["Crypto_Auth_Derive_Key"]:
                ds = self.sha10x_config.DataSourceType(name="Process_Info")
                ds.process_info = ""
                self.xml_obj.data_sources.data_source.append(ds)

                ds = self.sha10x_config.DataSourceType(name="KDF_Seed")
                ds.bytes_pad = self.sha10x_config.BytesPadType()
                ds.bytes_pad.input = "Process_Info.Serial_Number"
                ds.bytes_pad.fixed_size = self.sha10x_config.BytesPadType().FixedSize()
                ds.bytes_pad.fixed_size.output_size = "32"
                ds.bytes_pad.fixed_size.pad_byte = "0x00"
                ds.bytes_pad.fixed_size.alignment = self.sha10x_config.FixedSizeAlignment(value="Pad_Right")
                self.xml_obj.data_sources.data_source.append(ds)

            # Add KDF type if diversified key is checked
            if user_data.get('slot3_kdf_value') in ["HKDF_Extract", "HKDF_Expand", "Crypto_Auth_Derive_Key"]:
                ds = self.sha10x_config.DataSourceType(name="KDF") if user_data.get('slot3_kdf_value') in [
                    "HKDF_Extract", "HKDF_Expand"] else self.sha10x_config.DataSourceType(
                        name="Diversified_Key")
                ds.kdf = self.sha10x_config.Kdftype()

                if user_data.get('slot3_kdf_value') == "HKDF_Extract":
                    ds.kdf.hkdf_extract = self.sha10x_config.HkdfextractType()
                    ds.kdf.hkdf_extract.initial_keying_material = "IKM"
                    ds.kdf.hkdf_extract.output_size = "32"
                    ds.kdf.hkdf_extract.hash = "SHA256"
                elif user_data.get('slot3_kdf_value') == "HKDF_Expand":
                    ds.kdf.hkdf_expand = self.sha10x_config.HkdfexpandType()
                    ds.kdf.hkdf_expand.pseudorandom_key = "PRK"
                    ds.kdf.hkdf_expand.info = self.sha10x_config.StringOrDataOrFromSourceType()
                    ds.kdf.hkdf_expand.info.from_source = "False"
                    ds.kdf.hkdf_expand.info.encoding = "Hex"
                    ds.kdf.hkdf_expand.output_size = "32"
                    ds.kdf.hkdf_expand.hash = "SHA256"
                else:
                    ds.kdf.crypto_auth_derive_key = self.sha10x_config.CryptoAuthDeriveKeyType()
                    ds.kdf.crypto_auth_derive_key.parent_key = "Parent_Key"
                    ds.kdf.crypto_auth_derive_key.target_key = "3"
                    ds.kdf.crypto_auth_derive_key.seed = self.sha10x_config.StringOrDataOrFromSourceType()
                    ds.kdf.crypto_auth_derive_key.seed.from_source = "True"
                    ds.kdf.crypto_auth_derive_key.seed.value = "KDF_Seed"
                    ds.kdf.crypto_auth_derive_key.output_size = "32"
                self.xml_obj.data_sources.data_source.append(ds)

            # Writer For Slot 3
            if user_data.get('slot3_kdf_value') != "no_kdf":
                wr = self.sha10x_config.DataSourcesWriterType(source_name="KDF", target="Slot 3") if user_data.get(
                    'slot3_kdf_value') in ["HKDF_Extract", "HKDF_Expand"] else self.sha10x_config.DataSourcesWriterType(
                        source_name="Diversified_Key", target="Slot 3")
            else:
                wr = self.sha10x_config.DataSourcesWriterType(source_name="Slot_3_Client_Data", target="Slot 3")
            self.xml_obj.data_sources.writer.append(wr)

        # data source wrapped key
        self.xml_obj.data_sources.wrapped_key = []
