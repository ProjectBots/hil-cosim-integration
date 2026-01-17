from datetime import datetime

import mosaik
import mosaik.util as mu
import scenario.gridfactory as gridfactory
from typing import Any
import os


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


def add_simple_scenario(
    world: mosaik.World, use_async_battery: bool, use_real_battery: bool
):
    pv_sim = world.start("PVSim", step_size=1, sim_params=PVSIM_PARAMS)
    pp_sim = world.start("PPSim", step_size=1)
    battery_sim = world.start("BatterySim", step_size=1, use_async=use_async_battery)
    ev_sim = world.start("EVSim", step_size=1)
    ctrl_sim = world.start("ControllerSim", step_size=1)
    webvis = world.start("WebVis", start_date=START.isoformat(sep=" "), step_size=1)
    csv_sim_writer = world.start(
        "CSV_writer",
        start_date=START.isoformat(sep=" "),
        date_format="%Y-%m-%d %H:%M:%S",
        output_file="results.csv",
    )

    griddata = gridfactory.create_net()

    pv_model = pv_sim.PVSim.create(1, **PVMODEL_PARAMS)[0]
    grid = pp_sim.Grid(net=griddata["net"]).children
    if not use_real_battery:
        battery = battery_sim.Battery.create(
            1, e_max_mwh=1000 / 1e6, p_max_gen_mw=3000 / 1e6, p_max_load_mw=3000 / 1e6
        )[0]
    else:
        host = os.getenv("HOST", "localhost")
        if not host:
            raise ValueError("HOST environment variable not set")
        port_str = os.getenv("PORT", "5001")
        if not port_str:
            raise ValueError("PORT environment variable not set")
        try:
            port = int(port_str)
        except ValueError | TypeError:
            raise ValueError("PORT environment variable is not a valid integer")

        battery = battery_sim.Battery.create(1, host=host, port=port)[0]

    ev_model = ev_sim.EVSim.create(1, p_charge_mw=2500 / 1e6)[0]
    controller = ctrl_sim.BatteryDirector.create(1)[0]
    csv_writer = csv_sim_writer.CSVWriter(buff_size = 1)

    node_bat = get_node_by_id(grid, "Bus", griddata["id_battery"])
    node_ev = get_node_by_id(grid, "Bus", griddata["id_ev"])
    node_pv = get_node_by_id(grid, "Bus", griddata["id_pv"])
    # there should only be one external grid, but the id is not the same as the one of the connected bus
    node_grid = [elem for elem in grid if elem.type == "ExternalGrid"][0]

    world.connect(pv_model, node_pv, ("P[MW]", "P_gen[MW]"))
    world.connect(battery, node_bat, ("P_load[MW]", "P_load[MW]"))
    world.connect(battery, node_bat, ("P_gen[MW]", "P_gen[MW]"))
    world.connect(ev_model, node_ev, ("P_load[MW]", "P_load[MW]"))
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

    world.connect(battery, csv_writer, ("P[MW]", "Battery_P[MW]"))
    world.connect(ev_model, csv_writer, ("P_load[MW]", "EV_P_load[MW]"))
    world.connect(pv_model, csv_writer, ("P[MW]", "PV_P_gen[MW]"))
    world.connect(controller, csv_writer, ("P_target[MW]", "Controller_P_target[MW]"))
    world.connect(node_grid, csv_writer, ("P[MW]", "Grid_P[MW]"))

    webvis.set_config(
        ignore_types=["Topology", "Grid", "DebugSim", "CSVWriter"],
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
                "cls": "node",
                "attr": "P[MW]",
                "unit": "MW",
                "default": 0.0,
                "min": -1.0,
                "max": 1.0,
            },
            "PVSim": {
                "cls": "gen",
                "attr": "P[MW]",
                "unit": "MW",
                "default": 0.0,
                "min": 0.0,
                "max": PVMODEL_PARAMS["scale_factor"],
            },
            "Battery": {
                "cls": "storage",
                "attr": "SoC",
                "unit": "SoC",
                "default": 0.0,
                "min": 0.0,
                "max": 1.0,
            },
            "BatteryDirector": {
                "cls": "special",
                "attr": "P_target[MW]",
                "unit": "MW",
                "default": 0.5,
                "min": -1.0,
                "max": 1.0,
            },
            "EVSim": {
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
    world.connect(ev_model, vis_topo, ("E[MWH]", "E[MWH]"))
    world.connect(battery, vis_topo, ("SoC", "SoC"))

    mu.connect_many_to_one(
        world, [e for e in grid if e.type == "Bus"], vis_topo, ("P[MW]", "P[MW]")
    )
