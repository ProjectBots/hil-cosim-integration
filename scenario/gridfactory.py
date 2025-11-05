import pandapower as pp
from typing import Any

""" Data for household wiring (Copper 2.5 mm^2), not used atm because sources for values give conflicting information
HOUSEHOLD_WIRE_DATA = {
    "r_ohm_per_km": 7.41,
    "x_ohm_per_km": 0.12,
    "c_nf_per_km": 210,
    "max_i_ka": 0.020,
}
"""


def create_net() -> dict[str, Any]:
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

    return {
        "net": net,
        "id_center": bcenter,
        "id_battery": bbat,
        "id_ev": bev,
        "id_pv": bpv,
        "id_grid": bgrid,
    }
