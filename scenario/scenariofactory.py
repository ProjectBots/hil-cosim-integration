from datetime import datetime

import mosaik
import mosaik.util as mu
import scenario.gridfactory as gridfactory
from typing import Any


START = datetime(2020, 6, 1, 10, 0, 0)

PVSIM_PARAMS = {
    "start_date": START,
    "cache_dir": "./cache/pvsim/",
    "verbose": False,
}

PVMODEL_PARAMS = {
    "scale_factor": 1.7,  # multiplies power production, 1 is equal to 1 kW peak power installed
    "lat": 47.72368491405467,
    "lon": 13.086242711396213,
    "slope": 0,
    "azimuth": 0,
    "optimal_angle": True,  # calculate and use an optimal slope
    "optimal_both": False,  # calculate and use an optimal slope and azimuth
    "pvtech": "CIS",
    "system_loss": 14,
    "database": "PVGIS-SARAH3",
    "datayear": START.year,
}


def get_node_by_id(grid, type, id) -> Any:
    for elem in grid:
        if elem.eid == type + "-" + id.__str__():
            return elem
    raise ValueError(f"Node of type {type} with id {id} not found in grid")


def add_simple_scenario(world: mosaik.World, use_async_battery: bool):
    pv_sim = world.start("PVSim", step_size=1, sim_params=PVSIM_PARAMS)
    pp_sim = world.start("PPSim", step_size=1)
    battery_sim = world.start("BatterySim", step_size=1, use_async=use_async_battery)
    ev_sim = world.start("EVSim", step_size=1)
    ctrl_sim = world.start("ControllerSim", step_size=1)
    webvis = world.start(
        "WebVis", start_date=START.isoformat(sep=" "), step_size=1
    )

    griddata = gridfactory.create_net()

    pv_model = pv_sim.PVSim.create(1, **PVMODEL_PARAMS)[0]
    grid = pp_sim.Grid(net=griddata["net"]).children
    battery = battery_sim.BatteryModel.create(
        1, e_max_mwh=1000 / 1e6, p_max_gen_mw=3000 / 1e6, p_max_load_mw=3000 / 1e6
    )[0]
    ev = ev_sim.EVModel.create(1, p_charge_mw=2500 / 1e6)[0]
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
    # Use time shifted connection to prevent circular dependencies
    # If you want to know why we time shift here instead of the battery output, ask Tobias
    world.connect(
        controller,
        battery,
        ("P_target[MW]", "P_target[MW]"),
        time_shifted=True,
        initial_data={"P_target[MW]": 0.0},
    )
    world.connect(node_grid, controller, ("P[MW]", "P_grid[MW]"))

    webvis.set_config(
        ignore_types=["Topology", "Grid", "DebugSim"],
        merge_types=[
            "Line",
        ],
    )

    webvis.set_etypes(
        {
            "Bus": {
                "cls": "refbus",
                "attr": "P[MW]",
                "unit": "MW",
                "default": 0.0,
                "min": -1.0,
                "max": 1.0,
            },
            "ExternalGrid": {
                "cls": "slack",
                "attr": "P[MW]",
                "unit": "MW",
                "default": 0.0,
                "min": -1.0,
                "max": 1.0,
            },
            "PVSim": {
                "cls": "generator",
                "attr": "P[MW]",
                "unit": "MW",
                "default": 0.0,
                "min": 0.0,
                "max": PVMODEL_PARAMS["scale_factor"],
            },
            "BatteryModel": {
                "cls": "battery",
                "attr": "SoC",
                "unit": "SoC",
                "default": 0.0,
                "min": 0.0,
                "max": 1.0,
            },
            "BatteryControllerSim": {
                "cls": "controller",
                "attr": "P_target[MW]",
                "unit": "MW",
                "default": 0.5,
                "min": -1.0,
                "max": 1.0,
            },
            "EVModel": {
                "cls": "load",
                "attr": "E[MWH]",
                "unit": "MWH",
                "default": 0,
                "min": -0.1,
                "max": 0.1,
            },
        }  # pyright: ignore[reportCallIssue]
    )

    vis_topo = webvis.Topology()

    world.connect(pv_model, vis_topo, ("P[MW]", "P[MW]"))
    world.connect(node_grid, vis_topo, ("P[MW]", "P[MW]"))
    world.connect(controller, vis_topo, ("P_target[MW]", "P_target[MW]"))
    world.connect(ev, vis_topo, ("E[MWH]", "E[MWH]"))
    world.connect(battery, vis_topo, ("SoC", "SoC"))

    mu.connect_many_to_one(
        world, [e for e in grid if e.type == "Bus"], vis_topo, ("P[MW]", "P[MW]")
    )
