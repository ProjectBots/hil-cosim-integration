from enum import Enum


class IOType(Enum):
    READ = "read"
    WRITE = "write"
    BOTH = "both"

    @classmethod
    def from_string(cls, s: str) -> "IOType":
        s_lower = s.lower()
        if s_lower == "read":
            return IOType.READ
        elif s_lower == "write":
            return IOType.WRITE
        elif s_lower == "both":
            return IOType.BOTH
        else:
            raise ValueError(f"Invalid IOType string: {s}")
