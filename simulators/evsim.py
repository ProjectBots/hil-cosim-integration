import mosaik_api_v3
import random as rnd
import helperutils as hu


META = {
    "api_version": "3.0",
    "type": "time-based",
    "models": {
        "EVModel": {
            "public": True,
            "params": ["p_charge_mw"],
            "non-trigger": [],
            "persistent": ["E[MWH]", "P_load[MW]"],
        },
    },
}

ENERGY_CAPACITY_MWH = 200 / 1e6
BATTERY_EFFICIENCY = 0.8


class EVModel(mosaik_api_v3.Simulator):
    time_resolution: float
    entities: dict[str, dict[str, float]]
    step_size: int

    def __init__(self):
        super().__init__(META)
        self.entities = {}

    def init(self, sid, time_resolution, step_size):
        self.time_resolution = time_resolution
        self.step_size = step_size
        return self.meta

    def create(self, num, model, p_charge_mw):
        entities = []
        for i in range(num):
            eid = f"{model}_{len(self.entities)}"
            self.entities[eid] = {
                "E[MWH]": ENERGY_CAPACITY_MWH / 2,
                "P_load[MW]": 0.0,
                "P_charge[MW]": p_charge_mw,
            }
            entities.append({"eid": eid, "type": model})
        return entities

    def step(self, time, inputs, max_advance):
        for eid in self.entities.keys():
            p_load = self.entities[eid]["P_load[MW]"]
            charge_level = self.entities[eid]["E[MWH]"]

            if p_load == 0.0:
                charge_level -= (
                    2
                    * rnd.random()
                    * self.entities[eid]["P_charge[MW]"]
                    * (self.step_size * self.time_resolution / 3600.0)
                )
                if rnd.random() < 0.04 * self.time_resolution:
                    p_load = self.entities[eid]["P_charge[MW]"]
            else:
                charge_level += p_load * (
                    self.step_size * self.time_resolution / 3600.0 * BATTERY_EFFICIENCY
                )
                if charge_level >= ENERGY_CAPACITY_MWH:
                    p_load = 1e-9  # minimal load to keep the EV connected
                if rnd.random() < 0.02 * self.time_resolution:
                    p_load = 0.0

            charge_level = hu.clamp(charge_level, 0.0, ENERGY_CAPACITY_MWH)
            self.entities[eid]["P_load[MW]"] = p_load
            self.entities[eid]["E[MWH]"] = charge_level
        return time + self.step_size

    def get_data(self, outputs):
        data = {}
        for eid, attrs in outputs.items():
            data[eid] = {
                "E[MWH]": self.entities[eid]["E[MWH]"],
                "P_load[MW]": self.entities[eid]["P_load[MW]"],
            }
        return data
