# client is our simulation

from pyModbusTCP.client import ModbusClient
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
            return value / scalefactor
    raise ValueError(f"Address {address} not found in metadata")


# create client instance
client = ModbusClient(host='127.0.0.1', port=12345)

FIRST_REGISTER_ADDRESS = 840
N_REGISTERS = 7

# connect to device
if client.open():
    result = client.read_input_registers(FIRST_REGISTER_ADDRESS, N_REGISTERS)
    if result:
        print("Register 0 value:", scale_value(result[3], FIRST_REGISTER_ADDRESS + 3)) 
    else:
        print("Read failed or no response")
    client.close()
else:
    print("Connection failed")