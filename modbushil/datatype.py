from enum import Enum


class DataType(Enum):
    uint16 = "uint16"
    int16 = "int16"
    uint32 = "uint32"
    int32 = "int32"
    uint64 = "uint64"
    int64 = "int64"
    float32 = "float32"
    float64 = "float64"
    # string = "string"   #TODO: implement string

    @classmethod
    def from_string(cls, s: str) -> "DataType":
        s_lower = s.lower()
        if s_lower == "uint16" or s_lower == "ushort":
            return DataType.uint16
        elif s_lower == "int16" or s_lower == "short":
            return DataType.int16
        elif s_lower == "uint32" or s_lower == "uint":
            return DataType.uint32
        elif s_lower == "int32" or s_lower == "int":
            return DataType.int32
        elif s_lower == "float32" or s_lower == "float":
            return DataType.float32
        elif s_lower == "float64" or s_lower == "double":
            return DataType.float64
        #elif s_lower == "string": # TODO: uncomment when implemented
        #    return DataType.string
        else:
            raise ValueError(f"Invalid DataType string: {s}")
