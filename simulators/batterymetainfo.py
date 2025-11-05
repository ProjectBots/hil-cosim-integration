
BATTERY_MODEL_META_DATA = {
    "api_version": "3.0",
    "type": "time-based",
    "models": {
        "BatteryModel": {
            "public": True,
            "params": ["e_max_mwh", "p_max_gen_mw", "p_max_load_mw"],
            "non-trigger": ["P_target[MW]"],
            "persistent": ["P_gen[MW]", "P_load[MW]", "SoC", "P[MW]"], # SoC = state of charge
        },
    },
}