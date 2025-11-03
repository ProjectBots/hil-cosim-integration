import mosaik_api_v3

META = {
    "api_version": "3.0",
    "type": "time-based",
    "models": {
        "BatteryModel": {
            "public": True,
            "params": ["e_max_mwh"],
            "trigger": [],  
            "non-trigger": ["P_in[MW]"],
            "persistent": ["P_out[MW]", "SoC"], # SoC = state of charge
            "non-persistent": [],
        },
    },
}


class BatteryModel(mosaik_api_v3.Simulator):
    time_resolution: float
    entities: dict[str, dict[str, float]]
    step_size: int

    def __init__(self):
        super().__init__(META)
        self.entities = {}
        self.charge_level = 0.0

    def init(self, sid, time_resolution, step_size):
        print(f"Init called with sid={sid}, time_resolution={time_resolution}")
        self.time_resolution = time_resolution
        self.step_size = step_size
        return self.meta

    def create(self, num, model, e_max_mwh):
        entities = []
        for i in range(num):
            eid = f"{model}_{len(self.entities)}"
            self.entities[eid] = {
                "P_out[MW]": 0.0,
                "E_max[MWH]": e_max_mwh,
                "E[MWH]": 0.0,
            }
            entities.append({"eid": eid, "type": model})
        return entities

    def step(self, time, inputs, max_advance):
        for eid, attrs in inputs.items():
            p_in = sum(attrs["P_in[MW]"].values())
            p_out = self.entities[eid]["P_out[MW]"]

            charge_level = self.entities[eid]["E[MWH]"]
            charge_level += (p_in - p_out) * (self.step_size / 3600.0)
            charge_level = max(
                0.0, min(charge_level, self.entities[eid]["E_max[MWH]"])
            )
            if charge_level < 1e-6:
                self.setOutput(eid, 0.0)
            self.entities[eid]["E[MWH]"] = charge_level

        return time + self.step_size
    
    def setOutput(self, eid, value):
        self.entities[eid]["P_out[MW]"] = value
    
    def getOutput(self, eid):
        return self.entities[eid]["P_out[MW]"]

    def get_data(self, outputs):
        data = {}
        for eid, attrs in outputs.items():
            data[eid] = {
                "P_out[MW]": self.entities[eid]["P_out[MW]"],
                "SoC": self.entities[eid]["E[MWH]"]
                / self.entities[eid]["E_max[MWH]"],
            }

        return data
