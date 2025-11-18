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

NUM_AVG_STEPS = 10

class BatteryControllerSim(mosaik_api_v3.Simulator):
    entities: dict[str, dict[str, float]]
    step_size: int
    time_resolution: float
    last_targets: dict[str, list[float]]

    def __init__(self):
        super().__init__(META)
        self.entities = {}
        self.last_targets = {}

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
            self.last_targets[eid] = [0.0 for _ in range(NUM_AVG_STEPS)]

            entities.append({"eid": eid, "type": model})
        return entities

    def step(self, time, inputs, max_advance):
        for eid, attrs in inputs.items():
            p_grid = sum(attrs["P_grid[MW]"].values())
            self.last_targets[eid].pop(0)
            self.last_targets[eid].append(p_grid / self.entities.__len__())
            self.entities[eid]["P_target[MW]"] = sum(self.last_targets[eid]) / NUM_AVG_STEPS

        return time + self.step_size

    def get_data(self, outputs):
        data = {}
        for eid, attrs in outputs.items():
            data[eid] = {
                "P_target[MW]": self.entities[eid]["P_target[MW]"],
            }
        return data
