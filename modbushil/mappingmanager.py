from modbusclientmanager import ModbusClientManager
from modbusintegrationsettings import ModbusIntegrationSettings
from variablemapping import VariableMapping
from iotype import IOType
from typing import Any
from datatype import DataType


class MappingManager:
    def __init__(self, config: ModbusIntegrationSettings, host: str, port: int):
        config.check_validity()

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

    def read_cycle(self) -> None:
        self.modbus_manager.read_registers()

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
            else:
                raise ValueError(f"Unsupported data type: {var.data_type}")

            if var.scale != 1.0:
                value = value * var.scale
                if var.data_type in (
                    DataType.int16,
                    DataType.int32,
                    DataType.int64,
                    DataType.uint16,
                    DataType.uint32,
                    DataType.uint64,
                ):
                    value = int(value)

            self.variable_buffer[var_name] = value

        # read methods
        for method in self.config.read_methods:
            result = method.invoke(self.variable_buffer)
            self.variable_buffer[method.variable] = result

    def write_cycle(self) -> None:
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
            if var.scale != 1.0:
                value = value / var.scale
                if var.data_type in (
                    DataType.int16,
                    DataType.int32,
                    DataType.int64,
                    DataType.uint16,
                    DataType.uint32,
                    DataType.uint64,
                ):
                    value = int(value)

            if var.data_type in (DataType.int16, DataType.int32, DataType.int64):
                self.modbus_manager.set_int(var.register, int(value))
            elif var.data_type in (DataType.uint16, DataType.uint32, DataType.uint64):
                self.modbus_manager.set_uint(var.register, int(value))
            elif var.data_type in (DataType.float32, DataType.float64):
                self.modbus_manager.set_float(var.register, float(value))
            else:
                raise ValueError(f"Unsupported data type: {var.data_type}")

        self.modbus_manager.write_registers()

    def get_variable_value(self, variable_name: str) -> Any:
        return self.variable_buffer.get(variable_name, None)

    def set_variable_value(self, variable_name: str, value: Any) -> None:
        self.variable_buffer[variable_name] = value
