from tpds.app.messages import tpds_app_message
from tpds.servers import ReservedMessageId
from .symm_auth_user_inputs import SymmAuthUserInputs
from .wpc_user_inputs import WPCUserInputs


@tpds_app_message(ReservedMessageId.symm_auth_user_inputs)
def symm_auth_user_inputs(self, args):
    obj = SymmAuthUserInputs()
    obj.exec()
    return "OK", f"{obj.user_data}"


@tpds_app_message(ReservedMessageId.wpc_user_inputs)
def wpc_user_inputs(self, args):
    obj = WPCUserInputs()
    obj.exec()
    return "OK", f"{obj.user_data}"
