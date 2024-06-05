import os
import asyncio
import platform
import logging
import toga
import toga.paths
import toga.platform
from threading import Thread
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER, TOP
from toga.command import Group
from pathlib import Path
from .__init__ import __version__
from .descriptions import gui_descriptions
from .merge import run_merge
from .analyze import analyze
from .fileio import save_config, load_config, get_appdir, create_file
from .content import show_content_in_window, edit_exclusions_window
from .update import update_checker

class ICSMerger(toga.App):
    def startup(self):

        self.platform = platform.system()
        self.analyze_open = False
        self.merge_open = False

        # Initialize main window
        window_width, window_height = 750, 225
        position_x, position_y = self.window_position(window_width, window_height)
        self.main_window = toga.MainWindow(gui_descriptions["root_title"], resizable=False, size=(window_width, window_height), position = (position_x, position_y))

        # Load configuration
        self.config_path = get_appdir(self)
        self.config = load_config(self)

        # Dictionary to store full file paths
        self.file_paths = {}

        # Main layout box
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=10, flex=1))

        # ICS1 file selection
        ics1_box, self.ics1_entry, self.ics1_clear_button, self.ics1_browse_button, self.ics1_view_button = self.create_file_selection_row("ics1_description", "Optional: Previous iCal (.ics) file", "ics1", "ICS1", ["ICS"])
        main_box.add(ics1_box)

        # ICS2 file selection
        ics2_box, self.ics2_entry, self.ics2_clear_button, self.ics2_browse_button, self.ics2_view_button = self.create_file_selection_row("ics2_description", "Required: New iCal (.ics) file", "ics2", "ICS2", ["ICS"])
        main_box.add(ics2_box)

        # Exclusions file selection
        exclusions_box, self.exclusions_entry, self.exclusions_clear_button, self.exclusions_browse_button, self.exclusions_edit_button = self.create_file_selection_row("exclusions_description", "Optional: Exclusions file", "exclusions", "EXCL", [])
        main_box.add(exclusions_box)

        # All-day event option
        checkmark_box = toga.Box(style=Pack(direction=ROW, padding=10))
        self.checkmark = toga.Switch("Convert events to all-day events", value=False)
        checkmark_box.add(self.checkmark)
        main_box.add(checkmark_box)

        # Pre-populate entries based on configuration
        if 'ics1_path' in self.config:
            self.ics1_entry.value = os.path.basename(self.config['ics1_path'])
            self.file_paths['ics1'] = Path(self.config['ics1_path'])
        if 'ics2_path' in self.config:
            self.ics2_entry.value = os.path.basename(self.config['ics2_path'])
            self.file_paths['ics2'] = Path(self.config['ics2_path'])
        if 'exclusions_path' in self.config:
            self.exclusions_entry.value = os.path.basename(self.config['exclusions_path'])
            self.file_paths['exclusions'] = Path(self.config['exclusions_path'])
        if 'all_day' in self.config:
            self.checkmark.value = self.config['all_day']

        # Bottom button box
        save_button = toga.Button('Save Configuration', on_press=self.save_configuration, style=Pack(padding=10))
        self.analyze_button = toga.Button('Analyze', on_press=self.analyze_button_action, enabled=False, style=Pack(padding_top=10, padding_bottom=10, padding_left=120, padding_right=10))
        self.merge_button = toga.Button('Merge', on_press=self.merge_button_action, enabled=False, style=Pack(padding=10))
        button_box = toga.Box(style=Pack(direction=COLUMN, alignment=CENTER, flex=1), children=[
            inner := toga.Box(style=Pack(direction=ROW), children=[
                save_button,
                self.analyze_button,
                self.merge_button
            ])
        ])

        main_box.add(button_box)

        # Add check for updates command
        if self.platform == 'Windows':
            check_for_updates_command = toga.Command(lambda w: self.update_helper(False), 'Check for updates...', group=Group.FILE, section=1)
        else:
            check_for_updates_command = toga.Command(lambda w: self.update_helper(False), 'Check for updates...', group=Group.APP)
        self.commands.add(check_for_updates_command)

        # Activate the main window
        self.main_window.content = main_box
        self.main_window.show()

        # Check for updates
        self.update_helper(True)

        # Initial validation of file entries
        self.validate_files()

    def update_helper(self, type):
        async def task(widget):
            await update_checker(self, type)
        update_thread = Thread(target=toga.App.app.add_background_task(task))
        update_thread.start()

    def create_file_selection_row(self, description_key, placeholder_text, entry_key, entry_name, file_types):
        button_width = 60
        description_button = toga.Button('?', on_press=lambda widget: self.show_description(entry_name, description_key), style=Pack(padding=5))
        label = toga.Box(style=Pack(padding=5), children=[toga.Label(gui_descriptions[entry_key], style=Pack(padding=5, width=40))])
        entry = toga.TextInput(placeholder=placeholder_text,style=Pack(padding=5, flex=1), readonly=True)
        clear_button = toga.Button('Clear', on_press=lambda widget: self.clear_entry(entry_key), style=Pack(padding=5, width=button_width))
        browse_button = toga.Button('Browse', on_press=lambda widget: asyncio.create_task(self.select_file(entry_key, file_types)), style=Pack(padding=5, width=button_width))
        if entry_key == 'exclusions':
            view_button = toga.Button('Edit', on_press=lambda widget: asyncio.create_task(self.view_edit_exclusions_file(entry_key)), enabled=True, style=Pack(padding=5, width=button_width))
        else:
            view_button = toga.Button('View', on_press=lambda widget: asyncio.create_task(self.view_file(entry_key)), enabled=False, style=Pack(padding=5, width=button_width))

        if self.platform == 'Windows':
            row_box = toga.Box(style=Pack(direction=ROW, alignment=TOP, padding=5))
        else:
            row_box = toga.Box(style=Pack(direction=ROW, alignment=CENTER, padding=5))
        row_box.add(description_button)
        row_box.add(label)
        if self.platform == 'Windows':
            row_box.add(toga.Box(style=Pack(direction=COLUMN, flex=1), children=[
                entry, 
                toga.Label(placeholder_text, style=Pack(padding_left=5, padding_top=2, padding_bottom=0))
            ]))
        else:
            row_box.add(entry)
        row_box.add(clear_button)
        row_box.add(browse_button)
        row_box.add(view_button)
        return row_box, entry, clear_button, browse_button, view_button

    def window_position(self, window_width, window_height):
        screen_width, screen_height = self.screens[0].size
        position_x = (screen_width - window_width) // 2
        position_y = (screen_height - window_height) // 2
        return position_x, position_y

    def show_description(self, file, key):
        self.main_window.info_dialog(file, gui_descriptions[key])

    async def select_file(self, key, file_types):
        file_path = await self.main_window.open_file_dialog('Select File', file_types=file_types)
        logging.debug(f"Selected file: {file_path}")
        if file_path:
            file_name = os.path.basename(file_path)
            self.file_paths[key] = Path(file_path)  # Store as Path object for later use
            if key == 'ics1':
                self.ics1_entry.value = file_name
            elif key == 'ics2':
                self.ics2_entry.value = file_name
            elif key == 'exclusions':
                self.exclusions_entry.value = file_name
        self.validate_files()

    def clear_entry(self, key):
        if key == 'ics1':
            self.ics1_entry.value = ''
        elif key == 'ics2':
            self.ics2_entry.value = ''
        elif key == 'exclusions':
            self.exclusions_entry.value = ''
        self.file_paths.pop(key, None)
        self.validate_files()

    def validate_files(self):
        ics1_valid = 'ics1' in self.file_paths and self.file_paths['ics1'].is_file()
        ics2_valid = 'ics2' in self.file_paths and self.file_paths['ics2'].is_file()
        exclusions_valid = 'exclusions' in self.file_paths and self.file_paths['exclusions'].is_file()
        logging.debug(f"ICS1 Valid: {ics1_valid}")
        logging.debug(f"ICS2 Valid: {ics2_valid}")
        logging.debug(f"EXCL Valid: {exclusions_valid}")
        if not self.analyze_open:
            self.analyze_button.enabled = ics2_valid
        if not self.merge_open:
            self.merge_button.enabled = ics2_valid
        self.ics1_view_button.enabled = ics1_valid
        self.ics2_view_button.enabled = ics2_valid
        if exclusions_valid:
            self.exclusions_edit_button.text = "Edit"
            self.exclusions_edit_button.on_press=lambda widget: asyncio.create_task(self.view_edit_exclusions_file("exclusions"))
        else:
            self.exclusions_edit_button.text = "New"
            self.exclusions_edit_button.on_press=lambda widget: asyncio.create_task(self.new_exclusions_file())

    async def new_exclusions_file(self):
        """
        Opens a save file dialog to create a new exclusions file.
        
        Returns:
            None
        """
        exclusions_file_path = await self.main_window.save_file_dialog("New Exclusions File", "exclusions.txt", file_types=["txt"])
        logging.debug(f"exclusions_file_path: {exclusions_file_path}")
        if exclusions_file_path:
            self.file_paths['exclusions'] = exclusions_file_path
            file_name = os.path.basename(exclusions_file_path)
            self.exclusions_entry.value = file_name
            create_file(self, exclusions_file_path)
            self.exclusions_edit_button.text = "Edit"
            self.exclusions_edit_button.on_press=lambda widget: asyncio.create_task(self.view_edit_exclusions_file("exclusions"))
            await self.view_edit_exclusions_file("exclusions")

    def get_paths(self):
        ics1_path = str(self.file_paths.get('ics1', ''))
        logging.debug(f"ics1_path: {ics1_path}")
        if ics1_path == ".":
            ics1_path = ""
        ics2_path = str(self.file_paths.get('ics2', ''))
        logging.debug(f"ics2_path: {ics2_path}")
        if ics2_path == ".":
            ics2_path = ""
        exclusions_path = str(self.file_paths.get('exclusions', ''))
        logging.debug(f"exclusions_path: {exclusions_path}")
        if exclusions_path == ".":
            exclusions_path = ""
        return ics1_path, ics2_path, exclusions_path

    def check_paths(self, ics1_path, ics2_path, exclusions_path):
        # Sanity checks, though they should not really be necessary.
        if not ics2_path:
            self.main_window.error_dialog("Error", "ICS2 field must be filled out.")
            return False
        if ics1_path and not os.path.exists(ics1_path):
            self.main_window.error_dialog("Error", f"File not found: {ics1_path}")
            return False
        if not os.path.exists(ics2_path):
            self.main_window.error_dialog("Error", f"File not found: {ics2_path}")
            return False
        if exclusions_path and not os.path.exists(exclusions_path):
            self.main_window.error_dialog("Error", f"File not found: {exclusions_path}")
            return False
        return True

    def analyze_button_action(self, widget):
        """
        Extracts paths for selected files, and initiates an asynchronous analysis.

        Args:
            widget: The widget that triggered the action.

        Returns:
            None
        """
        ics1_path, ics2_path, exclusions_path = self.get_paths()
        logging.debug(f"\n\tics1_path:\t{ics1_path}\n\tics2_path:\t{ics2_path}\n\texclusions_path:\t{exclusions_path}")
        sanity_check = self.check_paths(ics1_path, ics2_path, exclusions_path)
        if sanity_check:
            asyncio.create_task(analyze(self, ics1_path, ics2_path, exclusions_path))

    def merge_button_action(self, widget):
        """
        Extracts paths for selected files, and initiates a merge action.

        Args:
            widget: The widget that triggered the merge action.

        Returns:
            None
        """
        ics1_path, ics2_path, exclusions_path = self.get_paths()
        all_day = self.checkmark.value
        logging.debug(f"\n\tics1_path:\t{ics1_path}\n\tics2_path:\t{ics2_path}\n\texclusions_path:\t{exclusions_path}\n\tall_day:\t{all_day}")
        sanity_check = self.check_paths(ics1_path, ics2_path, exclusions_path)
        if sanity_check:
            asyncio.create_task(run_merge(self, ics1_path, ics2_path, exclusions_path, all_day))

    async def save_configuration(self, widget):
            """
            Creates a configuration dictionary, and intiates a configureatino file save.

            Args:
                widget: The widget triggering the save action.

            Returns:
                None
            """
            ics1_path, ics2_path, exclusions_path = self.get_paths()
            all_day = self.checkmark.value

            config = {
                'ics1_path': ics1_path,
                'ics2_path': ics2_path,
                'exclusions_path': exclusions_path,
                'all_day' : all_day
            }
            logging.debug(f"config: {config.items()}")
            save_config(self, config)

    async def view_file(self, key):
        file_path = self.file_paths.get(key)
        logging.debug(f"file_path: {file_path}")
        if not file_path or not file_path.is_file():
            self.main_window.error_dialog('Warning', 'No file selected or file does not exist.')
            return

        try:
            with file_path.open('r') as file:
                content = file.read()
            await show_content_in_window(self, content, str(file_path), key)
        except Exception as e:
            self.main_window.error_dialog('Error', f'Failed to open file: {e}')

    async def view_edit_exclusions_file(self, key):
        file_path = self.file_paths.get(key)
        logging.debug(f"file_path: {file_path}")
        if not file_path or not file_path.is_file():
            self.main_window.error_dialog('Warning', 'No file selected or file does not exist.')
            return

        try:
            with file_path.open('r') as file:
                content = file.read()
                await edit_exclusions_window(self, content, str(file_path))
        except Exception as e:
            self.main_window.error_dialog('Error', f'Failed to open exclusions file: {e}')
            return

def main():
    return ICSMerger(f"{gui_descriptions["root_title"]} ({__version__})")

if __name__ == '__main__':
    main().main_loop()
