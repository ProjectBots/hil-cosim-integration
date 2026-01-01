import mosaik_api_v3
import time  # Added for RTT measurement
from modbushil.mappingmanager import MappingManager
from modbushil.configurationmanager import ConfigurationManager
from typing import Any

import threading
import asyncio
import concurrent.futures as cf

class ModbusSimInterface(mosaik_api_v3.Simulator):
    metadata: dict[str, Any] = {
        "api_version": "3.0",
        "type": "time-based",
        "models": {},  # to be filled in __init__
    }

    instance_counter: dict[str, int] = {}

    def __init__(self):
        for modelname in ConfigurationManager.configs.keys():
            self.metadata["models"][modelname] = {
                "public": True,
                "params": ["host", "port"],
                "non-trigger": ConfigurationManager.configs[
                    modelname
                ].get_mosaik_non_trigger_variables(),
                "persistent": ConfigurationManager.configs[
                    modelname
                ].get_mosaik_persistent_variables(),
            }
            self.instance_counter[modelname] = 0

        self.modbus_manager: dict[str, MappingManager] = {}
        self.step_size: int = -1  # negative value indicates uninitialized
        self.use_async: bool = False
        self.loop: asyncio.AbstractEventLoop
        self.resp_future: dict[str, cf.Future[dict[str, float]]] = {}
        self.entity_public: dict[str, dict[str, float]] = {}
        
        # New: List to store the RTT of every step
        self.step_durations = [] 
        
        super().__init__(self.metadata)

    def init(self, sid, time_resolution: float, step_size: int, use_async: bool):
        if step_size <= 0:
            raise ValueError("Step size must be positive and non-zero")
        self.step_size = step_size
        self.use_async = use_async
        if self.use_async:
            self.loop = asyncio.new_event_loop()
            threading.Thread(target=self.loop.run_forever, daemon=True).start()
        return self.meta

    def finalize(self):
        # New: Calculate and print RTT statistics before closing
        if self.step_durations:
            min_rtt = min(self.step_durations)
            max_rtt = max(self.step_durations)
            avg_rtt = sum(self.step_durations) / len(self.step_durations)

            print("\n" + "="*40)
            print("MODBUS ROUND TRIP TIME (RTT) STATISTICS")
            print(f"Total Steps Measured: {len(self.step_durations)}")
            print(f"Minimum RTT:          {min_rtt:.6f} seconds")
            print(f"Maximum RTT:          {max_rtt:.6f} seconds")
            print(f"Average RTT:          {avg_rtt:.6f} seconds")
            print("="*40 + "\n")

        if self.step_size <= 0:
            return super().finalize()

        for manager in self.modbus_manager.values():
            manager.close()
        if self.use_async:
            self.loop.call_soon_threadsafe(self.loop.stop)
        return super().finalize()

    def create(self, num: int, model: str, host: str, port: int):
        result = []
        for _ in range(num):
            if model not in ConfigurationManager.configs:
                raise ValueError(f"Model {model} not registered")

            eid = f"{model}_{host}_{port}_{self.instance_counter[model]}"
            self.instance_counter[model] += 1
            self.modbus_manager[eid] = MappingManager(
                host=host, port=port, config=ConfigurationManager.configs[model]
            )
            if self.use_async:
                self.resp_future[eid] = cf.Future()
                self.resp_future[eid].set_result(
                    ConfigurationManager.configs[
                        model
                    ].get_mosaik_persistent_variables_defaults()
                )

            self.entity_public[eid] = {}
            result.append({"eid": eid, "type": model})

        return result

    def step(self, time_val, inputs, max_advance):
        # New: Start timer for this step
        step_start = time.perf_counter()

        for eid, attrs in inputs.items():
            if self.use_async:
                # In async mode, we wait for the previous step's Modbus result to resolve
                self.entity_public[eid].update(self.resp_future[eid].result())

                vars = {v: sum(vals.values()) for v, vals in attrs.items()}

                self.resp_future[eid] = asyncio.run_coroutine_threadsafe(
                    self.fetch_entity_data_async(self.modbus_manager[eid], vars),
                    self.loop,
                )
            else:
                # In sync mode, we perform the Modbus read/write immediately
                vars = {v: sum(vals.values()) for v, vals in attrs.items()}
                result = ModbusSimInterface.fetch_entity_data(
                    self.modbus_manager[eid], vars
                )
                self.entity_public[eid].update(result)

        # New: Record the total time spent in this step
        step_end = time.perf_counter()
        self.step_durations.append(step_end - step_start)

        return time_val + self.step_size

    async def fetch_entity_data_async(
        self, mapping_manager: MappingManager, vars: dict[str, Any]
    ) -> dict[str, Any]:
        return await self.loop.run_in_executor(
            None, ModbusSimInterface.fetch_entity_data, mapping_manager, vars
        )

    @classmethod
    def fetch_entity_data(
        cls, mapping_manager: MappingManager, vars: dict[str, Any]
    ) -> dict[str, Any]:
        mapping_manager.update_variable_buffer(vars)
        mapping_manager.write_phase() # Writes to hardware registers

        mapping_manager.read_phase()  # Reads from hardware registers
        return mapping_manager.get_all_mosaik_persistent_variables()

    def get_data(self, outputs):
        data = {}
        for eid, attrs in outputs.items():
            data[eid] = self.entity_public[eid]

        return data