from enum import Enum
from pydantic import BaseModel
from typing import List, Optional
from tpds.devices.tpds_models import DeviceInterface


class ConfiguratorMessageReponse(BaseModel):
    """
    Configurator Message response data
    """

    response: str = "OK"
    status: str = "success"


class ConfiguratorXMLTypes(str, Enum):
    """
    XML format types from Configurators
    """

    # proto XML contains data in clear format
    proto = "proto_xml"
    # production XML contains secrets in encrypted format
    prod = "prod_xml"


class ConfiguratorSlotTypes(str, Enum):
    """
    Slot types information from Configurator
    """

    general = "general"
    secret = "secret"


class ConfiguratorSlotLock(str, Enum):
    """
    Slot lock information from Configurator
    """

    enabled = "enabled"
    disabled = "disabled"


class ConfiguratorKeyLoad(str, Enum):
    """
    Slot lock information from Configurator
    """

    no_load = "noLoad"
    load = "load"


class TFLXConfiguratorSlotInfo(BaseModel):
    """
    Base class for TFLX Slot Information in the message from Configuratorconfigurator
    """

    slot_id: int = 1
    slot_type: ConfiguratorSlotTypes = ConfiguratorSlotTypes.general
    key_load_config: ConfiguratorKeyLoad = ConfiguratorKeyLoad.no_load
    slot_lock: Optional[ConfiguratorSlotLock] = ConfiguratorSlotLock.disabled
    data: Optional[str] = ""


class TFLXConfiguratorMessage(BaseModel):
    """
    Base class for TFLX configurator Request Message
    """

    # Provisioning base XML file to use for final XML
    base_xml: str = ""
    # XML format to be generated
    xml_type: str = "proto_xml"
    # Interface Type
    interface: Optional[DeviceInterface] = DeviceInterface.i2c
    # Device Address
    device_address: str = ""
    # Fixed Reference
    fixed_reference: bool = False
    # Limited Use Key
    limited_key_use: str = ""
    # Enable Encrypted Write for HMAC Key
    encrypt_write: bool = False
    # diversified key option
    diversified_key: bool = False
    # Monotonic Counter
    counter_value: int = 0
    # serial number sn01, sn8
    sn01: str = "0123"
    sn8: str = "EE"
    slot3_kdf_value: str = "HKDF_Extract"


class TFLXAUTHConfiguratorMessage(TFLXConfiguratorMessage):
    """
    TFLXAUTH Configurator Request Message
    """

    # Provisioning base XML file to use for final XML
    base_xml: str = "SHA104_TFLXAUTH"
    # Enable Compliance Mode
    compliance: bool = False
    # health test
    health_test: bool = False
    # Slots information
    slot_info: List[TFLXConfiguratorSlotInfo] = [TFLXConfiguratorSlotInfo()]
    # Part Number
    part_number: str = ''
