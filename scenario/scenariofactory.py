from datetime import datetime

import mosaik
import scenario.gridfactory as gridfactory
from typing import Any

BATTERY_CAPACITY_MWH = 0.1


START = datetime(2020, 1, 1, 0, 0, 0)
STEP_SIZE_SECONDS = 10
STEPS_TOTAL = 100

PVSIM_PARAMS = {
    "start_date": START,
    "cache_dir": "./cache/pvsim/",
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


HOUSEHOLD_WIRE_DATA = {
    "r_ohm_per_km": 7.41,
    "x_ohm_per_km": 0.12,
    "c_nf_per_km": 210,
    "max_i_ka": 0.020,
}


def get_node_by_id(grid, type, id) -> Any:
    for elem in grid:
        if elem.eid == type + "-" + id.__str__():
            return elem
    raise ValueError(f"Node of type {type} with id {id} not found in grid")


def add_simple_scenario(world: mosaik.World):
    pv_sim = world.start("PVSim", step_size=STEP_SIZE_SECONDS, sim_params=PVSIM_PARAMS)
    pp_sim = world.start("PPSim", step_size=STEP_SIZE_SECONDS)
    battery_sim = world.start("BatterySim", step_size=STEP_SIZE_SECONDS)
    ev_sim = world.start("EVSim", step_size=STEP_SIZE_SECONDS)
    ctrl_sim = world.start("ControllerSim", step_size=STEP_SIZE_SECONDS)
    # TODO: do visualization
    #webvis = world.start("WebVis", start_date=START.isoformat(sep=" "), step_size=STEP_SIZE_SECONDS)

    griddata = gridfactory.create_net()

    pv_model = pv_sim.PVSim.create(1, **PVMODEL_PARAMS)[0]
    grid = pp_sim.Grid(net=griddata["net"]).children
    battery = battery_sim.BatteryModel.create(1, e_max_mwh=BATTERY_CAPACITY_MWH, p_max_gen_mw=0.05, p_max_load_mw=0.05)[0]
    ev = ev_sim.EVModel.create(1, p_charge_mw=0.007)[0]
    controller = ctrl_sim.BatteryControllerSim.create(1)[0]


    node_bat = get_node_by_id(grid, "Bus", griddata["id_battery"])
    node_ev = get_node_by_id(grid, "Bus", griddata["id_ev"])
    node_pv = get_node_by_id(grid, "Bus", griddata["id_pv"])
    # there should only be one external grid, but the id is not the same as the one of the connected bus
    node_grid = [elem for elem in grid if elem.type == "ExternalGrid"][0]

    world.connect(pv_model, node_pv, ("P[MW]", "P_gen[MW]"))
    world.connect(battery, node_bat, ("P_load[MW]", "P_load[MW]"))
    world.connect(battery, node_bat, ("P_gen[MW]", "P_gen[MW]"))
    world.connect(ev, node_ev, ("P_load[MW]", "P_load[MW]"))
    world.connect(controller, battery, ("P_target[MW]", "P_target[MW]"))
    # Use time_shifted connection to prevent circular dependency
    world.connect(node_grid, controller, ("P[MW]", "P_grid[MW]"), time_shifted=True, initial_data={"P[MW]": 0.0})

