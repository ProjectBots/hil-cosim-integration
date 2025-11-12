import mosaik

from datetime import datetime

import scenario.scenariofactory as scenariofactory

IS_REALTIME = True

STEP_SIZE_SECONDS = 60*60
STEPS_TOTAL = 500

sim_config: mosaik.SimConfig = {
    "BatterySim": {
        "python": "simulators.batteryreal:BatteryModel"  # simulators.batterysim:BatteryModelRT
        if IS_REALTIME
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
        'cmd': 'mosaik-web -s 127.0.0.1:8000 %(addr)s',
    },
    "DebugSim": {
        "python": "simulators.debugsim:DebugSim",
    },
}


def main():
    world = mosaik.World(sim_config)

    scenariofactory.add_simple_scenario(world, STEP_SIZE_SECONDS)

    # TODO: figure out how to get rid of behind schedule warnings when rt_factor is set
    # world.run(
    #     until=STEPS_TOTAL * STEP_SIZE_SECONDS, rt_factor=1.0 if IS_REALTIME else None
    # )
    world.run(until=STEPS_TOTAL * STEP_SIZE_SECONDS)    # no rt_factor for now to avoid warnings


    


if __name__ == "__main__":
    main()
