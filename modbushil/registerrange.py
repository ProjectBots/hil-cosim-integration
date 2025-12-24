from .modbusregistertypes import ModbusRegisterTypes


class RegisterRange:
    def __init__(self, start: int, length: int, reg_type: ModbusRegisterTypes):
        self.start: int = start
        self.length: int = length
        self.type: ModbusRegisterTypes = reg_type

    def __repr__(self) -> str:
        return (
            f"RegisterRange(start={self.start}, length={self.length}, type={self.type})"
        )

    def contains_range(self, other: "RegisterRange") -> bool:
        """
        Checks if this register range fully contains another register range.

        :param other: the other register range to check
        :type other: RegisterRange
        :return: True if this range contains the other range, False otherwise
        :rtype: bool
        """
        if self.type != other.type:
            return False
        return self.start <= other.start and (self.start + self.length) >= (
            other.start + other.length
        )

    @staticmethod
    def parse_registerrange(
        range_str: str, reg_type_override: ModbusRegisterTypes | None
    ) -> "RegisterRange":
        """
        Parses a register range string into a RegisterRange object.

        The register range string can be in the following formats:
        - "C0-10": Coils from address 0 to 10
        - "D5": Discrete Input at address 5
        - "H100-200": Holding Registers from address 100 to 200
        - "I50": Input Register at address 50
        - "0-10": Registers from address 0 to 10, with type specified by reg_type_override
        - "5": Register at address 5, with type specified by reg_type_override

        :param range_str: the register range string to parse
        :type range_str: str
        :param reg_type_override: Optional explicit register type to use when the string does not include a type prefix
        :type reg_type_override: ModbusRegisterTypes | None
        :return: the parsed RegisterRange
        :rtype: RegisterRange
        """
        if len(range_str) == 0:
            raise ValueError("Register range string is empty")
        fchar = range_str[0]

        reg_type = reg_type_override
        if not fchar.isdigit():
            if reg_type_override is None:
                reg_type = ModbusRegisterTypes.parse_regtype(fchar)
            range_str = range_str[1:]

        if reg_type is None:
            raise ValueError("Register type could not be determined")

        parts = range_str.split("-")
        part_count = len(parts)
        if part_count != 2 and part_count != 1:
            raise ValueError(f"Invalid register range format: {range_str}")
        try:
            start = int(parts[0])
            end = int(parts[1]) if part_count == 2 else start
        except ValueError:
            raise ValueError(f"Invalid register range numbers: {range_str}")

        if end < start:
            raise ValueError(f"End of register range must be >= start: {range_str}")

        length = end - start + 1

        return RegisterRange(start, length, reg_type)
