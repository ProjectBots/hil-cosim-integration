import mosaik_api_v3
import random as rnd


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
            self.entities[eid] = {"E[MWH]": 0.0, "P_load[MW]": 0.0, "P_charge[MW]": p_charge_mw}
            entities.append({"eid": eid, "type": model})
        return entities

    def step(self, time, inputs, max_advance):
        for eid, attrs in inputs.items():
            p_load = self.entities[eid].get("P_load[MW]", 0.0)
            if p_load == 0.0:
                if rnd.random() < 0.1:  # 10% chance to start charging
                    p_load = self.entities[eid]["P_charge[MW]"]
            else:
                self.entities[eid]["E[MWH]"] += p_load * (self.step_size / 3600.0)
                if rnd.random() < 0.05:  # 5% chance to stop charging
                    p_load = 0.0
            
            self.entities[eid]["P_load[MW]"] = p_load
        return time + self.step_size

    def get_data(self, outputs):
        data = {}
        for eid, attrs in outputs.items():
            data[eid] = {"E[MWH]": self.entities[eid]["E[MWH]"], "P_load[MW]": self.entities[eid]["P_load[MW]"]}
        return data
