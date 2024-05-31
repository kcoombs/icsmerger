import platform
import logging
import requests
import toga
import json
from pathlib import Path
from .__init__ import __version__
from .fileio import open_output_file, sha_check
from threading import Thread

# "main" or "dev"
BRANCH = "dev"

async def update_checker(self):
    update = Updater(__version__)
    
    logging.debug(f"\n\tUpdate check result:\n\t"
                    f"check_success: {update.check_success}\n\t"
                    f"update_available: {update.update_available}\n\t"
                    f"local_version: {update.local_version}\n\t"
                    f"server_version: {update.server_version}\n\t"
                    f"message: {update.message}"
                )

    if update.check_success and update.update_available:
        logging.debug("Update check success, and update available.")
        dialog_result = await toga.App.app.main_window.question_dialog("Update Check", f"Update available, you have {update.local_version}, {update.server_version}, available. Download update now?")
        await update.update_helper(dialog_result)
        return 
    elif update.check_success and not update.update_available:
        logging.debug("Update check success, and no update available.")
        return 
    elif not update.check_success:
        logging.debug(f"Update check failed: {update.message}")
        toga.App.app.main_window.error_dialog("Update Check", f"Update check failed:\n{update.message}")
        return 
    logging.debug(f"Problem in update logic.")

class Updater():
    branches = {
        "main" : "main",
        "dev" : "icsmerge-dev"
    }
    version_base_url = "https://raw.githubusercontent.com/kcoombs/icsmerger"
    version_file = "versions.json"
    update_base_url = "https://github.com/kcoombs/icsmerger/releases/download"
    update_base_file = "ICS.Merger-"
    messages = {
            "platform" : "Unsupported platform for update checking.",
            "check_error" : "Unable to check for updates: ",
            "no_update" : "No update available.",
            "update_available" : "Update available.",
            "download_error" : "Unable to download update file: ",
            "download_success" : "Update downloaded successfully.",
            "sha_fail" : "Downloaded file did not have the expected contents. Download possibly corrupted."
    }
 
    def __init__(self, local_version):
        self.version_url = f"{Updater.version_base_url}/{Updater.branches[BRANCH]}/{Updater.version_file}"
        self.check_success = False
        self.update_success = False
        self.update_available = False
        self.update_file_name = None
        self.update_file_base_name = "ICS.Merger-"
        self.update_file_extension = None
        self.platform = None
        self.server_version = None
        self.local_version = local_version
        self.message = None
        self.file = None
        self.sha256 = None
        self.exit = True

        if platform.system() == 'Windows':
            self.platform = "windows"
            self.update_file_extension = ".msi"
        elif platform.system() == 'Darwin':  # macOS
            self.platform = "macos"
            self.update_file_extension = ".dmg"
        # elif platform.system() == 'Linux':
        #     self.platform = "linux"
        #     self.update_file_extension = ".deb"
        else:
            logging.error(Updater.messages["platform"])
            self.message = Updater.messages["platform"]
            self.check_success = False
            return

        self.check_for_updates()
        return

    def check_for_updates(self):
        # Download the version file
        try:
            response = requests.get(self.version_url)
            logging.info(f"Checking update file at: {self.version_url}")

            # If download was successful, check the version
            if response.status_code == 200:
                versions = json.loads(response.text)
                self.server_version = versions[-1]['version']
                self.sha256 = versions[-1]['shasum'][self.platform]
                logging.info(f"Local version: {self.local_version}, Server version: {self.server_version}, Server sha256: {self.sha256}")

                ## FOR TESTING ##
                self.local_version="0.0.9"
                # self.server_version="0.0.9"
                ## FOR TESTING ##
                # If the server version is newer, download the update
                if self.server_version > self.local_version:
                    self.check_success = True
                    self.update_available = True
                    self.message = self.messages["update_available"]
                    logging.info(f"Update available: {self.server_version}")
                    return

                # Otherwise, no update is available
                else:
                    self.check_success = True
                    self.update_available = False
                    self.message = Updater.messages["no_update"]
                    logging.info(self.message)
                    return
        except requests.exceptions.RequestException as e:
            self.check_success = False
            self.message = Updater.messages["check_error" + str(e)]
            logging.error(self.message)
            return

    def download_update(self):
        # URL of the new application files on the server
        self.update_file_name = self.update_file_base_name + self.server_version + self.update_file_extension
        update_url = f"{Updater.update_base_url}/v{self.server_version}/{self.update_file_name}"
        logging.info(f"Downloading update from: {update_url}")

        # window_width, window_height = 300, 200
        # screen_width, screen_height = toga.App.screens[0].size
        # position_x = (screen_width - window_width) // 2
        # position_y = (screen_height - window_height) // 2
        # self.download_window = toga.Window(title="Update Download", resizable=False, closable=False, minimizable=True, closeable=False, size=(window_width, window_height), position=(position_x, position_y))
        # self.download_window = toga.Window(title="Update Download", resizable=False, closable=False, minimizable=True, closeable=False, size=(window_width, window_height))

        # Download the new application files
        try:
            response = requests.get(update_url, stream=True)
            if response.status_code == 200:
                # logging.debug(f"Response headers: {response.headers}")
                # file_size = int(response.headers.get('Content-Length', 0))
                
                # # Create a progress bar
                # self.progress_bar = toga.ProgressBar(max=file_size)

                # # Create a box to hold the progress bar and a label
                # self.progress_box = toga.Box()
                # self.progress_label = toga.Label('Downloading update...')
                # self.progress_box.add(self.progress_label)
                # self.progress_box.add(self.progress_bar)

                # # Add the box to the main window
                # self.download_window.content = self.progress_box
                # self.download_window.show()

                # # Update the progress bar as the file downloads
                # downloaded = 0
                # file_content = b""
                # for chunk in response.iter_content(chunk_size=1024):
                #     if chunk:
                #         downloaded += len(chunk)
                #         file_content += chunk
                #         self.progress_bar.value = downloaded

                sha_check(response.content, self.sha256)
                if sha_check:
                    # Download and check success
                    self.update_success = True
                    self.message = Updater.messages["download_success"]
                    logging.info(self.message)
                    self.file = response.content
                    return
                else:
                    # Download failure
                    self.update_success = False
                    self.message = Updater.messages["sha_fail"]
                    logging.error(self.message)
                    return
            else:
                self.update_success = False
                self.message = f"{Updater.messages["download_error"]} {str(e)}"
                logging.error(self.message)
                return
        except requests.exceptions.RequestException as e:
            self.update_success = False
            self.message = f"{Updater.messages["download_error"]} {str(e)}"
            logging.error(self.message)
            return

    async def update_helper(self, dialog_result):
        logging.debug(f"update_helper: {dialog_result}, {self}")
        if dialog_result:
            logging.debug("User elected to update.")
            ## ADD THREADING ##
            ## ADD DOWNLOAD PROGRESS CHECK ##
            self.download_update()
            if self.update_success:
                logging.debug("Download successful, saving.")
                save_base_path = Path(toga.App.app.paths.config)
                logging.debug(f"Save path: {save_base_path}")
                logging.debug(f"Save file name: {self.update_file_name}")
                save_path = f"{save_base_path}/{self.update_file_name}"
                logging.debug(f"Save file path: {save_path}")
                ## ADD THREADING ##
                if save_path:
                    with open(save_path, "wb") as f:
                        f.write(self.file)
                    logging.debug(f"Update file saved to {save_path}.")
                    # toga.App.app.main_window.info_dialog("Update", "Update downloaded successfully. Please close this application to install the update.")
                    dialog_result1 = await toga.App.app.main_window.question_dialog("Update File Downloaded", "Update file downloaded successfully. Exit this program and open the update file?")
                    if dialog_result1:
                        open_output_file(self, save_path)
                        toga.App.app.exit()
                    else:
                        dialog_result2 = await toga.App.app.main_window.question_dialog("Update File Downloaded", "Save downloaed file?")
                        if dialog_result2:
                            file_path = await toga.App.app.main_window.save_file_dialog("Save Update File", suggested_filename=self.update_file_name)
                            if file_path:   
                                with open(file_path, 'wb') as f:
                                    f.write(self.file)
                                    toga.App.app.main_window.info_dialog("Save Update File", "Update file saved successfully.")    
                                    logging.debug(f"Update file saved to {file_path}.")
                            return
                        else:
                            logging.debug("User elected to not save downloaded file.")
                            return
                else:
                    logging.error(f"Save path {save_path} not found.")
                    return
            else:
                logging.error("Update failed.")
                toga.App.app.main_window.error_dialog("Error", "Update failed.")
                return
        else:
            logging.debug("User elected to not update.")
            return
        