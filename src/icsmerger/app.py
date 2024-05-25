import os
import asyncio
import toga
import toga.platform
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER, BOLD
from pathlib import Path
from .descriptions import gui_descriptions
from .merge import run_merge
from .load import load_files
from .config import save_config, load_config, get_appdir

class ICSMerger(toga.App):
    def startup(self):
        # Initialize main window
        window_width, window_height = 750, 225
        position_x, position_y = self.window_position(window_width, window_height)
        self.main_window = toga.MainWindow("iCal Merger", resizable=False, size=(window_width, window_height), position = (position_x, position_y))

        # Load configuration
        self.config_path = get_appdir()
        self.config = load_config(self.main_window, self.config_path)

        # Dictionary to store full file paths
        self.file_paths = {}

        # Main layout box
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=10, flex=1))

        def create_file_selection_row(description_key, entry_key, entry_name):
            button_width = 60
            description_button = toga.Button(
                '?', 
                on_press=lambda widget: self.show_description(entry_name, description_key), 
                style=Pack(padding=5)
            )
            label = toga.Label(
                gui_descriptions[entry_key], 
                style=Pack(padding=5, width=205)
            )
            entry = toga.TextInput(
                style=Pack(flex=1, padding=5)
            )
            clear_button = toga.Button(
                'Clear', 
                on_press=lambda widget: self.clear_entry(entry_key), 
                style=Pack(padding=5, width=button_width)
            )
            browse_button = toga.Button(
                'Browse', 
                on_press=lambda widget: asyncio.create_task(self.select_file(entry_key)), 
                style=Pack(padding=5, width=button_width)
            )
            if entry_key == 'exclusions':
                view_button = toga.Button(
                    'Edit', 
                    on_press=lambda widget: asyncio.create_task(self.view_edit_exclusions_file(entry_key)), 
                    enabled=False, 
                    style=Pack(padding=5, width=button_width)
                )
            else:
                view_button = toga.Button(
                    'View', 
                    on_press=lambda widget: asyncio.create_task(self.view_file(entry_key)), 
                    enabled=False, 
                    style=Pack(padding=5, width=button_width)
                )

            row_box = toga.Box(style=Pack(direction=ROW, padding=5))
            row_box.add(description_button)
            row_box.add(label)
            row_box.add(entry)
            row_box.add(clear_button)
            row_box.add(browse_button)
            row_box.add(view_button)

            return row_box, entry, view_button

        # ICS1 file selection
        ics1_box, self.ics1_entry, self.ics1_view_button = create_file_selection_row("ics1_description", "ics1", "ICS1")
        main_box.add(ics1_box)

        # ICS2 file selection
        ics2_box, self.ics2_entry, self.ics2_view_button = create_file_selection_row("ics2_description", "ics2", "ICS2")
        main_box.add(ics2_box)

        # Exclusions file selection
        exclusions_box, self.exclusions_entry, self.exclusions_edit_button = create_file_selection_row("exclusions_description", "exclusions", "EXCL")
        main_box.add(exclusions_box)

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

        # Create the bottom button box
        button_box = toga.Box(style=Pack(
            direction=ROW, 
            padding=10, 
            alignment=CENTER,
        ))       
        
        # Add buttons to the button box
        self.analyze_button = toga.Button(
            'Analyze', 
            on_press=self.analyze_button_action, 
            enabled=False, 
            style=Pack(padding=10)
        )
        self.merge_button = toga.Button(
            'Merge', 
            on_press=self.merge_button_action, 
            enabled=False, 
            style=Pack(padding=10)
        )
        save_button = toga.Button(
            'Save Configuration', 
            on_press=self.save_configuration, 
            style=Pack(padding=10)
        )
        button_box.add(self.analyze_button)
        button_box.add(self.merge_button)
        button_box.add(save_button)

        # Add button box to the main box
        main_box.add(button_box)

        self.main_window.content = main_box
        # self.main_window.size = (750, 225)
        self.main_window.show()

        # Validate file entries
        self.validate_files()

    def window_position(self, window_width, window_height):
        screen_width, screen_height = self.screens[0].size
        position_x = (screen_width - window_width) // 2
        position_y = (screen_height - window_height) // 2
        return position_x, position_y

    def show_description(self, file, key):
        self.main_window.info_dialog(file, gui_descriptions[key])

    async def select_file(self, key):
        file_path = await self.main_window.open_file_dialog('Select File')
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
        self.analyze_button.enabled = ics2_valid
        self.merge_button.enabled = ics2_valid
        self.ics1_view_button.enabled = ics1_valid
        self.ics2_view_button.enabled = ics2_valid
        self.exclusions_edit_button.enabled = exclusions_valid

    def analyze_button_action(self, widget):
        ics1_path = str(self.file_paths.get('ics1', ''))
        ics2_path = str(self.file_paths.get('ics2', ''))
        exclusions_path = str(self.file_paths.get('exclusions', ''))

        if ics1_path or ics2_path or exclusions_path:
            try:
                ics_text = toga.MultilineTextInput(readonly=True, style=Pack(flex=1))
                excl_text = toga.MultilineTextInput(readonly=True, style=Pack(flex=1))
                
                window_width, window_height = 800, 600
                position_x, position_y = self.window_position(window_width, window_height)
                analysis_window = toga.Window(title="ICS Analysis", size=(window_width, window_height), position=(position_x, position_y))
                
                main_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

                row1 = toga.Box(style=Pack(direction=ROW, padding=10))
                row2 = toga.Box(style=Pack(direction=ROW, padding=10, flex=1))
                row3 = toga.Box(style=Pack(direction=ROW, padding=10))

                # Labels
                row1.add(toga.Label("ICS Information", style=Pack(font_weight=BOLD, flex=1)))
                row1.add(toga.Label("Exclusions Information", style=Pack(font_weight=BOLD, flex=1)))

                # Content
                row2.add(ics_text)
                row2.add(excl_text)                 

                # Close button
                row3.add(toga.Button('Close', on_press=lambda w: analysis_window.close(), style=Pack(padding=5)))

                main_box.add(row1)
                main_box.add(row2)
                main_box.add(row3)

                analysis_window.content = main_box
                analysis_window.show()

                load_files(self.main_window, ics1_path, ics2_path, exclusions_path, ics_text, excl_text)
            
            except Exception as e:
                self.main_window.error_dialog('Error', f'Failed to analyze files:\n{e}')

    def merge_button_action(self, widget):
        ics1_path = str(self.file_paths.get('ics1', ''))
        ics2_path = str(self.file_paths.get('ics2', ''))
        exclusions_path = str(self.file_paths.get('exclusions', ''))

        asyncio.create_task(run_merge(self, self.main_window, ics1_path, ics2_path, exclusions_path))

    def save_configuration(self, widget):
        # Retrieve the paths from the file_paths dictionary, if they exist
        ics1_path = str(self.file_paths.get('ics1', ''))
        ics2_path = str(self.file_paths.get('ics2', ''))
        exclusions_path = str(self.file_paths.get('exclusions', ''))

        config = {
            'ics1_path': ics1_path,
            'ics2_path': ics2_path,
            'exclusions_path': exclusions_path
        }

        config_path = get_appdir()

        try:
            save_config(self.main_window, config, config_path)
            self.main_window.info_dialog('Save Configuration', 'Configuration saved successfully.')
        except Exception as e:
            self.main_window.error_dialog('Error', f'Failed to save configuration:\n{e}')

    async def view_file(self, key):
        file_path = self.file_paths.get(key)
        if not file_path or not file_path.is_file():
            self.main_window.error_dialog('Warning', 'No file selected or file does not exist.')
            return

        try:
            with file_path.open('r') as file:
                content = file.read()
                await self.show_content_in_window(content, str(file_path))
        except Exception as e:
            self.main_window.error_dialog('Error', f'Failed to open file:\n{e}')

    async def show_content_in_window(self, content, title):
        window_width, window_height = 800, 600
        position_x, position_y = self.window_position(window_width, window_height)
        content_window = toga.Window(title=title, size=(window_width, window_height), position=(position_x, position_y))
        content_box = toga.Box(style=Pack(direction=COLUMN, padding=10, flex=1))

        # Text Area
        text_area = toga.MultilineTextInput(value=content, readonly=True, style=Pack(flex=1))
        scroll_container = toga.ScrollContainer(content=text_area, style=Pack(flex=1))
        content_box.add(scroll_container)
        
        # Close Button
        button_box = toga.Box(style=Pack(direction=ROW, padding=10))
        close_button = toga.Button('Close', on_press=lambda w: content_window.close(), style=Pack(padding=5))
        button_box.add(close_button)
        content_box.add(button_box)

        content_window.content = content_box
        content_window.show()

    async def view_edit_exclusions_file(self, key):
        file_path = self.file_paths.get(key)
        if not file_path or not file_path.is_file():
            self.main_window.error_dialog('Warning', 'No file selected or file does not exist.')
            return

        try:
            with file_path.open('r') as file:
                content = file.read()
        except Exception as e:
            self.main_window.error_dialog('Error', f'Failed to open exclusions file:\n{e}')
            return

        await self.edit_exclusions_window(content, str(file_path))

    async def edit_exclusions_window(self, content, file_path):
        window_width, window_height = 800, 600
        position_x, position_y = self.window_position(window_width, window_height)
        exclusions_window = toga.Window(title="Exclusions Editor", size=(window_width, window_height), position=(position_x, position_y))
        text_box = toga.Box(style=Pack(direction=COLUMN, padding=10, flex=1))
        text_input = toga.MultilineTextInput(value=content, style=Pack(flex=1))

        def save_exclusions(widget):
            try:
                with open(file_path, 'w') as file:
                    file.write(text_input.value.strip())
                self.main_window.info_dialog("Success", "Exclusions file saved successfully.")
                exclusions_window.close()
            except Exception as e:
                self.main_window.error_dialog("Error", f"Failed to save exclusions file:\n{e}")

        text_box.add(text_input)
        button_box = toga.Box(style=Pack(direction=ROW, padding=10))
        save_button = toga.Button('Save', on_press=save_exclusions, style=Pack(padding=5))
        cancel_button = toga.Button('Cancel', on_press=lambda w: exclusions_window.close(), style=Pack(padding=5))
        button_box.add(save_button)
        button_box.add(cancel_button)
        text_box.add(button_box)

        exclusions_window.content = text_box
        exclusions_window.show()

def main():
    return ICSMerger("iCal Merger")

if __name__ == '__main__':
    main().main_loop()
