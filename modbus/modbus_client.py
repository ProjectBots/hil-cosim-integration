# client is our simulation

from pyModbusTCP.client import ModbusClient

# create client instance
client = ModbusClient(host='127.0.0.1', port=12345)

FIRST_REGISTER_ADDRESS = 840
N_REGISTERS = 7

# connect to device
if client.open():
    # read 1 holding register starting at address 0
    result = client.read_holding_registers(840, 7)
    if result:
        print("Register 0 value:", result[6])
    else:
        print("Read failed or no response")
    client.close()
else:
    print("Connection failed")