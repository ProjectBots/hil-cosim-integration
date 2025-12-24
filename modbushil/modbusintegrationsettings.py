from typing import Any

from modbushil.datatype import DataType
from modbushil.methodinvoker import MethodInvoker
from modbushil.iotype import IOType
from modbushil.modbusiobundlesconfiguration import ModbusIOBundlesConfiguration
from modbushil.variablemapping import VariableMapping


class ModbusIntegrationSettings:
    def __init__(self, config: dict[str, Any]):
        self.modbus_io_bundles: ModbusIOBundlesConfiguration = (
            ModbusIOBundlesConfiguration(config["modbus_io_bundles"])
        )
        self.variables: dict[str, VariableMapping] = {
            k: VariableMapping(v) for k, v in config["variables"].items()
        }
        self.read_methods: list[MethodInvoker] = []
        self.write_methods: list[MethodInvoker] = []
        if "methods" in config:
            method_configs = config["methods"]
            if "read" in method_configs:
                self.read_methods = [MethodInvoker(m) for m in method_configs["read"]]
            if "write" in method_configs:
                self.write_methods = [MethodInvoker(m) for m in method_configs["write"]]
        self.check_validity()

    def check_validity(self) -> None:
        # read cycle: all varaibles shown to Mosaik must be valid
        valid_vars = set()
        for var_name, var in self.variables.items():
            # all variables directly mapped to a register are valid
            if var.register is None:
                continue

            if var.io_type not in (IOType.READ, IOType.BOTH):
                continue

            if not self.modbus_io_bundles.has_read_range(var.register):
                raise ValueError(
                    f"Variable '{var_name}' is mapped to register {var.register} which is not included in any read range."
                )

            valid_vars.add(var_name)

        for method in self.read_methods:
            # variables set by read methods are also valid
            for req_var in method.required_variables:
                if req_var not in valid_vars:
                    raise ValueError(
                        f"Read method requires variable '{req_var}' which is not valid at this time."
                    )

            valid_vars.add(method.variable)

        for var_name, var in self.variables.items():
            # check if all variables marked for Mosaik are valid
            if not var.mosaik:
                continue

            if var.io_type not in (IOType.READ, IOType.BOTH):
                continue

            if var_name not in valid_vars:
                raise ValueError(
                    f"Variable '{var_name}' is marked for Mosaik but is not valid in read cycle."
                )

        # write cycle: all variables that will be written to Modbus must be valid
        valid_vars = set()
        for var_name, var in self.variables.items():
            # all variables coming from Mosaik are valid
            if not var.mosaik:
                continue

            if var.io_type not in (IOType.WRITE, IOType.BOTH):
                continue

            valid_vars.add(var_name)

        for method in self.write_methods:
            # variables set by write methods are also valid
            for req_var in method.required_variables:
                if req_var not in valid_vars:
                    raise ValueError(
                        f"Write method requires variable '{req_var}' which is not valid at this time."
                    )

            valid_vars.add(method.variable)

        for var_name, var in self.variables.items():
            # check if all variables marked for Modbus are valid
            if var.register is None:
                continue

            if var.io_type not in (IOType.WRITE, IOType.BOTH):
                continue

            if var_name not in valid_vars:
                raise ValueError(
                    f"Variable '{var_name}' is marked to be written over Modbus but is not valid in write cycle."
                )

            if not self.modbus_io_bundles.has_write_range(var.register):
                raise ValueError(
                    f"Variable '{var_name}' is mapped to register {var.register} which is not included in any write range."
                )

    def get_mosaik_non_trigger_variables(self) -> list[str]:
        vars_list: list[str] = []
        for var_name, var in self.variables.items():
            if var.mosaik and var.io_type in (IOType.WRITE, IOType.BOTH):
                vars_list.append(var_name)
        return vars_list

    def get_mosaik_persistent_variables(self) -> list[str]:
        vars_list: list[str] = []
        for var_name, var in self.variables.items():
            if var.mosaik and var.io_type in (IOType.READ, IOType.BOTH):
                vars_list.append(var_name)
        return vars_list

    def get_mosaik_persistent_variables_defaults(self) -> dict[str, Any]:
        vars_dict: dict[str, Any] = {}
        for var_name, var in self.variables.items():
            if var.mosaik and var.io_type in (IOType.READ, IOType.BOTH):
                if var.data_type == DataType.bool:
                    vars_dict[var_name] = False
                else:
                    vars_dict[var_name] = 0

        return vars_dict
