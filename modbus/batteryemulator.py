from pyModbusTCP.server import ModbusServer
import time
import os
import schedule
import helperutils as hu
import warnings

import dotenv

# TODO: central location for these constants
POWER_GEN_MAX_W = 4000.0
POWER_LOAD_MAX_W = 3000.0
ENERGY_CAPACITY_WH = 10000.0

REGISTER_P_TARGET = 1
REGISTER_STATE = 2
REGISTER_P_OUT = 3
REGISTER_E = 4

STEP_SIZE_SECONDS = 1

class ModbusBatteryServer:
    
    current_power_w = 0.0
    energy_wh = 0.0
    server: ModbusServer
    
    def __init__(self, host, port) -> None:
        if POWER_GEN_MAX_W > 65535 or POWER_LOAD_MAX_W > 65535 or ENERGY_CAPACITY_WH > 65535:
            raise ValueError("POWER_GEN_MAX_W, POWER_LOAD_MAX_W, and ENERGY_CAPACITY_WH must be <= 65535 for Modbus register storage")

        print("Starting Modbus Battery Server...")
        self.server = ModbusServer(host, port, no_block=True)

        self.server.data_bank.set_holding_registers(REGISTER_P_TARGET, [0])
        self.server.data_bank.set_holding_registers(REGISTER_STATE, [0])
        self.server.data_bank.set_holding_registers(REGISTER_P_OUT, [0])
        self.server.data_bank.set_holding_registers(REGISTER_E, [0])

        self.server.start()
        print(f"Server started on {host}:{port}")

    def step(self) -> None:
        regs = self.server.data_bank.get_holding_registers(REGISTER_P_TARGET, 2)
        if regs is None or len(regs) < 2:
            print("Failed to read target power or state from Modbus register")
            return
        p_target_w = regs[0]
        state = regs[1]
        
        if state == 0:
            # Discharging
            if self.energy_wh <= 0.0:
                self.current_power_w = 0.0  # Prevent discharging when empty
            else:
                self.current_power_w = min(p_target_w, POWER_LOAD_MAX_W)
        elif state == 1:
            # Charging
            if self.energy_wh >= ENERGY_CAPACITY_WH:
                self.current_power_w = 0.0  # Prevent charging when full
            else:
                self.current_power_w = -min(p_target_w, POWER_GEN_MAX_W)
        else:
            warnings.warn(f"Unknown state {state}, setting power to 0")
            self.current_power_w = 0.0  # Idle
        
        self.energy_wh -= self.current_power_w * (STEP_SIZE_SECONDS / 3600.0)
        self.energy_wh = hu.clamp(self.energy_wh, 0.0, ENERGY_CAPACITY_WH)
        
        self.server.data_bank.set_holding_registers(
            REGISTER_P_OUT, [int(abs(self.current_power_w))]
        )
        self.server.data_bank.set_holding_registers(
            REGISTER_E, [int(self.energy_wh)]
        )
        
        print(f"Modbus Battery Emulator Step: P_target={p_target_w} W, State={state}, P_out={self.current_power_w} W, E={self.energy_wh} Wh")
        

    def stop(self) -> None:
        print("Shutting down server...")
        self.server.stop()
        print("Server is offline")
        

if __name__ == "__main__":
    dotenv.load_dotenv()

    host = os.getenv("HOST")
    if not host:
        raise ValueError("HOST environment variable not set")
    port = os.getenv("PORT")
    if not port:
        raise ValueError("PORT environment variable not set")
    try:
        port = int(port)
    except ValueError | TypeError:
        raise ValueError("PORT environment variable is not a valid integer")

    emulator = ModbusBatteryServer(host, port)
    
    schedule.every(STEP_SIZE_SECONDS).seconds.do(emulator.step)

    # wait for keyboard interrupt to stop the server
    try:
        while True:
            schedule.run_pending()
            time.sleep(0.1)
    except KeyboardInterrupt:
        emulator.stop()
    
    exit(0)
        
