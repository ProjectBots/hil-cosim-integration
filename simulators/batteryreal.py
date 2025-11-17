import mosaik_api_v3

import simulators.batterymetainfo as batterymetainfo
from pyModbusTCP.client import ModbusClient
import os
import warnings

import threading
import asyncio
import concurrent.futures
import helperutils as hu

# TODO: central location for these constants
REGISTER_P_TARGET = 1  # Register to write target power (kW)
REGISTER_STATE = 2  # Register to write charge/discharge state
REGISTER_P_OUT = 3  # Register to read current power (kW)
REGISTER_E_MWH = 4  # Register to read current energy (kWh)


class BatteryModel(mosaik_api_v3.Simulator):
    created: bool = False
    eid: str = "Real_Battery"
    entity_public: dict[str, float]

    client: ModbusClient
    step_size: int

    resp_future: concurrent.futures.Future[dict[str, float]] | None = None
    loop: asyncio.AbstractEventLoop

    def __init__(self):
        super().__init__(batterymetainfo.BATTERY_MODEL_META_DATA)

    def init(self, sid, time_resolution, step_size):
        self.step_size = step_size
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.loop.run_forever, daemon=True).start()
        return self.meta

    def finalize(self):
        if self.client.is_open:
            self.client.close()
        if self.loop is not None:
            self.loop.call_soon_threadsafe(self.loop.stop)
        return super().finalize()

    def create(self, num, model, e_max_mwh, p_max_gen_mw, p_max_load_mw):
        if num != 1 or self.created:
            raise ValueError("BatteryModel only supports one instance")
        self.created = True
        self.entity_public = {
            "P_out[MW]": 0.0,
            "E_max[MWH]": e_max_mwh,
            "E[MWH]": 0.0,
            "P_max_gen[MW]": p_max_gen_mw,  # Not used but kept for compatibility
            "P_max_load[MW]": p_max_load_mw,  # Not used but kept for compatibility
        }

        port_str = os.getenv("PORT", "5001")
        if not port_str:
            raise ValueError("PORT environment variable not set")
        host = os.getenv("HOST", "localhost")
        if not host:
            raise ValueError("HOST environment variable not set")
        try:
            port = int(port_str)
        except ValueError | TypeError:
            raise ValueError("PORT environment variable is not a valid integer")

        self.client = ModbusClient(host=host, port=port)
        if not self.client.open():
            raise ConnectionError("Unable to connect to Modbus server")

        return [{"eid": self.eid, "type": model}]

    def step(self, time, inputs, max_advance):
        if self.resp_future is not None:
            self.entity_public.update(self.resp_future.result())

        attrs = inputs.get(self.eid, {})
        p_target = sum(attrs["P_target[MW]"].values()) * 1e6

        self.resp_future = asyncio.run_coroutine_threadsafe(
            self.update_entity_data(p_target), self.loop
        )

        return time + self.step_size

    async def update_entity_data(self, p_target) -> dict[str, float]:
        if not self.client.is_open:
            warnings.warn("Modbus client not connected, attempting to reconnect")
            if not self.client.open():
                raise ConnectionError("Unable to connect to Modbus server")

        state = 0 if p_target > 0 else 1  # 0: discharging, 1: charging
        p_target = int(hu.clamp(abs(p_target), 0, pow(2, 16) - 1))

        self.client.write_multiple_registers(REGISTER_P_TARGET, [p_target, state])

        regs = self.client.read_holding_registers(REGISTER_P_OUT, 2)
        if regs is None or len(regs) < 2:
            raise ConnectionError("Failed to read from Modbus server")

        result = {
            "P_out[MW]": regs[0] / 1e6 * (1 if state == 0 else -1),
            "E[MWH]": regs[1] / 1e6,
        }

        return result

    def get_data(self, outputs):
        data = {}
        for eid, attrs in outputs.items():
            data[eid] = {
                "P_load[MW]": max(0.0, self.entity_public["P_out[MW]"]),
                "P_gen[MW]": max(0.0, -self.entity_public["P_out[MW]"]),
                "SoC": self.entity_public["E[MWH]"] / self.entity_public["E_max[MWH]"],
                "P[MW]": self.entity_public["P_out[MW]"],
            }

        return data
