from typing import Any

from .datatype import DataType
from .iotype import IOType
from .registerrange import RegisterRange


class VariableMapping:
    def __init__(self, var_config: dict[str, Any]):
        self.io_type: IOType = IOType.from_string(var_config["iotype"])

        self.data_type: DataType | None = None
        if "datatype" in var_config:
            self.data_type = DataType.from_string(var_config["datatype"])

        self.register: RegisterRange | None = None
        if "register" in var_config:
            if "datatype" not in var_config:
                raise ValueError(
                    "If 'register' is specified, 'datatype' must also be specified."
                )
            self.register = RegisterRange.parse_registerrange(
                var_config["register"],
                reg_type_override=None,
            )

        self.mosaik: bool = False
        if "mosaik" in var_config:
            self.mosaik = var_config["mosaik"]

        self.scale: float | None = None
        if "scale" in var_config:
            self.scale = float(var_config["scale"])
