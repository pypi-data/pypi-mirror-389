import os
from .api.apis import router
from tpds.devices import TpdsDevices
from tpds.app.vars import get_app_ref
from tpds.xml_handler import XMLProcessingRegistry
from .api.sha10x_xml_updates import SHA10x_TFLXAUTH_XMLUpdates
from .sha10x_symm_auth_user_inputs import sha10x_symm_auth_user_inputs


if get_app_ref():
    get_app_ref()._messages.register(sha10x_symm_auth_user_inputs)


TpdsDevices().add_device_info(os.path.dirname(__file__))
XMLProcessingRegistry().add_handler('SHA104_TFLXAUTH', SHA10x_TFLXAUTH_XMLUpdates('SHA104_TFLXAUTH'))
XMLProcessingRegistry().add_handler('SHA105_TFLXAUTH', SHA10x_TFLXAUTH_XMLUpdates('SHA105_TFLXAUTH'))
XMLProcessingRegistry().add_handler('SHA106_TFLXAUTH', SHA10x_TFLXAUTH_XMLUpdates('SHA106_TFLXAUTH'))
