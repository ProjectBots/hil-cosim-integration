import mosaik

from datetime import datetime

import pandapower as pp

BATTERY_CAPACITY_MWH = 0.1

IS_REALTIME = False

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


sim_config: mosaik.SimConfig = {
    "BatterySim": {
        "python": "simulators.batterysim:BatteryModel",
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
}

def main():
    world = mosaik.World(sim_config)

    create_scenario(world)

    world.run(until=100 * STEP_SIZE_SECONDS, rt_factor=1.0 if IS_REALTIME else None) #TODO: figure out how to get rid of behind schedule warnings when rt_factor is set


def create_scenario(world):
    pv_sim = world.start("PVSim", step_size=STEP_SIZE_SECONDS, sim_params=PVSIM_PARAMS)
    pp_sim_pv_bat = world.start("PPSim", step_size=STEP_SIZE_SECONDS)
    pp_sim_bat_ev = world.start("PPSim", step_size=STEP_SIZE_SECONDS)
    battery_sim = world.start("BatterySim", step_size=STEP_SIZE_SECONDS)
    ev_sim = world.start("EVSim", step_size=STEP_SIZE_SECONDS)

    pv_model = pv_sim.PVSim.create(1, **PVMODEL_PARAMS)[0]

    line_pv_bat = pp_sim_pv_bat.Grid(net=get_net_pv_bat()).children
    node_pv_gen = [elem for elem in line_pv_bat if "ControlledGen" == elem.type][0]
    node_bat_load = [elem for elem in line_pv_bat if "ExternalGrid" == elem.type][0]

    line_bat_ev = pp_sim_bat_ev.Grid(net=get_net_bat_ev()).children
    node_bat_gen = [elem for elem in line_bat_ev if "ControlledGen" == elem.type][0]
    node_ev_load = [elem for elem in line_bat_ev if "Load" == elem.type][0]

    battery = battery_sim.BatteryModel.create(1, e_max_mwh=BATTERY_CAPACITY_MWH)[0]

    ev = ev_sim.EVModel.create(1)[0]

    # TODO: add WebVis for visualization
    # TODO: sync what ev is actually consuming with the battery

    world.connect(pv_model, node_pv_gen, "P[MW]")
    world.connect(node_bat_load, battery, ("P[MW]", "P_in[MW]"))
    world.connect(battery, node_bat_gen, ("P_out[MW]", "P[MW]"))
    world.connect(node_ev_load, ev, "P[MW]")





def get_net_pv_bat():
    net = pp.create_empty_network()

    bus_pv = pp.create_bus(net, vn_kv=0.23, name="PV_Bus")
    bus_batt = pp.create_bus(net, vn_kv=0.23, name="Battery_Bus")

    pp.create_line_from_parameters(
        net,
        from_bus=bus_pv,
        to_bus=bus_batt,
        length_km=0.02,
        r_ohm_per_km=HOUSEHOLD_WIRE_DATA["r_ohm_per_km"],
        x_ohm_per_km=HOUSEHOLD_WIRE_DATA["x_ohm_per_km"],
        c_nf_per_km=HOUSEHOLD_WIRE_DATA["c_nf_per_km"],
        max_i_ka=HOUSEHOLD_WIRE_DATA["max_i_ka"],
        name="Line_PV_to_Battery",
    )

    pp.create_gen(net, bus=bus_pv, p_mw=0.0, name="PV_Generator")

    #pp.create_load(net, bus=bus_batt, p_mw=0.0, q_mvar=0, name="Battery_Load")

    pp.create_ext_grid(net, bus=bus_pv, vm_pu=1.0, name="Grid_Connection_PV")

    return net


def get_net_bat_ev():
    net = pp.create_empty_network()

    bus_batt = pp.create_bus(net, vn_kv=0.23, name="Battery_Bus")
    bus_ev = pp.create_bus(net, vn_kv=0.23, name="EV_Bus")

    pp.create_line_from_parameters(
        net,
        from_bus=bus_batt,
        to_bus=bus_ev,
        length_km=0.015,
        r_ohm_per_km=HOUSEHOLD_WIRE_DATA["r_ohm_per_km"],
        x_ohm_per_km=HOUSEHOLD_WIRE_DATA["x_ohm_per_km"],
        c_nf_per_km=HOUSEHOLD_WIRE_DATA["c_nf_per_km"],
        max_i_ka=HOUSEHOLD_WIRE_DATA["max_i_ka"],
        name="Line_Battery_to_EV",
    )

    pp.create_gen(net, bus=bus_batt, p_mw=0.0, name="Battery_Inverter", slack=True)
    pp.create_load(net, bus=bus_ev, p_mw=0.0, q_mvar=0, name="EV_Load")

    return net


if __name__ == "__main__":
    main()
