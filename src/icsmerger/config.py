import os
import json
from appdirs import user_data_dir
#from tkinter import messagebox

# Define application name and author for appdirs
APP_NAME = "icsmerger"
APP_AUTHOR = "Kirk Coombs"

# Get configuration file directory (per-OS)
def get_appdir():
    config_dir = user_data_dir(APP_NAME, APP_AUTHOR)
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, 'config.json')

# Get save file directory (per-OS)
def get_outdir():
    config_dir = user_data_dir(APP_NAME, APP_AUTHOR)
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, 'out.ics')

# Load configuration from file
def load_config(config_path):
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            return {}
    except Exception as e:
#        messagebox.showerror("Error", f"Failed to load configuration file: {e}")
        return {}

# Save configuration to file
def save_config(config, config_path):
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        pass
#        messagebox.showerror("Error", f"Failed to save configuration file: {e}")
