import mosaik_api_v3

META = {
    "api_version": "3.0",
    "type": "time-based",
    "models": {
        "BatteryControllerSim": {
            "public": True,
            "params": [],
            "trigger": [],
            "non-trigger": ["P_grid[MW]"],
            "persistent": ["P_target[MW]"],
            "non-persistent": [],
        },
    },
}


class BatteryControllerSim(mosaik_api_v3.Simulator):
    entities: dict[str, dict[str, float]]
    step_size: int
    time_resolution: float

    def __init__(self):
        super().__init__(META)
        self.entities = {}

    def init(self, sid, time_resolution, step_size):
        self.time_resolution = time_resolution
        self.step_size = step_size
        return self.meta

    def create(self, num, model):
        entities = []
        for i in range(num):
            eid = f"{model}_{len(self.entities)}"
            self.entities[eid] = {
                "P_target[MW]": 0.0,
            }
            entities.append({"eid": eid, "type": model})
        return entities

    def step(self, time, inputs, max_advance):
        for eid, attrs in inputs.items():
            p_grid = sum(attrs["P_grid[MW]"].values())
            self.entities[eid]["P_target[MW]"] = -p_grid / self.entities.__len__()

        return time + self.step_size

    def get_data(self, outputs):
        data = {}
        for eid, attrs in outputs.items():
            data[eid] = {
                "P_target[MW]": self.entities[eid]["P_target[MW]"],
            }
        return data
