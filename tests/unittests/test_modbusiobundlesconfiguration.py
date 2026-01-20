from unittest import TestCase

import modbushil.modbusiobundlesconfiguration as mbc
import modbushil.registerrange as rr


class TestModbusIOBundlesConfiguration(TestCase):
    def test_io_bundles_parsing(self):
        config = {
            "read": {"holding_register": ["0-10", "20-30"], "coil": ["0-5"]},
            "write": {"holding_register": ["100-110"], "discrete_input": ["0-3"]},
        }
        io_bundles = mbc.ModbusIOBundlesConfiguration(config)

        self.assertEqual(
            len(io_bundles.read_ranges[rr.ModbusRegisterTypes.HOLDING_REGISTER]), 2
        )
        self.assertEqual(len(io_bundles.read_ranges[rr.ModbusRegisterTypes.COIL]), 1)
        self.assertEqual(
            len(io_bundles.write_ranges[rr.ModbusRegisterTypes.HOLDING_REGISTER]), 1
        )
        self.assertEqual(
            len(io_bundles.write_ranges[rr.ModbusRegisterTypes.DISCRETE_INPUT]), 1
        )

    def test_has_read_range(self):
        config = {"read": {"holding_register": ["H0-10"]}, "write": {}}
        io_bundles = mbc.ModbusIOBundlesConfiguration(config)

        test_range = rr.RegisterRange(2, 5, rr.ModbusRegisterTypes.HOLDING_REGISTER)
        self.assertTrue(io_bundles.has_read_range(test_range))

        test_range_outside = rr.RegisterRange(
            11, 5, rr.ModbusRegisterTypes.HOLDING_REGISTER
        )
        self.assertFalse(io_bundles.has_read_range(test_range_outside))
