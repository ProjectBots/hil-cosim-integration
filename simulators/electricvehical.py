
import mosaik_api_v3

META = {
    "type": "time-based",
    "models": {
        # TODO change model
        "MyModel": {
            "public": True,
            "params": ["p1", "p2"],
            "attrs": ["a", "b"],
        },
    },
}


class MySimulator(mosaik_api_v3.Simulator):
    def __init__(self):
        super().__init__(META)
        self.entities = {}

    def init(self, sid, time_resolution, **sim_params):
        print(f"Init called with sid={sid}, time_resolution={time_resolution}")
        return self.meta

    def create(self, num, model, **model_params):
        entities = []
        for i in range(num):
            eid = f"{model}_{len(self.entities)}"
            self.entities[eid] = model_params
            entities.append({"eid": eid, "type": model})
        return entities

    def step(self, time, inputs, max_advance):
        return time + 1

    def get_data(self, outputs):
        data = {}
        for eid, attrs in outputs.items():
            data[eid] = {a: 42 for a in attrs}  # dummy values
        return data