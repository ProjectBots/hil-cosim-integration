import mosaik

from datetime import datetime

import scenario.scenariofactory as scenariofactory

IS_REALTIME = False

START = datetime(2020, 1, 1, 0, 0, 0)
STEP_SIZE_SECONDS = 10
STEPS_TOTAL = 5

sim_config: mosaik.SimConfig = {
    "BatterySim": {
        "python": "simulators.batterysim:BatteryModelRT"
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
}


def main():
    world = mosaik.World(sim_config)

    scenariofactory.add_simple_scenario(world)

    # TODO: figure out how to get rid of behind schedule warnings when rt_factor is set
    world.run(
        until=STEPS_TOTAL * STEP_SIZE_SECONDS, rt_factor=1.0 if IS_REALTIME else None
    )


if __name__ == "__main__":
    main()
