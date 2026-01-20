from unittest import TestCase

import modbushil.registerhelpers as rh


class TestRegisterHelpers(TestCase):
    def test_int_to_register(self):
        cases = [
            (0x1234567890123456, 4, [0x3456, 0x9012, 0x5678, 0x1234]),
            (0x12345678, 2, [0x5678, 0x1234]),
            (0x1234, 1, [0x1234]),
            [-10, 2, [0xFFF6, 0xFFFF]],
        ]
        for value, num_registers, expected_regs in cases:
            with self.subTest(value=value, num_registers=num_registers):
                regs = rh.int_to_register(value, num_registers)
                self.assertEqual(regs, expected_regs)

    def test_register_to_int(self):
        cases = [
            ([0x5678, 0x1234], 0x12345678),
            ([0x1234], 0x1234),
            ([0xFFF6, 0xFFFF], -10),
        ]
        for regs, expected_value in cases:
            with self.subTest(regs=regs):
                value = rh.register_to_int(regs)
                self.assertEqual(value, expected_value)

    def test_float_to_register(self):
        cases = [
            (1234.5678, 2, [0x522b, 0x449a]),
            (1234.56789, 4, [0xc6e7, 0x84f4, 0x4a45, 0x4093]),
            (-12.34, 2, [0x70a4, 0xc145]),
        ]
        for value, num_registers, expected_regs in cases:
            with self.subTest(value=value):
                regs = rh.float_to_register(value, num_registers)
                self.assertEqual(regs, expected_regs)
    
    def test_register_to_float(self):
        cases = [
            ([0x522b, 0x449a], 1234.5678),
            ([0xc6e7, 0x84f4, 0x4a45, 0x4093], 1234.56789),
            ([0x70a4, 0xc145], -12.34),
        ]
        for regs, expected_value in cases:
            with self.subTest(regs=regs):
                value = rh.register_to_float(regs)
                self.assertAlmostEqual(value, expected_value, places=3)