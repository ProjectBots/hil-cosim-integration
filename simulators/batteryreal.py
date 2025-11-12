import mosaik_api_v3

import simulators.batterymetainfo as batterymetainfo
from pyModbusTCP.client import ModbusClient
import csv

MAX_CHARGE_WH = 5120


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
    

class BatteryModel(mosaik_api_v3.Simulator):
    created: bool = False
    eid: str = "Real_Battery"
    entity: dict[str, float]
    step_size: int

    def __init__(self):
        super().__init__(batterymetainfo.BATTERY_MODEL_META_DATA)

    def init(self, sid, time_resolution, step_size):
        if time_resolution != 1.0:
            raise ValueError("BatteryModelRT only supports time_resolution of '1s'")
        self.step_size = step_size
        return self.meta

    def create(self, num, model, e_max_mwh, **kwargs):
        if num != 1:
            raise ValueError(
                "BatteryModelRT only supports creating one instance at a time"
            )
        self.created = True
        self.entity = {
            "P_out[MW]": 0.0,
            "E_max[MWH]": MAX_CHARGE_WH/1e6, #TODO were does this value come from, we need to adjust it, i replaced it temporarily e_max_mwh
            "E[MWH]": 0.0,
        }
        self.client, self.metadata = init_modbus_client()  # Initialize Modbus client
        return [{"eid": self.eid, "type": model}]

    def step(self, time, inputs, max_advance):
        P_load = sum(attrs["P_load[MW]"][-1] for attrs in inputs.values() if "P_load[MW]" in attrs)
        
        # values from modbus server
        try:
            real_energy = read_register(self.client, self.metadata, 843) * MAX_CHARGE_WH / 1e6
        except Exception as e:
            print("Modbus read error:", e)
            real_energy = 0.0

        self.entity["P_out[MW]"] = -P_load  # batterie compensates load TODO improve this i think
        self.entity["E[MWH]"] = real_energy

        return time + self.step_size

    def get_data(self, outputs):
        data = {}
        for eid, attrs in outputs.items():
            data[eid] = {
                "P_load[MW]": max(0.0, self.entity["P_out[MW]"]),
                "P_gen[MW]": max(0.0, -self.entity["P_out[MW]"]),
                "SoC": self.entity["E[MWH]"] / self.entity["E_max[MWH]"],
                "P[MW]": self.entity["P_out[MW]"],
            }

        return data
