from typing import List
import struct

def register_to_int(regs: List[int]) -> int:
	"""Convert a list of Modbus register values to a single integer.

	:param regs: List of Modbus register values (16-bit unsigned integers)
	:type regs: List[int]
	:return: The combined integer value
	:rtype: int
	"""
	result = 0
	for i, reg in enumerate(regs):
		result |= (reg & 0xFFFF) << (16 * i)
	# account for signage (two's complement)
	total_bits = 16 * len(regs)
	sign_bit = 1 << (total_bits - 1)
	if result & sign_bit:
		result -= 1 << total_bits
	return result

def int_to_register(value: int, num_registers: int) -> List[int]:
	"""Convert an integer to a list of Modbus register values.

	:param value: The integer value to convert
	:type value: int
	:param num_registers: The number of Modbus registers to use for the conversion
	:type num_registers: int
	:return: List of Modbus register values (16-bit unsigned integers)
	:rtype: List[int]
	"""
	mask = (1 << (16 * num_registers)) - 1
	value &= mask
	regs = []
	for i in range(num_registers):
		regs.append((value >> (16 * i)) & 0xFFFF)
	return regs

def register_to_uint(regs: List[int]) -> int:
	"""Convert a list of Modbus register values to a single unsigned integer.

	:param regs: List of Modbus register values (16-bit unsigned integers)
	:type regs: List[int]
	:return: The combined unsigned integer value
	:rtype: int
	"""
	result = 0
	for i, reg in enumerate(regs):
		result |= (reg & 0xFFFF) << (16 * i)
	return result

def uint_to_register(value: int, num_registers: int) -> List[int]:
	"""Convert an unsigned integer to a list of Modbus register values.

	:param value: The unsigned integer value to convert
	:type value: int
	:param num_registers: The number of Modbus registers to use for the conversion
	:type num_registers: int
	:return: List of Modbus register values (16-bit unsigned integers)
	:rtype: List[int]
	"""
	regs = []
	for i in range(num_registers):
		reg = (value >> (16 * i)) & 0xFFFF
		regs.append(reg)
	return regs

def register_to_float(regs: List[int]) -> float:
	"""Convert a list of Modbus register values to a single float or double.

	:param regs: List of Modbus register values (16-bit unsigned integers)
	:type regs: List[int]
	:return: The combined float/double value
	:rtype: float
	"""
	if len(regs) == 2:
		int_value = register_to_int(regs) & 0xFFFFFFFF
		return struct.unpack('<f', struct.pack('<I', int_value))[0]
	elif len(regs) == 4:
		int_value = register_to_int(regs) & 0xFFFFFFFFFFFFFFFF
		return struct.unpack('<d', struct.pack('<Q', int_value))[0]
	else:
		raise ValueError("register_to_float requires 2 (float32) or 4 (float64) registers")

def float_to_register(value: float, num_registers: int) -> List[int]:
	"""Convert a float to a list of Modbus register values.

	:param value: The float value to convert
	:type value: float
	:param num_registers: The number of Modbus registers to use for the conversion (2 for float32, 4 for float64)
	:type num_registers: int
	:return: List of Modbus register values (16-bit unsigned integers)
	:rtype: List[int]
	"""
	if num_registers == 2:
		int_value = struct.unpack('<I', struct.pack('<f', value))[0]
		return int_to_register(int_value, num_registers)
	elif num_registers == 4:
		int_value = struct.unpack('<Q', struct.pack('<d', value))[0]
		return int_to_register(int_value, num_registers)
	else:
		raise ValueError("float_to_register requires num_registers 2 (float32) or 4 (float64)")