
from unittest import TestCase

import modbushil.registerrange as rr

class TestRegisterRange(TestCase):
	def test_contains_range(self):
		range1 = rr.RegisterRange(0, 10, rr.ModbusRegisterTypes.COIL)
		range2 = rr.RegisterRange(2, 5, rr.ModbusRegisterTypes.COIL)
		range3 = rr.RegisterRange(5, 10, rr.ModbusRegisterTypes.COIL)
		range4 = rr.RegisterRange(0, 10, rr.ModbusRegisterTypes.HOLDING_REGISTER)

		self.assertTrue(range1.contains_range(range2))
		self.assertFalse(range1.contains_range(range3))
		self.assertFalse(range1.contains_range(range4))

	def test_parse_registerrange(self):
		cases = [
			("C0-10", rr.RegisterRange(0, 11, rr.ModbusRegisterTypes.COIL)),
			("D5", rr.RegisterRange(5, 1, rr.ModbusRegisterTypes.DISCRETE_INPUT)),
			("h100-200", rr.RegisterRange(100, 101, rr.ModbusRegisterTypes.HOLDING_REGISTER)),
			("I50", rr.RegisterRange(50, 1, rr.ModbusRegisterTypes.INPUT_REGISTER)),
			("0-10", rr.RegisterRange(0, 11, rr.ModbusRegisterTypes.HOLDING_REGISTER), rr.ModbusRegisterTypes.HOLDING_REGISTER),
			("i5", rr.RegisterRange(5, 1, rr.ModbusRegisterTypes.HOLDING_REGISTER), rr.ModbusRegisterTypes.HOLDING_REGISTER),
		]

		for case in cases:
			if len(case) == 2:
				range_str, expected = case
				result = rr.RegisterRange.parse_registerrange(range_str, None)
			else:
				range_str, expected, reg_type_override = case
				result = rr.RegisterRange.parse_registerrange(range_str, reg_type_override)

			self.assertEqual(result.start, expected.start)
			self.assertEqual(result.length, expected.length)
			self.assertEqual(result.type, expected.type)