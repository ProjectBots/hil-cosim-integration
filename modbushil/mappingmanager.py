from typing import Any

from .modbusclientmanager import ModbusClientManager
from .modbusintegrationsettings import ModbusIntegrationSettings
from .variablemapping import VariableMapping
from .iotype import IOType
from .datatype import DataType


class MappingManager:
    def __init__(self, config: ModbusIntegrationSettings, host: str, port: int):
        self.config: ModbusIntegrationSettings = config

        self.variable_buffer: dict[str, Any] = {}

        self.modbus_manager: ModbusClientManager = ModbusClientManager(
            host, port, config.modbus_io_bundles
        )
        self.modbus_manager.connect()

    def close(self) -> None:
        self.modbus_manager.disconnect()

    def get_variable_mapping(self, variable_name: str) -> VariableMapping:
        return self.config.variables[variable_name]

    def read_phase(self) -> None:
        self.modbus_manager.do_read()

        # direct variable mappings
        for var_name, var in self.config.variables.items():
            if var.register is None:
                continue

            if var.io_type not in (IOType.READ, IOType.BOTH):
                continue

            value = None
            if var.data_type in (DataType.int16, DataType.int32, DataType.int64):
                value = self.modbus_manager.get_int(var.register)
            elif var.data_type in (DataType.uint16, DataType.uint32, DataType.uint64):
                value = self.modbus_manager.get_uint(var.register)
            elif var.data_type in (DataType.float32, DataType.float64):
                value = self.modbus_manager.get_float(var.register)
            elif var.data_type == DataType.bool:
                value = self.modbus_manager.get_bool(var.register)
            else:
                raise ValueError(f"Unsupported data type: {var.data_type}")

            if var.scale is not None:
                value = value * var.scale

            self.variable_buffer[var_name] = value

        # read methods
        for method in self.config.read_methods:
            result = method.invoke(self.variable_buffer)
            self.variable_buffer[method.variable] = result

    def write_phase(self) -> None:
        # write methods
        for method in self.config.write_methods:
            result = method.invoke(self.variable_buffer)
            self.variable_buffer[method.variable] = result

        # direct variable mappings
        for var_name, var in self.config.variables.items():
            if var.register is None:
                continue

            if var.io_type not in (IOType.WRITE, IOType.BOTH):
                continue

            if var_name not in self.variable_buffer:
                raise ValueError(f"Variable '{var_name}' not found in variable buffer.")

            value = self.variable_buffer[var_name]
            if var.scale is not None:
                value = value / var.scale

            if var.data_type in (DataType.int16, DataType.int32, DataType.int64):
                self.modbus_manager.set_int(var.register, int(value))
            elif var.data_type in (DataType.uint16, DataType.uint32, DataType.uint64):
                self.modbus_manager.set_uint(var.register, int(value))
            elif var.data_type in (DataType.float32, DataType.float64):
                self.modbus_manager.set_float(var.register, float(value))
            elif var.data_type == DataType.bool:
                self.modbus_manager.set_bool(var.register, bool(value))
            else:
                raise ValueError(f"Unsupported data type: {var.data_type}")

        self.modbus_manager.do_write()

    def get_variable_value(self, variable_name: str) -> Any:
        return self.variable_buffer[variable_name]

    def set_variable_value(self, variable_name: str, value: Any) -> None:
        self.variable_buffer[variable_name] = value

    def update_variable_buffer(self, vars: dict[str, Any]) -> None:
        for var_name, value in vars.items():
            self.set_variable_value(var_name, value)

    def get_all_mosaik_persistent_variables(self) -> dict[str, Any]:
        result = {}
        for var_name in self.config.get_mosaik_persistent_variables():
            result[var_name] = self.get_variable_value(var_name)
        return result
