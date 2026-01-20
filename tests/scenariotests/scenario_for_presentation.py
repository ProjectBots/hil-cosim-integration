
import os
from typing import Any
from datetime import datetime

import dotenv

import mosaik
import mosaik.util as mu
import pandapower as pp

from modbushil.configurationmanager import ConfigurationManager

import tests.helpers.helperutils as hu


""" Scenario test for presentation purposes. 

This scenario simulates a simple grid with a PV system, a battery, and an EV.
The battery can either be a real Modbus-connected battery or a simulated one.
The battery is controlled by a simple controller that adjusts its target power
based on the grid power flow.

Please setup a .env file in the workspace-root directory with the following
variables:
USE_REAL_BATTERY=True
HOST=<IP_ADDRESS_OF_MODBUS_BATTERY>
PORT=<PORT_OF_MODBUS_BATTERY>

You can use the provided Modbus battery emulator for testing purposes.
It will use the same .env file for HOST and PORT.
(HOST should probably be "localhost" and PORT can be any free port, e.g., 5020)

If you are going to use an actual Battery HIL setup, you most likely have to adjust the
MODBUS_HIL_CONFIG_BATTERY in this file to match your Modbus register mapping.

"""

START = datetime(2020, 6, 1, 10, 0, 0)

STEP_SIZE_SECONDS = 0.5
STEPS_TOTAL = 500

MODBUS_HIL_CONFIG_BATTERY = {
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


def main() -> None:
    use_real_battery = hu.get_bool_env_var("USE_REAL_BATTERY", False)

    if use_real_battery:
        ConfigurationManager.register_model("Battery", MODBUS_HIL_CONFIG_BATTERY)

    sim_config: mosaik.SimConfig = {
        "BatterySim": {
            "python": "modbushil.siminterface:ModbusSimInterface"
            if use_real_battery
            else "tests.simulators.batterysim:BatteryModel",
        },
        "PPSim": {
            "python": "mosaik_components.pandapower:Simulator",
        },
        "PVSim": {
            "python": "mosaik_components.pv.pvgis_simulator:PVGISSimulator",
        },
        "EVSim": {
            "python": "tests.simulators.evsim:EVModel",
        },
        "ControllerSim": {
            "python": "tests.simulators.controllersim:BatteryControllerSim",
        },
        "WebVis": {
            "cmd": "mosaik-web -s 127.0.0.1:8000 %(addr)s",
        },
        "DebugSim": {
            "python": "tests.simulators.debugsim:DebugSim",
        },
        "CSV_writer": {
            "python": "mosaik_csv_writer:CSVWriter",
        },
    }

    world = mosaik.World(sim_config, time_resolution=STEP_SIZE_SECONDS)

    use_async_battery = hu.get_bool_env_var("USE_ASYNC_BATTERY", True)

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

    net = pp.create_empty_network()

    bcenter = pp.create_bus(net, vn_kv=0.4, name="center")
    bbat = pp.create_bus(net, vn_kv=0.4, name="battery")
    bev = pp.create_bus(net, vn_kv=0.4, name="ev")
    bpv = pp.create_bus(net, vn_kv=0.4, name="pv")
    bgrid = pp.create_bus(net, vn_kv=0.4, name="grid")

    pp.create_lines(
        net=net,
        from_buses=[bcenter, bcenter, bcenter, bcenter],
        to_buses=[bbat, bev, bpv, bgrid],
        length_km=[0.01, 0.02, 0.20, 1.0],
        std_type="NAYY 4x50 SE",
        names=[
            "line_center_battery",
            "line_battery_ev",
            "line_battery_pv",
            "line_center_grid",
        ],
    )

    pp.create_ext_grid(net, bus=bgrid, vm_pu=1.0, name="Grid_Connection")

    pv_model = pv_sim.PVSim.create(1, **PVMODEL_PARAMS)[0]
    grid = pp_sim.Grid(net=net).children
    if not use_real_battery:
        battery = battery_sim.Battery.create(
            1, e_max_mwh=1000 / 1e6, p_max_gen_mw=3000 / 1e6, p_max_load_mw=3000 / 1e6
        )[0]
    else:
        host = os.getenv("HOST")
        if not host:
            raise ValueError("HOST environment variable not set")
        port_str = os.getenv("PORT")
        if not port_str:
            raise ValueError("PORT environment variable not set")
        try:
            port = int(port_str)
        except ValueError | TypeError:
            raise ValueError("PORT environment variable is not a valid integer")

        battery = battery_sim.Battery.create(1, host=host, port=port)[0]

    ev_model = ev_sim.EVSim.create(1, p_charge_mw=2500 / 1e6)[0]
    controller = ctrl_sim.BatteryDirector.create(1)[0]
    csv_writer = csv_sim_writer.CSVWriter(buff_size=1)

    node_bat = get_node_by_id(grid, "Bus", bbat)
    node_ev = get_node_by_id(grid, "Bus", bev)
    node_pv = get_node_by_id(grid, "Bus", bpv)
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

    # TODO: figure out how to get rid of behind schedule warnings when rt_factor is set
    world.run(
        until=STEPS_TOTAL,
        rt_factor=1.0 if hu.get_bool_env_var("USE_REAL_BATTERY", False) else None,
    )

if __name__ == "__main__":
    dotenv.load_dotenv()
    main()
