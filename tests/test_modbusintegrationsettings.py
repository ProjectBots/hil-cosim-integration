from unittest import TestCase

from modbushil.modbusintegrationsettings import ModbusIntegrationSettings


class TestModbusIntegrationSettings(TestCase):
    def test_check_validity_success(self):
        config = {
            "modbus_io_bundles": {
                "read": {"holding_register": ["0-10"]},
                "write": {"holding_register": ["20-30"]},
            },
            "variables": {
                "var1": {
                    "data_type": "int",
                    "register": "H0",
                    "io_type": "read",
                    "mosaik": True,
                },
                "var2": {
                    "data_type": "int",
                    "register": "H5",
                    "io_type": "read",
                    "mosaik": False,
                },
                "var3": {
                    "data_type": "int",
                    "register": "H25",
                    "io_type": "write",
                    "mosaik": True,
                },
            },
            "methods": {
                "read": [
                    {
                        "set": "var4",
                        "action": "eval",
                        "expression": "$(var1) + 10",
                    }
                ]
            },
        }
        settings = ModbusIntegrationSettings(config)
        settings.check_validity()  # Should not raise any exception

    def test_check_validity_failure_outside_range(self):
        config = {
            "modbus_io_bundles": {
                "read": {"holding_register": ["0-10"]},
                "write": {"holding_register": ["20-30"]},
            },
            "variables": {
                "var1": {
                    "data_type": "int",
                    "register": "H15",
                    "io_type": "read",
                    "mosaik": True,
                },
            },
        }
        settings = ModbusIntegrationSettings(config)
        with self.assertRaises(ValueError) as context:
            settings.check_validity()
        self.assertIn("is mapped to register", str(context.exception))

    def test_check_validity_failure_invalid_method_variable(self):
        config = {
            "modbus_io_bundles": {
                "read": {"holding_register": ["0-10"]},
                "write": {"holding_register": ["20-30"]},
            },
            "variables": {},
            "methods": {
                "read": [
                    {
                        "set": "var2",
                        "action": "eval",
                        "expression": "$(var3) + 10",
                    }
                ]
            },
        }
        settings = ModbusIntegrationSettings(config)
        with self.assertRaises(ValueError) as context:
            settings.check_validity()
        self.assertIn(
            "requires variable 'var3' which is not valid", str(context.exception)
        )

    def test_check_validity_failure_mosaik_variable_invalid(self):
        config = {
            "modbus_io_bundles": {
                "read": {"holding_register": ["0-10"]},
                "write": {"holding_register": ["20-30"]},
            },
            "variables": {
                "var1": {
                    "data_type": "int",
                    "io_type": "read",
                    "mosaik": True,
                },
            },
        }
        settings = ModbusIntegrationSettings(config)
        with self.assertRaises(ValueError) as context:
            settings.check_validity()
        self.assertIn(
            "is marked for Mosaik but is not valid in read cycle",
            str(context.exception),
        )
