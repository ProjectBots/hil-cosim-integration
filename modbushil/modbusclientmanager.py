from pyModbusTCP.client import ModbusClient
from typing import cast

from modbushil.modbusiobundlesconfiguration import ModbusIOBundlesConfiguration
from modbushil.registerrange import RegisterRange

from .modbusregistertypes import ModbusRegisterTypes

import modbushil.registerhelpers as rh


class ModbusClientManager:
    def __init__(
        self,
        host: str,
        port: int,
        io_config: ModbusIOBundlesConfiguration,
        modbus_client: ModbusClient | None = None,
    ):
        self.client = (
            modbus_client
            if modbus_client is not None
            else ModbusClient(host=host, port=port)
        )
        self.io_config = io_config
        self.buffer_register: dict[ModbusRegisterTypes, dict[int, list[int]]] = {}
        self.buffer_discrete: dict[ModbusRegisterTypes, dict[int, list[bool]]] = {}

        for reg_type in ModbusRegisterTypes:
            self.buffer_register[reg_type] = {}
            self.buffer_discrete[reg_type] = {}

            for reg_range in self.io_config.read_ranges[reg_type] + self.io_config.write_ranges[reg_type]:
                if reg_type in (
                    ModbusRegisterTypes.COIL,
                    ModbusRegisterTypes.DISCRETE_INPUT,
                ):
                    self.buffer_discrete[reg_type][reg_range.start] = [
                        False
                    ] * reg_range.length
                else:
                    self.buffer_register[reg_type][reg_range.start] = [
                        0
                    ] * reg_range.length

    def connect(self):
        if not self.client.is_open:
            self.client.open()

    def disconnect(self):
        if self.client.is_open:
            self.client.close()

    def read_registers(self):
        """
        Reads the configured registers from the Modbus server and updates the internal buffers.

        :param self: The ModbusInterface instance
        :type self: ModbusInterface
        """
        self.connect()
        for reg_type, ranges in self.io_config.read_ranges.items():
            for i, reg_range in enumerate(ranges):
                if reg_type == ModbusRegisterTypes.COIL:
                    regs = self.client.read_coils(reg_range.start, reg_range.length)
                elif reg_type == ModbusRegisterTypes.DISCRETE_INPUT:
                    regs = self.client.read_discrete_inputs(
                        reg_range.start, reg_range.length
                    )
                elif reg_type == ModbusRegisterTypes.HOLDING_REGISTER:
                    regs = self.client.read_holding_registers(
                        reg_range.start, reg_range.length
                    )
                elif reg_type == ModbusRegisterTypes.INPUT_REGISTER:
                    regs = self.client.read_input_registers(
                        reg_range.start, reg_range.length
                    )
                else:
                    raise ValueError(f"Unsupported register type: {reg_type}")

                if regs is None or len(regs) < reg_range.length:
                    raise ConnectionError(
                        f"Failed to read {reg_type.name} registers from Modbus server"
                    )

                if reg_type in (
                    ModbusRegisterTypes.COIL,
                    ModbusRegisterTypes.DISCRETE_INPUT,
                ):
                    self.buffer_discrete[reg_type][reg_range.start] = cast(
                        list[bool], regs
                    )  # discrete inputs are bools
                else:
                    self.buffer_register[reg_type][reg_range.start] = cast(
                        list[int], regs
                    )  # registers are ints

    def write_registers(self):
        """
        Writes the configured registers to the Modbus server from the internal buffers.

        Any changes made to the internal buffers which are not in the write ranges will be ignored.

        :param self: The ModbusInterface instance
        :type self: ModbusInterface
        """
        # TODO: optimize by only writing changed registers
        self.connect()
        for reg_type, ranges in self.io_config.write_ranges.items():
            for i, reg_range in enumerate(ranges):
                if reg_type in (
                    ModbusRegisterTypes.COIL,
                    ModbusRegisterTypes.DISCRETE_INPUT,
                ):
                    values = self.buffer_discrete[reg_type][reg_range.start]
                else:
                    values = self.buffer_register[reg_type][reg_range.start]

                if reg_type == ModbusRegisterTypes.COIL:
                    success = self.client.write_multiple_coils(reg_range.start, values)
                elif reg_type == ModbusRegisterTypes.HOLDING_REGISTER:
                    success = self.client.write_multiple_registers(
                        reg_range.start, values
                    )
                else:
                    raise ValueError(
                        f"Unsupported register type for writing: {reg_type}"
                    )

                if not success:
                    raise ConnectionError(
                        f"Failed to write {reg_type.name} registers to Modbus server"
                    )

    def get_registers(self, address: RegisterRange) -> list[int]:
        """
        Gets a list of integer values from the internal buffer for the specified register type, starting address, and length.

        :param self: The ModbusInterface instance
        :type self: ModbusInterface
        :param reg_type: The register type
        :type reg_type: ModbusRegisterTypes
        :param start: The starting register address
        :type start: int
        :param length: The number of registers to get
        :type length: int
        :return: The list of integer values at the specified register addresses
        :rtype: list[int]
        """
        for range_start, regs in self.buffer_register[address.type].items():
            if range_start <= address.start < range_start + len(regs):
                if address.start + address.length <= range_start + len(regs):
                    return regs[
                        address.start - range_start : address.start
                        - range_start
                        + address.length
                    ]
                else:
                    raise ValueError(
                        f"Requested length exceeds buffer for {address.type.name} starting at {address.start}"
                    )
        raise ValueError(
            f"Start address {address.start} not in buffer for {address.type.name}"
        )

    def set_registers(self, address: RegisterRange, values: list[int]):
        """
        Sets a list of integer values in the internal buffer for the specified register type, starting address, and length.

        There is no range checking on the values, it is assumed that the values fit in the specified register type.

        To actually write the values to the Modbus server, call :func:`write_registers` afterwards.

        :param self: The ModbusInterface instance
        :type self: ModbusInterface
        :param reg_type: The register type
        :type reg_type: ModbusRegisterTypes
        :param start: The starting register address
        :type start: int
        :param values: The list of integer values to set at the specified register addresses
        :type values: list[int]
        """
        for range_start, regs in self.buffer_register[address.type].items():
            if range_start <= address.start < range_start + len(regs):
                if address.start + len(values) <= range_start + len(regs):
                    regs[
                        address.start - range_start : address.start
                        - range_start
                        + len(values)
                    ] = [v & 0xFFFF for v in values]
                    return
                else:
                    raise ValueError(
                        f"Values exceed buffer for {address.type.name} starting at {address.start}"
                    )
        raise ValueError(
            f"Start address {address.start} not in buffer for {address.type.name}"
        )

    def get_int(self, address: RegisterRange) -> int:
        """
        Gets an integer value from the internal buffer for the specified register range.

        The data type is a signed integer. The size is determined by the length of the register range.

        :param self: The ModbusInterface instance
        :type self: ModbusInterface
        :param address: The register range
        :type address: RegisterRange
        :return: The integer value at the specified register address
        :rtype: int
        """

        regs = self.get_registers(address)
        return rh.register_to_int(regs)

    def set_int(self, address: RegisterRange, value: int):
        """
        Sets an integer value in the internal buffer for the specified register range.

        The data type is a signed integer. The size is determined by the length of the register range.

        There is no range checking on the value, it is assumed to fit in the specified register range.

        To actually write the value to the Modbus server, call :func:`write_registers` afterwards.

        :param self: The ModbusInterface instance
        :param address: The register range
        :type address: RegisterRange
        :param value: The integer value to set at the specified register address
        :type value: int
        """

        regs = rh.int_to_register(value, address.length)
        self.set_registers(address, regs)

    def get_uint(self, address: RegisterRange) -> int:
        """
        Gets an unsigned integer value from the internal buffer for the specified register range.

        The data type is an unsigned integer. The size is determined by the length of the register range.

        :param self: The ModbusInterface instance
        :type self: ModbusInterface
        :param address: The register range
        :type address: RegisterRange
        :return: The unsigned integer value at the specified register address
        :rtype: int
        """

        regs = self.get_registers(address)
        return rh.register_to_uint(regs)

    def set_uint(self, address: RegisterRange, value: int):
        """
        Sets an unsigned integer value in the internal buffer for the specified register range.

        The data type is an unsigned integer. The size is determined by the length of the register range.

        There is no range checking on the value, it is assumed to fit in the specified register range.

        To actually write the value to the Modbus server, call :func:`write_registers` afterwards.

        :param self: The ModbusInterface instance
        :param address: The register range
        :type address: RegisterRange
        :param value: The unsigned integer value to set at the specified register address
        :type value: int
        """

        regs = rh.uint_to_register(value, address.length)
        self.set_registers(address, regs)

    def get_float(self, address: RegisterRange) -> float:
        """
        Gets a float/double value from the internal buffer for the specified register range.

        The data type is float32 for length 2 and float64 for length 4.

        :param self: The ModbusInterface instance
        :type self: ModbusInterface
        :param address: The register range
        :type address: RegisterRange
        :return: The float/double value at the specified register address
        :rtype: float
        """

        regs = self.get_registers(address)
        return rh.register_to_float(regs)

    def set_float(self, address: RegisterRange, value: float):
        """
        Sets a float/double value in the internal buffer for the specified register range.

        The data type is float32 for length 2 and float64 for length 4.

        There is no range checking on the value, it is assumed to fit in the specified register range.

        To actually write the value to the Modbus server, call :func:`write_registers` afterwards.

        :param self: The ModbusInterface instance
        :param address: The register range
        :type address: RegisterRange
        :param value: The float/double value to set at the specified register address
        :type value: float
        """

        regs = rh.float_to_register(value, address.length)
        self.set_registers(address, regs)
