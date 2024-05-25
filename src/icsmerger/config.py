import os
import platform
import subprocess
import json
from appdirs import user_data_dir

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
def load_config(main_window, config_path):
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            return {}
    except Exception as e:
        main_window.info_dialog("Error", f"Failed to load configuration file: {e}")
        return {}

# Save configuration to file
def save_config(main_window, config, config_path):
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        main_window.info_dialog("Error", f"Failed to save configuration file: {e}")

# Open the OUT file in the default application
def open_output_file(main_window, file_path):
    print("open_output_file\n")
    try:
        if platform.system() == 'Windows':
            subprocess.call(f'start "" "{file_path}"', shell=True)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.call(['open', file_path])
        elif platform.system() == 'Linux':
            subprocess.call(['xdg-open', file_path])
        else:
           main_window.info_dialog("Unsupported OS", "Your operating system is not supported for this operation.")
    except Exception as e:
        print(f"Error opening file: {e}")