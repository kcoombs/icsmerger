import platform
import logging
import requests
import toga
import asyncio
import json
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER
from pathlib import Path
from threading import Thread, Event
from .__init__ import __version__
from .fileio import open_output_file, sha_check, save_file

# "main" or "dev"
BRANCH = "dev"

async def update_checker(self):
    update = Updater(self, __version__)
    
    logging.debug(f"\n\tUpdate check result:\n\t"
                    f"check_success: {update.check_success}\n\t"
                    f"update_available: {update.update_available}\n\t"
                    f"local_version: {update.local_version}\n\t"
                    f"server_version: {update.server_version}\n\t"
                    f"message: {update.message}"
                )

    if update.check_success and update.update_available:
        logging.debug("Update check was successful, and an update is available.")
        update.updater_ui.show()
        result = await update.updater_ui.update_available(update.local_version, update.server_version)
        await update.update_helper(update, result)
        update.updater_ui.close()
        return 
    elif update.check_success and not update.update_available:
        logging.debug("Update check success, and no update available.")
        return 
    elif not update.check_success:
        logging.debug(f"Update check failed: {update.message}")
        if not update.automatic:
            update.updater_ui.show()
            await update.updater_ui.update_check_failed(update.message)
            update.updater_ui.close()
        return 
    logging.debug("There is a problem with the update logic.")

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
            "platform" : "Platform unsupported for update checking.",
            "check_error" : "Unable to check for updates: ",
            "no_update" : "No update available.",
            "update_available" : "Update available.",
            "download_error" : "Unable to download the update file: ",
            "download_success" : "Update downloaded successfully.",
            "sha_fail" : "The downloaded file did not have the expected contents. The download may be corrupted."
    }
 
    def __init__(self, main_window, local_version):
        self.version_url = f"{Updater.version_base_url}/{Updater.branches[BRANCH]}/{Updater.version_file}"
        self.check_success = False
        self.update_success = False
        self.update_available = False
        self.update_file_name = None
        self.update_file_base_name = "ICSMerger"
        self.update_file_extension = None
        self.update_file_platform = None
        self.platform = None
        self.server_version = None
        self.local_version = local_version
        self.message = None
        self.file = None
        self.sha256 = None
        self.exit = True
        self.save_finished = Event()
        self.file_size = 0
        self.downloaded_size = 0
        self.automatic = True                   # For future use, to silent check failure on automatic updates

        if platform.system() == 'Windows':
            self.platform = "windows"
            self.update_file_extension = ".msi"
            self.update_file_platform = "Windows"
        elif platform.system() == 'Darwin':  # macOS
            self.platform = "macos"
            self.update_file_extension = ".dmg"
            self.update_file_platform = "MacOS"
        # elif platform.system() == 'Linux':
        #     self.platform = "linux"
        #     self.update_file_extension = ".deb"
        #     self.update_file_platform = "Linux"
        else:
            logging.error(Updater.messages["platform"])
            self.message = Updater.messages["platform"]
            self.check_success = False
            return

        self.updater_ui = UpdaterUI(main_window)

        self.check_for_updates()
        return

    async def update_helper(self, update, result):
        logging.debug(f"update_helper: {result}, {self}")
        if result:
            logging.debug("User elected to update.")
            update_thread = Thread(target=self.download_update)
            update_thread.start()
            progress_started = False
            while update_thread.is_alive():
                if self.file_size == 0:
                    # File size not yet known
                    pass
                elif self.file_size != 0 and progress_started == False:
                    # Create progress bar
                    progress_started = True
                    update.updater_ui.start_progress(self.file_size)
                    # logging.debug(f"Start progress bar with: {self.file_size}")
                else:
                    # Update progress bar
                    update.updater_ui.update_progress(self.downloaded_size)
                    # logging.debug(f"{self.downloaded_size} of {self.file_size} downloaded.")
                await asyncio.sleep(0.01)
            update.updater_ui.stop_progress()
            if self.update_success:
                # self.progress_label.text = 'Downloading Complete'
                logging.debug("Download successful.")
                if (await update.updater_ui.install_update()):
                    # User elected to install the update, save the file and open it
                    save_base_path = Path(toga.App.app.paths.config)
                    logging.debug(f"Save path: {save_base_path}")
                    logging.debug(f"Save file name: {self.update_file_name}")
                    save_path = f"{save_base_path}/{self.update_file_name}"
                    logging.debug(f"Save file path: {save_path}")
                    if save_path:
                        save_thread = Thread(target=save_file, args=(self.file, save_path, self.save_finished))
                        save_thread.start()
                        self.save_finished.wait()
                        self.save_finished.clear()
                        logging.debug(f"Update file saved to {save_path}. Opening file and exiting.")
                        open_output_file(self, save_path)
                    else:
                        logging.error(f"Save path {save_path} not found. Exiting.")
                    toga.App.app.exit()
                else:
                    # User elected not to install the update
                    if (await update.updater_ui.save_update()):
                        # User elected to save the update file
                        file_path = await update.updater_ui.save_update_file_path(self.update_file_name)
                        if file_path:
                            save_thread = Thread(target=save_file, args=(self.file, file_path, self.save_finished))
                            save_thread.start()
                            self.save_finished.wait()
                            self.save_finished.clear()
                            await update.updater_ui.save_success()
                            logging.debug(f"Update file saved to {file_path}.")
                        return
                    else:
                        # User elected not to save the update file
                        logging.debug("User elected to not save downloaded file.")
                        return
            else:
                logging.error("Update download failed.")
                await update.updater_ui.update_download_failed()
                return
        else:
            logging.debug("User elected to not update.")
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
                # self.local_version="0.0.9"
                # self.server_version="0.2.0"
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
            else:
                self.check_success = False
                self.message = Updater.messages["check_error"] + "\nHTTP Status: " + str(response.status_code)
                logging.error(self.message)
                return
        except requests.exceptions.RequestException as e:
            self.check_success = False
            self.message = Updater.messages["check_error" + str(e)]
            logging.error(self.message)
            return

    # def download_update(self, progress_box):

    def download_update(self):
        # URL of the new application files on the server
        self.update_file_name = self.update_file_base_name + "-" + self.server_version + "-" + self.update_file_platform + self.update_file_extension
        update_url = f"{Updater.update_base_url}/v{self.server_version}/{self.update_file_name}"
        logging.info(f"Downloading update from: {update_url}")

        # Download the new application files
        try:
            response = requests.get(update_url, stream=True)
            if response.status_code == 200:
                self.file_size = int(response.headers.get('content-length', 0))
                # logging.debug(f"File size: {self.file_size}")

                chunks = []
                for chunk in response.iter_content(1024):
                    chunks.append(chunk)
                    self.downloaded_size += len(chunk)
                    # logging.debug(f"Chunk size: {len(chunk)}, Total size: {self.downloaded_size}")
                
                content = b''.join(chunks)

                sha_check(content, self.sha256)
                if sha_check:
                    # Download and check success
                    self.update_success = True
                    self.message = Updater.messages["download_success"]
                    logging.info(self.message)
                    self.file = content
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

