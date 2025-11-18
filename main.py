import mosaik
import scenario.scenariofactory as scenariofactory
import helperutils as hu

from dotenv import load_dotenv

STEP_SIZE_SECONDS = 2
STEPS_TOTAL = 500

def main():
    sim_config: mosaik.SimConfig = {
        "BatterySim": {
            "python": "simulators.batteryreal:BatteryModel"
            if hu.get_bool_env_var("USE_REAL_BATTERY", False)
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

    world = mosaik.World(sim_config)

    scenariofactory.add_simple_scenario(world, STEP_SIZE_SECONDS)

    # TODO: figure out how to get rid of behind schedule warnings when rt_factor is set
    world.run(
        until=STEPS_TOTAL * STEP_SIZE_SECONDS,
        rt_factor=1.0 if hu.get_bool_env_var("USE_REAL_BATTERY", False) else None,
    )


if __name__ == "__main__":
    load_dotenv()
    main()
