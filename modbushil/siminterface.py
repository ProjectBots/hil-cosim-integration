import mosaik_api_v3

from modbushil.mappingmanager import MappingManager
from typing import Any


import threading
import asyncio
import concurrent.futures as cf
from modbushil.modbusintegrationsettings import ModbusIntegrationSettings


class ModbusSimInterface(mosaik_api_v3.Simulator):
    metadata: dict[str, Any] = {
        "api_version": "3.0",
        "type": "time-based",
        "models": {},  # to be filled by registerModel
    }
    modbus_config: dict[str, ModbusIntegrationSettings] = {}
    instance_counter: dict[str, int] = {}

    @classmethod
    def registerModel(cls, modelname: str, config: dict[str, Any]):
        settings = ModbusIntegrationSettings(config)
        cls.modbus_config[modelname] = settings
        cls.metadata["models"][modelname] = {
            "public": True,
            "params": ["host", "port"],
            "non-trigger": settings.get_mosaik_non_trigger_variables(),
            "persistent": settings.get_mosaik_persistent_variables(),
        }
        cls.instance_counter[modelname] = 0

    def __init__(self):
        self.modbus_manager: dict[str, MappingManager] = {}
        self.step_size: int = -1  # negative value indicates uninitialized
        self.use_async: bool = False
        self.loop: asyncio.AbstractEventLoop
        self.resp_future: dict[str, cf.Future[dict[str, float]]] = {}
        self.entity_public: dict[str, dict[str, float]] = {}
        super().__init__(self.metadata)

    def init(self, sid, time_resolution: float, step_size: int, use_async: bool):
        if step_size <= 0:
            raise ValueError("Step size must be positive")
        self.step_size = step_size
        self.use_async = use_async
        if self.use_async:
            self.loop = asyncio.new_event_loop()
            threading.Thread(target=self.loop.run_forever, daemon=True).start()
        return self.meta

    def finalize(self):
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
            if model not in self.modbus_config:
                raise ValueError(f"Model {model} not registered")

            eid = f"{model}_{host}_{port}_{self.instance_counter[model]}"
            self.instance_counter[model] += 1
            self.modbus_manager[eid] = MappingManager(
                host=host, port=port, config=self.modbus_config[model]
            )
            if self.use_async:
                self.resp_future[eid] = cf.Future()
                self.resp_future[eid].set_result(
                    self.modbus_config[model].get_mosaik_persistent_variables_defaults()
                )

            self.entity_public[eid] = {}
            result.append({"eid": eid, "type": model})

        return result

    def step(self, time, inputs, max_advance):
        for eid, attrs in inputs.items():
            if self.use_async:
                self.entity_public[eid].update(self.resp_future[eid].result())

                vars = {v: sum(vals.values()) for v, vals in attrs.items()}

                self.resp_future[eid] = asyncio.run_coroutine_threadsafe(
                    self.fetch_entity_data_async(self.modbus_manager[eid], vars),
                    self.loop,
                )
            else:
                vars = {v: sum(vals.values()) for v, vals in attrs.items()}
                result = ModbusSimInterface.fetch_entity_data(
                    self.modbus_manager[eid], vars
                )
                self.entity_public[eid].update(result)

        return time + self.step_size

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
        mapping_manager.write_phase()

        mapping_manager.read_phase()
        return mapping_manager.get_all_mosaik_persistent_variables()

    def get_data(self, outputs):
        data = {}
        for eid, attrs in outputs.items():
            data[eid] = self.entity_public[eid]

        return data
