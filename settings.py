import json
import os
import constants

SETTINGS_FILE = "settings.json"

def load_settings():
    settings = {
        "MAX_CURRENT_MA": 10000,
        "MAX_VOLTAGE_MV": 60000,
        "MIN_FREQ_HZ": 1,
        "MAX_FREQ_HZ": 1000,
        "MAX_DATAPOINTS": 60,
        "INACTIVITY_TIMEOUT_MS": 3000,
        "ACK_TIMEOUT_MS": 2000,
        "GRAPH_UPDATE_MS": 500,
        "baudrate": 115200,
        "is_dark_mode": False,
        "unit_mode": "mV/mA",
        "show_legends": True,
        "show_titles": True,
        "show_timestamps": True,
        "show_raw_telemetry": True
    }
    
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                settings.update(json.load(f))
        except Exception as e:
            print(f"Error loading {SETTINGS_FILE}: {e}")

    constants.MAX_CURRENT_MA = settings["MAX_CURRENT_MA"]
    constants.MAX_VOLTAGE_MV = settings["MAX_VOLTAGE_MV"]
    constants.MIN_FREQ_HZ = settings["MIN_FREQ_HZ"]
    constants.MAX_FREQ_HZ = settings["MAX_FREQ_HZ"]
    constants.MAX_DATAPOINTS = settings["MAX_DATAPOINTS"]
    constants.INACTIVITY_TIMEOUT_MS = settings["INACTIVITY_TIMEOUT_MS"]
    constants.ACK_TIMEOUT_MS = settings["ACK_TIMEOUT_MS"]
    constants.GRAPH_UPDATE_MS = settings["GRAPH_UPDATE_MS"]

    return settings

def save_settings(settings):
    settings["MAX_CURRENT_MA"] = constants.MAX_CURRENT_MA
    settings["MAX_VOLTAGE_MV"] = constants.MAX_VOLTAGE_MV
    settings["MIN_FREQ_HZ"] = constants.MIN_FREQ_HZ
    settings["MAX_FREQ_HZ"] = constants.MAX_FREQ_HZ
    settings["MAX_DATAPOINTS"] = constants.MAX_DATAPOINTS
    settings["INACTIVITY_TIMEOUT_MS"] = constants.INACTIVITY_TIMEOUT_MS
    settings["ACK_TIMEOUT_MS"] = constants.ACK_TIMEOUT_MS
    settings["GRAPH_UPDATE_MS"] = constants.GRAPH_UPDATE_MS
    
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"Error saving {SETTINGS_FILE}: {e}")