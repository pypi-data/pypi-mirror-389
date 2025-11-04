from fastapi.routing import APIRouter
from .models import (
    ConfiguratorMessageReponse,
    TFLXAUTHConfiguratorMessage,
)
from .sha10x_tflxauth import SHA10xTFLXAuthPackage, sha10x_tflxauth_proto_prov_handle

router = APIRouter(prefix="/sha10x", tags=["SHA10x_APIs"])


@router.post("/generate_tflxauth_xml", response_model=ConfiguratorMessageReponse)
def generate_tflxauth_xml(config_string: TFLXAUTHConfiguratorMessage):
    resp = SHA10xTFLXAuthPackage(config_string.json())
    return resp.get_response()


@router.post("/provision_tflxauth_device")
def provision_tflxauth_device(config_string: TFLXAUTHConfiguratorMessage) -> None:
    resp = sha10x_tflxauth_proto_prov_handle(config_string.json())
    return resp
