from pyModbusTCP.client import ModbusClient
import csv


def init_modbus_client(csv_path='modbus/modbus_metadata.csv', host='127.0.0.1', port=12345):
    metadata = []
    with open(csv_path, mode='r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            metadata.append(row)
    
    client = ModbusClient(host=host, port=port)
    
    return client, metadata


def scale_value(value, address, metadata):
    for row in metadata:
        if int(row['Address']) == address:
            scalefactor = float(row['Scalefactor'])
            return value / scalefactor
    raise ValueError(f"Address {address} not found in metadata")


def read_register(client, metadata, address):
    if client.open():
        result = client.read_input_registers(address, 1)
        client.close()
        if result:
            return scale_value(result[0], address, metadata)
        else:
            raise ConnectionError("Read failed or no response")
    else:
        raise ConnectionError("Connection failed")


client, metadata = init_modbus_client()
try:
    value = read_register(client, metadata, 843)
    print("Register 843 value:", value)
except Exception as e:
    print(e)
