
import mosaik_api_v3


META = {
    "api_version": "3.0",
    "type": "time-based",
    "models": {
        "DebugSim": {
            "public": True,
            "params": ["name"],
            "non-trigger": ["A"],
            "persistent": [],
        },
    },
}


class DebugSim(mosaik_api_v3.Simulator):
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

	def create(self, num, model, name):
		entities = []
		for i in range(num):
			eid = f"{model}_{len(self.entities)}"
			self.entities[eid] = {"name": name}
			entities.append({"eid": eid, "type": model})
		return entities

	def step(self, time, inputs, max_advance):
		for eid, attrs in inputs.items():
			a = sum(attrs["A"].values())
			print(f"[DebugSim] time {time}: Received A={a} from {self.entities[eid]["name"]}")
			
		return time + self.step_size

	def get_data(self, outputs):
		data = {}
		'''
		for eid, attrs in outputs.items():
			pass
		'''
		return data