import os
import logging
import platform
import subprocess
import json
import hashlib
from pathlib import Path

# Get configuration file directory (per-OS)
def get_appdir(self):
    config_dir = Path(self.paths.config)
    logging.info(f"config_dir: {config_dir}")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, 'config.json')

# Get save file directory (per-OS)
def get_outdir(self):
    get_outdir = Path(self.paths.cache)
    logging.info(f"out_dir: {get_outdir}")
    os.makedirs(get_outdir, exist_ok=True)
    return os.path.join(get_outdir, 'out.ics')

# Load configuration from file
def load_config(self):
    try:
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return json.load(f)
        else:
            logging.debug(f"Configuration file does not exist: {self.config_path}")
            return {}
    except Exception as e:
        message = f"Failed to load configuration file: {e}"
        logging.critical(message)
        self.main_window.info_dialog("Error", message)
        return {}

# Save configuration to file
def save_config(self, config):
    config_path = get_appdir(self)
    try:
        with open(config_path, 'w') as f:
             json.dump(config, f, indent=4)
        self.main_window.info_dialog('Save Configuration', 'Configuration saved successfully.')
    except Exception as e:
        message = f"Failed to save configuration file: {e}"
        logging.error(message)
        self.main_window.error_dialog('Error', message)

# Create a new file
def create_file(self, file):
    try:
        with open(file, 'w') as file:
             file.write('')
        # self.main_window.info_dialog('New File', 'New file created successfully.')
    except Exception as e:
        message = f'Failed to create file: {file}'
        logging.error(message)
        self.main_window.error_dialog('Error', message)

# Open file_path in the default application
def open_output_file(self, file_path):
    try:
        if platform.system() == 'Windows':
            subprocess.call(f'start "" "{file_path}"', shell=True)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.call(['open', file_path])
        elif platform.system() == 'Linux':
            subprocess.call(['xdg-open', file_path])
        else:
           self.main_window.info_dialog("Unsupported OS", "Your operating system is not supported for this operation.")
    except Exception as e:
        logging.error(f"Error opening file: {e}")

# Validate the shasum of contents using sha256
def sha_check(contents, sha256):
    calculated_shasum = hashlib.sha256(contents).hexdigest()

    # Check the shasum
    if calculated_shasum == sha256:
        logging.debug(f"sha_check succeeded: calculated_shasum: {calculated_shasum} == sha256: {sha256}")
        return True
    else:
        logging.error(f"sha_check failed: calculated_shasum: {calculated_shasum} != sha256: {sha256}")
        return False
    
def save_file(file, save_path, event):
    try:
        with open(save_path, "wb") as f:
            f.write(file)
        logging.debug(f"File saved: {save_path}")
    except Exception as e:
        logging.error(f"Error saving file: {e}")
    event.set()