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
                    "datatype": "int",
                    "register": "H0",
                    "iotype": "read",
                    "mosaik": True,
                },
                "var2": {
                    "datatype": "int",
                    "register": "H5",
                    "iotype": "read",
                    "mosaik": False,
                },
                "var3": {
                    "datatype": "int",
                    "register": "H25",
                    "iotype": "write",
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
                    "datatype": "int",
                    "register": "H15",
                    "iotype": "read",
                    "mosaik": True,
                },
            },
        }
        with self.assertRaises(ValueError) as context:
            ModbusIntegrationSettings(config)
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
        with self.assertRaises(ValueError) as context:
            ModbusIntegrationSettings(config)
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
                    "datatype": "int",
                    "iotype": "read",
                    "mosaik": True,
                },
            },
        }
        with self.assertRaises(ValueError) as context:
            ModbusIntegrationSettings(config)
        self.assertIn(
            "is marked for Mosaik but is not valid in read cycle",
            str(context.exception),
        )
