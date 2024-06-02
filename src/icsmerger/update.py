import platform
import logging
import requests
import toga
import asyncio
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER
import json
from pathlib import Path
from .__init__ import __version__
from .fileio import open_output_file, sha_check, save_file
from threading import Thread, Event

# "main" or "dev"
BRANCH = "main"

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
        logging.debug("Update check was successful, and no update is available.")
        update.download_window.show()
        dialog_result = await update.download_window.question_dialog("Update Check", f"Update available, you have {update.local_version}, {update.server_version}, available. Download update now?")
        await update.update_helper(update, dialog_result)
        update.download_window.close()
        return 
    elif update.check_success and not update.update_available:
        logging.debug("Update check success, and no update available.")
        return 
    elif not update.check_success:
        logging.debug(f"Update check failed: {update.message}")
        update.download_window.show()
        await update.download_window.error_dialog("Update Check", f"Update check failed:\n{update.message}")
        update.download_window.close()
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
        self.update_file_base_name = "ICS.Merger-"
        self.update_file_extension = None
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

        window_width, window_height = 400, 150
        screen_width, screen_height = main_window.screens[0].size
        position_x = (screen_width - window_width) // 2
        position_y = (screen_height - window_height) // 2
        self.download_window = toga.Window(title="Update Checker", resizable=False, closable=True, minimizable=True, closeable=False, size=(window_width, window_height), position=(position_x, position_y))

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
                # self.local_version="0.0.9"
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
        self.update_file_name = self.update_file_base_name + self.server_version + self.update_file_extension
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

    async def update_helper(self, update, dialog_result):
        logging.debug(f"update_helper: {dialog_result}, {self}")
        if dialog_result:
            logging.debug("User elected to update.")

            progress_box = toga.Box(style=Pack(direction=COLUMN, alignment=CENTER, padding=10, flex=1), children=[
                toga.Box(style=Pack(direction=ROW, alignment=CENTER), children=[toga.Label('', style=Pack(padding=5))]),
                toga.Box(style=Pack(direction=ROW, alignment=CENTER), children=[
                    progress_label := toga.Label('Downloading Update', style=Pack(alignment=CENTER, padding=10, font_weight='bold'))
                    ]),
                toga.Box(style=Pack(direction=ROW, alignment=CENTER), children=[
                    progress_bar := toga.ProgressBar(style=Pack(alignment=CENTER, padding=(10, 60, 10, 60), flex=1))
                    ]),
                toga.Box(style=Pack(direction=ROW, alignment=CENTER), children=[toga.Label('', style=Pack(padding=5))]),
                # toga.Box(style=Pack(direction=ROW, alignment=CENTER), children=[
                #     messages := toga.Label('PLACEHOLDER', style=Pack(alignment=CENTER, padding=10)),
                #     ]),
                # toga.Box(style=Pack(direction=ROW, alignment=CENTER), children=[
                #     button1 := toga.Button(text="BUTTON1", style=Pack(alignment=CENTER, padding=10)),
                #     button2 := toga.Button(text="BUTTON2", style=Pack(alignment=CENTER, padding=10))
                #     ])
            ])
            update.download_window.content = progress_box
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
                    progress_bar.max = self.file_size
                    progress_bar.start()
                    # logging.debug(f"Start progress bar with: {self.file_size}")
                else:
                    # Update progress bar
                    progress_bar.value = self.downloaded_size
                    # logging.debug(f"{self.downloaded_size} of {self.file_size} downloaded.")
                await asyncio.sleep(0.01)
            progress_bar.stop()
            if self.update_success:
                progress_label.text = 'Downloading Complete'
                logging.debug("Download successful, saving.")
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
                    logging.debug(f"Update file saved to {save_path}.")
                    dialog_result1 = await update.download_window.question_dialog("Update File Downloaded", "Update file downloaded successfully. Exit this program and open the update file?")
                    if dialog_result1:
                        open_output_file(self, save_path)
                        toga.App.app.exit()
                    else:
                        dialog_result2 = await update.download_window.question_dialog("Update File Downloaded", "Save downloaded file?")
                        if dialog_result2:
                            file_path = await update.download_window.save_file_dialog("Save Update File", suggested_filename=self.update_file_name)
                            if file_path:   
                                save_thread = Thread(target=save_file, args=(self.file, file_path, self.save_finished))
                                save_thread.start()
                                self.save_finished.wait()
                                self.save_finished.clear()
                                await update.download_window.info_dialog("Save Update File", "Update file saved successfully.")    
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
                await update.download_window.error_dialog("Error", "Update failed.")
                return
        else:
            logging.debug("User elected to not update.")
            return
        