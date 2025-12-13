from pyModbusTCP.client import ModbusClient
from typing import cast

from .modbusregistertypes import ModbusRegisterTypes
from .registerrange import RegisterRange

class ModbusClientManager:
    def __init__(
        self, host: str, port: int, io_config: dict[str, dict[str, list[str]]]
    ):
        self.client: ModbusClient = ModbusClient(host=host, port=port)
        self.read_ranges: dict[ModbusRegisterTypes, list[RegisterRange]] = {}
        self.write_ranges: dict[ModbusRegisterTypes, list[RegisterRange]] = {}
        self.buffer_register: dict[ModbusRegisterTypes, dict[int, list[int]]] = {}
        self.buffer_discrete: dict[ModbusRegisterTypes, dict[int, list[bool]]] = {}

        for reg_type in ModbusRegisterTypes:
            self.read_ranges[reg_type] = []
            self.write_ranges[reg_type] = []
            self.buffer_register[reg_type] = {}
            self.buffer_discrete[reg_type] = {}

        for direction, regs in io_config.items():
            for reg_type_str, reg_list in regs.items():
                reg_type = ModbusRegisterTypes.parse_regtype(reg_type_str)
                for reg_str in reg_list:
                    reg_range = RegisterRange.parse_registerrange(
                        reg_str,
                        reg_type_override=reg_type,
                    )

                    if direction == "read":
                        self.read_ranges[reg_type].append(reg_range)
                    elif direction == "write":
                        self.write_ranges[reg_type].append(reg_range)
                    else:
                        raise ValueError(f"Invalid IO config direction: {direction}")

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
        for reg_type, ranges in self.read_ranges.items():
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
        self.connect()
        for reg_type, ranges in self.write_ranges.items():
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

    def get_registers(
        self, reg_type: ModbusRegisterTypes, start: int, length: int
    ) -> list[int]:
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
        for range_start, regs in self.buffer_register[reg_type].items():
            if range_start <= start < range_start + len(regs):
                if start + length <= range_start + len(regs):
                    return regs[start - range_start : start - range_start + length]
                else:
                    raise ValueError(
                        f"Requested length exceeds buffer for {reg_type.name} starting at {start}"
                    )
        raise ValueError(f"Start address {start} not in buffer for {reg_type.name}")

    def set_registers(
        self, reg_type: ModbusRegisterTypes, start: int, values: list[int]
    ):
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
        for range_start, regs in self.buffer_register[reg_type].items():
            if range_start <= start < range_start + len(regs):
                if start + len(values) <= range_start + len(regs):
                    regs[start - range_start : start - range_start + len(values)] = [
                        v & 0xFFFF for v in values
                    ]
                    return
                else:
                    raise ValueError(
                        f"Values exceed buffer for {reg_type.name} starting at {start}"
                    )
        raise ValueError(f"Start address {start} not in buffer for {reg_type.name}")

    def get_uint16(self, reg_type: ModbusRegisterTypes, address: int) -> int:
        """
        Gets an unsigned 16-bit integer value from the internal buffer for the specified register type and address.

        :param self: The ModbusInterface instance
        :type self: ModbusInterface
        :param reg_type: The register type
        :type reg_type: ModbusRegisterTypes
        :param address: The register address
        :type address: int
        :return: The integer value at the specified register address
        :rtype: int
        """
        if reg_type in (ModbusRegisterTypes.COIL, ModbusRegisterTypes.DISCRETE_INPUT):
            raise ValueError(
                f"Cannot get integer value from discrete register type: {reg_type.name}"
            )

        regs = self.get_registers(reg_type, address, 1)
        if len(regs) != 1:
            raise ValueError(
                f"Failed to get register value at address {address} for {reg_type.name}"
            )

        return regs[0]

    def set_uint16(self, reg_type: ModbusRegisterTypes, address: int, value: int):
        """
        Sets an integer value in the internal buffer for the specified register type and address.

        There is no range checking on the value, it is assumed to be a 16-bit unsigned integer.

        To actually write the value to the Modbus server, call :func:`write_registers` afterwards.

        :param self: The ModbusInterface instance
        :param reg_type: The register type
        :type reg_type: ModbusRegisterTypes
        :param address: The register address
        :type address: int
        :param value: The integer value to set at the specified register address
        :type value: int
        """
        self.set_registers(reg_type, address, [value & 0xFFFF])

    def get_uint32(self, reg_type: ModbusRegisterTypes, address: int) -> int:
        """
        Gets a 32-bit integer value from the internal buffer for the specified register type and address.

        The value is constructed from two consecutive 16-bit registers, with the first register being the high word (big endian).

        :param self: The ModbusInterface instance
        :type self: ModbusInterface
        :param reg_type: The register type
        :type reg_type: ModbusRegisterTypes
        :param address: The starting register address (high word)
        :type address: int
        :return: The 32-bit integer value at the specified register address
        :rtype: int
        """
        regs = self.get_registers(reg_type, address, 2)
        if len(regs) != 2:
            raise ValueError(
                f"Failed to get 32-bit register value at address {address} for {reg_type.name}"
            )

        return (regs[0] << 16) | regs[1]

    def set_uint32(self, reg_type: ModbusRegisterTypes, address: int, value: int):
        """
        Sets a 32-bit integer value in the internal buffer for the specified register type and address.

        The value is split into two consecutive 16-bit registers, with the first register being the high word (big endian).

        There is no range checking on the value, it is assumed to be a 32-bit unsigned integer.

        To actually write the value to the Modbus server, call :func:`write_registers` afterwards.

        :param self: The ModbusInterface instance
        :param reg_type: The register type
        :type reg_type: ModbusRegisterTypes
        :param address: The starting register address (high word)
        :type address: int
        :param value: The 32-bit integer value to set at the specified register address
        :type value: int
        """
        if reg_type in (ModbusRegisterTypes.COIL, ModbusRegisterTypes.DISCRETE_INPUT):
            raise ValueError(
                f"Cannot set integer value in discrete register type: {reg_type.name}"
            )

        high_word = (value >> 16) & 0xFFFF
        low_word = value & 0xFFFF
        self.set_registers(reg_type, address, [high_word, low_word])

    def get_int16(self, reg_type: ModbusRegisterTypes, address: int) -> int:
        """
        Gets a signed 16-bit integer value from the internal buffer for the specified register type and address.

        :param self: The ModbusInterface instance
        :type self: ModbusInterface
        :param reg_type: The register type
        :type reg_type: ModbusRegisterTypes
        :param address: The register address
        :type address: int
        :return: The integer value at the specified register address
        :rtype: int
        """
        uint_value = self.get_uint16(reg_type, address)
        if uint_value >= 0x8000:
            return uint_value - 0x10000
        else:
            return uint_value

    def set_int16(self, reg_type: ModbusRegisterTypes, address: int, value: int):
        """
        Sets a signed 16-bit integer value in the internal buffer for the specified register type and address.

        The value is stored as an unsigned 16-bit integer in two's complement format.

        There is no range checking on the value, it is assumed to be a 16-bit signed integer.

        To actually write the value to the Modbus server, call :func:`write_registers` afterwards.

        :param self: The ModbusInterface instance
        :param reg_type: The register type
        :type reg_type: ModbusRegisterTypes
        :param address: The register address
        :type address: int
        :param value: The integer value to set at the specified register address
        :type value: int
        """

        if value < 0:
            uint_value = value + 0x10000
        else:
            uint_value = value

        self.set_registers(reg_type, address, [uint_value & 0xFFFF])

    def get_int32(self, reg_type: ModbusRegisterTypes, address: int) -> int:
        """
        Gets a signed 32-bit integer value from the internal buffer for the specified register type and address.

        The value is constructed from two consecutive 16-bit registers, with the first register being the high word (big endian).

        :param self: The ModbusInterface instance
        :type self: ModbusInterface
        :param reg_type: The register type
        :type reg_type: ModbusRegisterTypes
        :param address: The starting register address (high word)
        :type address: int
        :return: The 32-bit integer value at the specified register address
        :rtype: int
        """
        uint_value = self.get_uint32(reg_type, address)
        if uint_value >= 0x80000000:
            return uint_value - 0x100000000
        else:
            return uint_value

    def set_int32(self, reg_type: ModbusRegisterTypes, address: int, value: int):
        """
        Sets a signed 32-bit integer value in the internal buffer for the specified register type and address.

        The value is stored as an unsigned 32-bit integer in two's complement format.

        There is no range checking on the value, it is assumed to be a 32-bit signed integer.

        To actually write the value to the Modbus server, call :func:`write_registers` afterwards.

        :param self: The ModbusInterface instance
        :param reg_type: The register type
        :type reg_type: ModbusRegisterTypes
        :param address: The starting register address (high word)
        :type address: int
        :param value: The 32-bit integer value to set at the specified register address
        :type value: int
        """

        if value < 0:
            uint_value = value + 0x100000000
        else:
            uint_value = value

        self.set_uint32(reg_type, address, uint_value & 0xFFFFFFFF)

    # TODO: add more get_/set_ methods for other data types (float, bool, etc.)
    # TODO: outsource helper methods for data type conversions
