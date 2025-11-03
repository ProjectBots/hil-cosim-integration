
import mosaik_api_v3


META = {
    "api_version": "3.0",
    "type": "time-based",
    "models": {
        "EVModel": {
            "public": True,
            "params": [],
            "trigger": [],  # SoC = state of charge
            "non-trigger": ["P[MW]"],
            "persistent": ["E[MWH]"],
            "non-persistent": [],
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
        print(f"Init called with sid={sid}, time_resolution={time_resolution}")
        self.time_resolution = time_resolution
        self.step_size = step_size
        return self.meta

    def create(self, num, model):
        entities = []
        for i in range(num):
            eid = f"{model}_{len(self.entities)}"
            self.entities[eid] = {"E[MWH]": 0.0}
            entities.append({"eid": eid, "type": model})
        return entities

    def step(self, time, inputs, max_advance):
        # TODO: implement EV behavior
        return time + self.step_size

    def get_data(self, outputs):
        data = {}
        for eid, attrs in outputs.items():
            data[eid] = {"E[MWH]": self.entities[eid]["E[MWH]"]}
        return data