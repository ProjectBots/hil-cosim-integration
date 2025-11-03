# server is the battery system
# slightly modified :https://github.com/Johannes4Linux/Simple-ModbusTCP-Server/blob/master/Simple_ModbusServer.py

from pyModbusTCP.server import ModbusServer
from time import sleep
# from random import uniform

server = ModbusServer("127.0.0.1", 12345, no_block=True)
VOLTAGE = 51.2 * 10
AMPERAGE = 100.0 * 10
POWER = VOLTAGE * AMPERAGE
STATE_OF_CHARGE = 90.0
STATE = 1   # 0=idle;1=charging;2=discharging
CONSUMED_AMPHOURS = 10.0 * -10
TIME_TO_GO = 3240 * 0.01


try:
    print("Starting Modbus Battery Server...")
    server.start()
    print("Server is online")

    server.data_bank.set_holding_registers(840, [
        int(VOLTAGE),
        int(AMPERAGE),
        int(POWER),
        int(STATE_OF_CHARGE),
        int(STATE),
        int(CONSUMED_AMPHOURS),
        int(TIME_TO_GO)
    ])

    while True:
        # server.data_bank.set_holding_registers(0, [int(uniform(0, 2))])

        # # read register
        # reg1 = server.data_bank.get_holding_registers(0, 1)
        # print(f"Updated Register 0 to: {reg1[0]}")
        sleep(0.5)

except KeyboardInterrupt:
    print("Shutting down server...")
    server.stop()
    print("Server is offline")
