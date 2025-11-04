import mosaik_api_v3

import simulators.batterymetainfo as batterymetainfo


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

    def create(self, num, model, e_max_mwh):
        if num != 1:
            raise ValueError("BatteryModelRT only supports creating one instance at a time")
        self.created = True
        self.entity = { 
            "P_out[MW]": 0.0,
            "E_max[MWH]": e_max_mwh,
            "E[MWH]": 0.0,
        }
        return [{"eid": self.eid, "type": model}]

    def step(self, time, inputs, max_advance):
        # TODO: implement communication with real battery hardware
        return time + self.step_size
    
    def get_data(self, outputs):
        data = {}
        for eid, attrs in outputs.items():
            data[eid] = {
                "P_load[MW]": max(0.0, self.entity["P_out[MW]"]),
				"P_gen[MW]": max(0.0, -self.entity["P_out[MW]"]),
                "SoC": self.entity["E[MWH]"]
                / self.entity["E_max[MWH]"],
            }

        return data
