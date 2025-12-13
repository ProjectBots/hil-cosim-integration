import enum

class ModbusRegisterTypes(enum.Enum):
    COIL = 1
    DISCRETE_INPUT = 2
    HOLDING_REGISTER = 3
    INPUT_REGISTER = 4
    
    def __str__(self) -> str:
        return self.name

    @staticmethod
    def parse_regtype(type_str: str) -> "ModbusRegisterTypes":
        type_str = type_str.upper()
        if type_str == "COIL" or type_str == "C":
            return ModbusRegisterTypes.COIL
        elif type_str == "DISCRETE_INPUT" or type_str == "D":
            return ModbusRegisterTypes.DISCRETE_INPUT
        elif type_str == "HOLDING_REGISTER" or type_str == "H":
            return ModbusRegisterTypes.HOLDING_REGISTER
        elif type_str == "INPUT_REGISTER" or type_str == "I":
            return ModbusRegisterTypes.INPUT_REGISTER
        else:
            raise ValueError(f"Invalid Modbus register type: {type_str}")