import mosaik
import scenario.scenariofactory as scenariofactory
import helperutils as hu
from modbushil.configurationmanager import ConfigurationManager

from dotenv import load_dotenv

STEP_SIZE_SECONDS = 0.5
STEPS_TOTAL = 500

REAL_BATTERY_PARAMS = {
    "modbus_io_bundles": {
        "read": {"holding_register": ["2-4"]},
        "write": {"holding_register": ["1-2"]},
    },
    "variables": {
        "P_target[MW]": {
            "iotype": "write",
            "datatype": "uint",
            "register": "h1",
            "mosaik": True,
            "scale": 1e-6,
        },
        "State": {
            "iotype": "both",
            "datatype": "uint",
            "register": "h2",
        },
        "P_out[MW]": {
            "iotype": "read",
            "datatype": "int",
            "register": "h3",
            "scale": 1e-6,
        },
        "E[MWH]": {
            "iotype": "read",
            "datatype": "int",
            "register": "h4",
            "mosaik": True,
            "scale": 1e-6,
        },
        "P_load[MW]": {
            "iotype": "read",
            "datatype": "float",
            "mosaik": True,
        },
        "P_gen[MW]": {
            "iotype": "read",
            "datatype": "float",
            "mosaik": True,
        },
        "P[MW]": {
            "iotype": "read",
            "datatype": "float",
            "mosaik": True,
        },
        "SoC": {
            "iotype": "read",
            "datatype": "float",
            "mosaik": True,
        },
    },
    "methods": {
        "read": [
            {
                "set": "P[MW]",
                "action": "eval",
                "expression": "$(P_out[MW]) * (1 if $(State) == 0 else -1)",
            },
            {
                "set": "P_gen[MW]",
                "action": "eval",
                "expression": "max(-$(P[MW]), 0.0)",
            },
            {
                "set": "P_load[MW]",
                "action": "eval",
                "expression": "max($(P[MW]), 0.0)",
            },
            {
                "set": "SoC",
                "action": "eval",
                "expression": "$(E[MWH]) / (1000 / 1e6)",  # Assuming E_max is 1000 MWH
            },
        ],
        "write": [
            {
                "set": "State",
                "action": "eval",
                "expression": "0 if $(P_target[MW]) >= 0.0 else 1",
            },
            {
                "set": "P_target[MW]",
                "action": "eval",
                "expression": "abs($(P_target[MW]))",
            },
        ],
    },
}


def main():
    use_real_battery = hu.get_bool_env_var("USE_REAL_BATTERY", False)

    if use_real_battery:
        ConfigurationManager.register_model("BatterySim", REAL_BATTERY_PARAMS)

    sim_config: mosaik.SimConfig = {
        "BatterySim": {
            "python": "modbushil.siminterface:ModbusSimInterface"
            if use_real_battery
            else "simulators.batterysim:BatteryModel",
        },
        "PPSim": {
            "python": "mosaik_components.pandapower:Simulator",
        },
        "PVSim": {
            "python": "mosaik_components.pv.pvgis_simulator:PVGISSimulator",
        },
        "EVSim": {
            "python": "simulators.evsim:EVModel",
        },
        "ControllerSim": {
            "python": "simulators.controllersim:BatteryControllerSim",
        },
        "WebVis": {
            "cmd": "mosaik-web -s 127.0.0.1:8000 %(addr)s",
        },
        "DebugSim": {
            "python": "simulators.debugsim:DebugSim",
        },
    }

    world = mosaik.World(sim_config, time_resolution=STEP_SIZE_SECONDS)

    use_async_battery = hu.get_bool_env_var("USE_ASYNC_BATTERY", True)

    scenariofactory.add_simple_scenario(world, use_async_battery, use_real_battery)

    # TODO: figure out how to get rid of behind schedule warnings when rt_factor is set
    world.run(
        until=STEPS_TOTAL,
        rt_factor=1.0 if hu.get_bool_env_var("USE_REAL_BATTERY", False) else None,
    )


if __name__ == "__main__":
    load_dotenv()
    main()
