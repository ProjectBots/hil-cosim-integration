# server is the battery system
# slightly modified :https://github.com/Johannes4Linux/Simple-ModbusTCP-Server/blob/master/Simple_ModbusServer.py

from pyModbusTCP.server import ModbusServer
from time import sleep
# from random import uniform
import csv

metadata = []

with open('modbus/modbus_metadata.csv', mode='r', newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        metadata.append(row)


def scale_value(value, address):
    for row in metadata:
        if int(row['Address']) == address:
            scalefactor = float(row['Scalefactor'])
            return value * scalefactor
    raise ValueError(f"Address {address} not found in metadata")


server = ModbusServer("127.0.0.1", 12345, no_block=True)
VOLTAGE = 51.2
AMPERAGE = 100.0
POWER = VOLTAGE * AMPERAGE
STATE_OF_CHARGE = 90.0
STATE = 1   # 0=idle;1=charging;2=discharging
CONSUMED_AMPHOURS = 10.0
TIME_TO_GO = 3240


try:
    print("Starting Modbus Battery Server...")
    server.start()
    print("Server is online")

    server.data_bank.set_input_registers(840, [
        scale_value(VOLTAGE, 840),
        scale_value(AMPERAGE, 841),
        scale_value(POWER, 842),
        scale_value(STATE_OF_CHARGE, 843),
        scale_value(STATE, 844),
        scale_value(CONSUMED_AMPHOURS, 845),
        scale_value(TIME_TO_GO, 846),
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
