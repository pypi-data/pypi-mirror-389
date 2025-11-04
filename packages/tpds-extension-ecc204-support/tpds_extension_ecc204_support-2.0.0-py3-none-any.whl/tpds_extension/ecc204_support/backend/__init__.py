import os
from tpds.devices import TpdsDevices
from tpds.xml_handler import XMLProcessingRegistry
from tpds.app.vars import get_app_ref
from .api.apis import router  # noqa: F401
from .api.ecc204_xml_updates import ECC204_TA010_TFLXAUTH_XMLUpdates, ECC204_TA010_TFLXWPC_XMLUpdates
from .msg_handler import symm_auth_user_inputs, wpc_user_inputs

TpdsDevices().add_device_info(os.path.join(os.path.dirname(__file__), "parts"))
XMLProcessingRegistry().add_handler('ECC204_TFLXAUTH', ECC204_TA010_TFLXAUTH_XMLUpdates('ECC204_TFLXAUTH'))
XMLProcessingRegistry().add_handler('ECC206_TFLXAUTH', ECC204_TA010_TFLXAUTH_XMLUpdates('ECC206_TFLXAUTH'))
XMLProcessingRegistry().add_handler('ECC204_TFLXWPC', ECC204_TA010_TFLXWPC_XMLUpdates('ECC204_TFLXWPC'))

if get_app_ref():
    get_app_ref()._messages.register(symm_auth_user_inputs)
    get_app_ref()._messages.register(wpc_user_inputs)
