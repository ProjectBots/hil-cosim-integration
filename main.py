import mosaik

from datetime import datetime
from datetime import timedelta

START = datetime(2020, 1, 1, 0, 0, 0)
STEP_SIZE = timedelta(minutes=15)

PVSIM_PARAMS = {
    "start_date": START,
    "cache_dir": "./chache/pvsim/",
    "verbose": True,
}

PVMODEL_PARAMS = {
    "scale_factor": 1000,  # multiplies power production, 1 is equal to 1 kW peak power installed
    "lat": 52.373,
    "lon": 9.738,
    "slope": 0,  # default value,
    "azimuth": 0,  # default value,
    "optimal_angle": True,  # calculate and use an optimal slope
    "optimal_both": False,  # calculate and use an optimal slope and azimuth
    "pvtech": "CIS",  # default value,
    "system_loss": 14,  # default value,
    "database": "PVGIS-SARAH3",  # default value,
    "datayear": 2016,  # default value,
}


sim_config: mosaik.SimConfig = {
    "BatterySim": {
        "python": "simulators.BatterySimulator:Battery",
    },
    "Grid": {
        "python": "mosaik_pandapower.simulator:Pandapower",
    },
    "PVSim": {"python": "mosaik_components.pv.pvgis_simulator:PVGISSimulator"},
}


def main():
    world = mosaik.World(sim_config)

    gridsim = world.start("Grid", stepSize=15 * 60)
    mysim = world.start("MySim")
    evsim = world.start("EV")

    pv_sim = world.start(
        "PVSim",
        step_size=STEP_SIZE,
        sim_params=PVSIM_PARAMS,
    )
    pv_model = pv_sim.PVSim.create(1, **PVMODEL_PARAMS)

    grid = gridsim.Grid(gridfile="gridfile.json")

    a = mysim.MyModel.create(1, p1=10)

    world.run(until=100)


if __name__ == "__main__":
    main()
