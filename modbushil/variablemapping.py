from typing import Any
from modbushil.datatype import DataType
from modbushil.iotype import IOType
from modbushil.registerrange import RegisterRange


class VariableMapping:
    def __init__(self, var_config: dict[str, Any]):
        self.io_type: IOType = IOType.from_string(var_config["io_type"])
        self.data_type: DataType = DataType.from_string(var_config["data_type"])

        self.register: RegisterRange | None = None
        if "register" in var_config:
            self.register = RegisterRange.parse_registerrange(
                var_config["register"],
                reg_type_override=None,
            )

        self.mosaik: bool = False
        if "mosaik" in var_config:
            self.mosaik = var_config["mosaik"]

        self.scale: float = 1.0
        if "scale" in var_config:
            self.scale = float(var_config["scale"])
