from fastapi.routing import APIRouter
from .models import ConfiguratorMessageReponse, TFLXAUTHConfiguratorMessage, TFLXWPCConfiguratorMessage
from .tflxauth_ecc204 import ECC204TFLXAuthPackage, ecc204_tflxauth_proto_prov_handle
from .tflxwpc_ecc204 import ECC204TFLXWPCPackage, ecc204_tflxwpc_proto_prov_handle

router = APIRouter(prefix="/ecc204", tags=["ECC204_APIs"])


@router.post('/generate_tflxauth_xml', response_model=ConfiguratorMessageReponse)
def generate_tflxauth_xml(config_string: TFLXAUTHConfiguratorMessage):
    resp = ECC204TFLXAuthPackage(config_string.json(), config_string.base_xml)
    return resp.get_response()


@router.post('/provision_tflxauth_device')
def provision_tflxauth_device(config_string: TFLXAUTHConfiguratorMessage) -> None:
    resp = ecc204_tflxauth_proto_prov_handle(config_string.json(), config_string.base_xml)
    return resp


@router.post('/generate_tflxwpc_xml', response_model=ConfiguratorMessageReponse)
def generate_tflxwpc_xml(config_string: TFLXWPCConfiguratorMessage):
    resp = ECC204TFLXWPCPackage(config_string.json(), "ECC204_TFLXWPC")
    return resp.get_response()


@router.post('/provision_tflxwpc_device')
def provision_tflxwpc_device(config_string: TFLXWPCConfiguratorMessage) -> None:
    resp = ecc204_tflxwpc_proto_prov_handle(config_string.json(), "ECC204_TFLXWPC")
    return resp
