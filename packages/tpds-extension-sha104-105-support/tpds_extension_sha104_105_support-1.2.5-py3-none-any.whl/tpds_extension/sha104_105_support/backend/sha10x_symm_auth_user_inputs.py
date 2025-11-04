import sys
from PySide6.QtWidgets import QApplication
from tpds.app.messages import tpds_app_message
from tpds.servers import ReservedMessageId
from ecc204_support.symm_auth_user_inputs import SymmAuthUserInputs


@tpds_app_message(ReservedMessageId.sha10x_symm_auth_user_inputs)
def sha10x_symm_auth_user_inputs(self, args):
    obj = Sha10xSymmAuthUserInputs()
    obj.exec()
    return "OK", f"{obj.user_data}"


class Sha10xSymmAuthUserInputs(SymmAuthUserInputs):
    def __init__(self, parent=None, config_string=None):
        super().__init__(parent, config_string)

    def add_device_interface(self):
        self.add_rb_group(["I2C", "SWI"], "Select SHA10x device interface", self.rb_interface_handler)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    obj = Sha10xSymmAuthUserInputs()
    app.exec()
    print(obj.user_data)