class UpdaterUI():
    def __init__(self, main_window):
        window_width, window_height = 400, 150
        screen_width, screen_height = main_window.screens[0].size
        position_x = (screen_width - window_width) // 2
        position_y = (screen_height - window_height) // 2
        self.update_window = toga.Window(title="Update Checker", resizable=False, closable=True, minimizable=True, size=(window_width, window_height), position=(position_x, position_y))

        self.progress_label = toga.Label('Downloading Update', style=Pack(alignment=CENTER, padding=10, font_weight='bold'))
        self.progress_bar = toga.ProgressBar(style=Pack(alignment=CENTER, padding=(10, 60, 10, 60), flex=1))
                
        self.progress_box = toga.Box(style=Pack(direction=COLUMN, alignment=CENTER, padding=10, flex=1), children=[
            toga.Box(style=Pack(direction=ROW, alignment=CENTER), children=[toga.Label('', style=Pack(padding=5))]),
            toga.Box(style=Pack(direction=ROW, alignment=CENTER), children=[self.progress_label]),
            toga.Box(style=Pack(direction=ROW, alignment=CENTER), children=[self.progress_bar]),
            toga.Box(style=Pack(direction=ROW, alignment=CENTER), children=[toga.Label('', style=Pack(padding=5))]),
            # toga.Box(style=Pack(direction=ROW, alignment=CENTER), children=[
            #     messages := toga.Label('PLACEHOLDER', style=Pack(alignment=CENTER, padding=10)),
            #     ]),
            # toga.Box(style=Pack(direction=ROW, alignment=CENTER), children=[
            #     button1 := toga.Button(text="BUTTON1", style=Pack(alignment=CENTER, padding=10)),
            #     button2 := toga.Button(text="BUTTON2", style=Pack(alignment=CENTER, padding=10))
            #     ])
        ])
        self.update_window.content = self.progress_box
        return

    def show(self):
        self.update_window.show()
        return

    def close(self):
        self.update_window.close()
        return

    async def update_available(self, local_version, server_version):
        result = await self.update_window.question_dialog("Update Check", f"Update available, you have {local_version}, {server_version}, available. Download update now?")
        return result
    
    async def update_check_failed(self, message):
        result = await self.update_window.error_dialog("Update Check", f"Update check failed:\n{message}")
        return result

    async def update_download_failed(self):
        result = await self.update_window.error_dialog("Error", "Update download failed.")
        return result

    async def install_update(self):
        result = await self.update_window.question_dialog("Update File Downloaded", "Update file downloaded successfully. Exit this program and open the update file?")
        return result

    async def save_update(self):
        result = await self.update_window.question_dialog("Update File Downloaded", "Save downloaded file?")
        return result

    async def save_update_file_path(self, filename):
        result = await self.update_window.save_file_dialog("Save Update File", suggested_filename=filename)
        return result

    async def save_success(self):
        result = await self.update_window.info_dialog("Save Update File", "Update file saved successfully.")    
        return result

    def start_progress(self, size):
        self.progress_bar.max = size
        self.progress_bar.start()
        return
    
    def update_progress(self, size):
        self.progress_bar.value = size
        return
    
    def stop_progress(self):
        self.progress_bar.stop()
        return