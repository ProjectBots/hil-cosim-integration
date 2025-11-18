import mosaik_api_v3

import simulators.batterymetainfo as batterymetainfo
import helperutils as hu


class BatteryModel(mosaik_api_v3.Simulator):
    time_resolution: float # TODO: fix time resolution not affecting power calculations
    entities: dict[str, dict[str, float]]
    step_size: int

    def __init__(self):
        super().__init__(batterymetainfo.BATTERY_MODEL_META_DATA)
        self.entities = {}

    def init(self, sid, time_resolution, step_size):
        self.time_resolution = time_resolution
        self.step_size = step_size
        return self.meta

    def create(self, num, model, e_max_mwh, p_max_gen_mw, p_max_load_mw):
        entities = []
        for i in range(num):
            eid = f"{model}_{len(self.entities)}"
            self.entities[eid] = {
                "P_out[MW]": 0.0,
                "E_max[MWH]": e_max_mwh,
                "E[MWH]": e_max_mwh / 2.0,  # start at 50% SOC
                "P_max_gen[MW]": p_max_gen_mw,
                "P_max_load[MW]": p_max_load_mw,
            }
            entities.append({"eid": eid, "type": model})
        return entities

    def step(self, time, inputs, max_advance):
        for eid, attrs in inputs.items():

            p_out = self.entities[eid]["P_out[MW]"]

            charge_level = self.entities[eid]["E[MWH]"]
            charge_level -= p_out * (self.step_size / 3600.0)
            charge_level = hu.clamp(charge_level, 0.0, self.entities[eid]["E_max[MWH]"])

            p_target = sum(attrs["P_target[MW]"].values())

            if charge_level < 1e-6 and p_target > 0.0:
                self.entities[eid]["P_out[MW]"] = 0.0  # Prevent discharging when empty
            elif charge_level > self.entities[eid]["E_max[MWH]"] - 1e-6 and p_target < 0.0:
                self.entities[eid]["P_out[MW]"] = 0.0  # Prevent charging when full
            else:
                self.entities[eid]["P_out[MW]"] = hu.clamp(
                    p_target,
                    -self.entities[eid]["P_max_gen[MW]"],
                    self.entities[eid]["P_max_load[MW]"],
                )
            self.entities[eid]["E[MWH]"] = charge_level
            
        return time + self.step_size

    def get_data(self, outputs):
        data = {}
        for eid, attrs in outputs.items():
            data[eid] = {
                "P_load[MW]": max(0.0, self.entities[eid]["P_out[MW]"]),
                "P_gen[MW]": max(0.0, -self.entities[eid]["P_out[MW]"]),
                "SoC": self.entities[eid]["E[MWH]"] / self.entities[eid]["E_max[MWH]"],
                "P[MW]": self.entities[eid]["P_out[MW]"],
            }

        return data
