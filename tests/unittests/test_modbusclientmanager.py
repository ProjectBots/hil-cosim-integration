from unittest import TestCase
from unittest.mock import MagicMock
from modbushil.modbusclientmanager import ModbusClientManager
from modbushil.modbusiobundlesconfiguration import ModbusIOBundlesConfiguration
from modbushil.modbusregistertypes import ModbusRegisterTypes
from modbushil.registerrange import RegisterRange


class TestModbusClientManager(TestCase):
    def test_connect_calls_modbusclient_open(self):
        mock_client = MagicMock()
        mock_client.is_open = False
        manager = ModbusClientManager(
            "localhost", 502, MagicMock(), modbus_client=mock_client
        )

        manager.connect()

        mock_client.open.assert_called_once()

    def test_connect_does_not_call_open_if_already_connected(self):
        mock_client = MagicMock()
        mock_client.is_open = True
        manager = ModbusClientManager(
            "localhost", 502, MagicMock(), modbus_client=mock_client
        )

        manager.connect()

        mock_client.open.assert_not_called()

    def test_disconnect_calls_modbusclient_close(self):
        mock_client = MagicMock()
        mock_client.is_open = True
        manager = ModbusClientManager(
            "localhost", 502, MagicMock(), modbus_client=mock_client
        )

        manager.disconnect()

        mock_client.close.assert_called_once()

    def test_disconnect_does_not_call_close_if_already_disconnected(self):
        mock_client = MagicMock()
        mock_client.is_open = False
        manager = ModbusClientManager(
            "localhost", 502, MagicMock(), modbus_client=mock_client
        )

        manager.disconnect()

        mock_client.close.assert_not_called()

    def test_read_holding_registers(self):
        mock_client = MagicMock()
        mock_client.read_holding_registers.return_value = [1, 2, 3, 4, 5]

        io_config = ModbusIOBundlesConfiguration(
            {"read": {"holding_register": ["0-4"]}, "write": {}}
        )

        manager = ModbusClientManager(
            "localhost", 502, io_config, modbus_client=mock_client
        )

        manager.do_read()

        mock_client.read_holding_registers.assert_called_once_with(0, 5)
        self.assertEqual(
            manager.buffer_register_read[ModbusRegisterTypes.HOLDING_REGISTER][0],
            [1, 2, 3, 4, 5],
        )

    def test_write_holding_registers(self):
        mock_client = MagicMock()

        io_config = ModbusIOBundlesConfiguration(
            {"read": {}, "write": {"holding_register": ["10-14"]}}
        )

        manager = ModbusClientManager(
            "localhost", 502, io_config, modbus_client=mock_client
        )
        manager.buffer_register_write[ModbusRegisterTypes.HOLDING_REGISTER][10] = [
            10,
            20,
            30,
            40,
            50,
        ]

        manager.do_write()

        mock_client.write_multiple_registers.assert_called_once_with(
            10, [10, 20, 30, 40, 50]
        )

    def test_get_registers(self):
        mock_client = MagicMock()

        io_config = ModbusIOBundlesConfiguration({"read": {}, "write": {}})

        manager = ModbusClientManager(
            "localhost", 502, io_config, modbus_client=mock_client
        )
        manager.buffer_register_read[ModbusRegisterTypes.HOLDING_REGISTER][5] = [
            100,
            200,
            300,
            400,
            500,
        ]

        buffer = manager.get_registers(
            RegisterRange(5, 3, ModbusRegisterTypes.HOLDING_REGISTER)
        )

        self.assertEqual(buffer, [100, 200, 300])

    def test_set_registers(self):
        mock_client = MagicMock()

        io_config = ModbusIOBundlesConfiguration(
            {
                "read": {},
                "write": {"holding_register": ["8-11"]},
            }
        )

        manager = ModbusClientManager(
            "localhost", 502, io_config, modbus_client=mock_client
        )
        manager.set_registers(
            RegisterRange(8, 4, ModbusRegisterTypes.HOLDING_REGISTER), [7, 14, 21, 28]
        )

        self.assertEqual(
            manager.buffer_register_write[ModbusRegisterTypes.HOLDING_REGISTER][8],
            [7, 14, 21, 28],
        )
