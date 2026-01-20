
from .modbusregistertypes import ModbusRegisterTypes
from .registerrange import RegisterRange


class ModbusIOBundlesConfiguration():
    def __init__(
        self, io_config: dict[str, dict[str, list[str]]]
    ):
        self.read_ranges: dict[ModbusRegisterTypes, list[RegisterRange]] = {}
        self.write_ranges: dict[ModbusRegisterTypes, list[RegisterRange]] = {}

        for reg_type in ModbusRegisterTypes:
            self.read_ranges[reg_type] = []
            self.write_ranges[reg_type] = []

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

                    
    
    def has_read_range(self, reg_range: RegisterRange) -> bool:
        for existing_range in self.read_ranges[reg_range.type]:
            if existing_range.contains_range(reg_range):
                return True
        return False
    
    def has_write_range(self, reg_range: RegisterRange) -> bool:
        for existing_range in self.write_ranges[reg_range.type]:
            if existing_range.contains_range(reg_range):
                return True
        return False