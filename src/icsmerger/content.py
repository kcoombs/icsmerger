
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

async def show_content_in_window(self, content, title):
    def close_handler(widget):
        content_window.close()
        self.main_window.show()
    
    window_width, window_height = 800, 600
    position_x, position_y = self.window_position(window_width, window_height)
    content_window = toga.Window(title=title, size=(window_width, window_height), position=(position_x, position_y))
    content_box = toga.Box(style=Pack(direction=COLUMN, padding=10, flex=1))

    # Text Area
    text_area = toga.MultilineTextInput(value=content, readonly=True, style=Pack(flex=1))
    scroll_container = toga.ScrollContainer(content=text_area, style=Pack(flex=1))
    content_box.add(scroll_container)
    
    # Close Button
    button_box = toga.Box(style=Pack(direction=ROW))
    close_button = toga.Button('Close', on_press=close_handler, style=Pack(padding=10))
    button_box.add(close_button)
    content_box.add(button_box)

    content_window.content = content_box
    content_window.on_close = close_handler
    content_window.show()
    self.main_window.hide()

async def edit_exclusions_window(self, content, file_path):
    changed = False

    def change_handler(widget):
        nonlocal changed 
        changed = True

    async def close_handler(widget):
        if changed:
            result = await exclusions_window.question_dialog("Save Exclusions File?", "Contents changed. Save changes to EXCL before closing?")
            if result:
                await save_exclusions(widget)
        exclusions_window.close()
        self.main_window.show()

    async def on_close_handler(widget):
        if changed:
            result = await exclusions_window.question_dialog("Save File?", "Contents changed. Save Changes to EXCL before closing?")
            if result:
                await save_exclusions(widget)
        exclusions_window.close()
        self.main_window.show()

    window_width, window_height = 800, 600
    position_x, position_y = self.window_position(window_width, window_height)
    exclusions_window = toga.Window(title="Exclusions Editor", size=(window_width, window_height), position=(position_x, position_y))
    text_box = toga.Box(style=Pack(direction=COLUMN, padding=10, flex=1))
    text_input = toga.MultilineTextInput(value=content, style=Pack(flex=1), on_change=change_handler)
    
    async def save_exclusions(widget):
        nonlocal changed
        try:
            with open(file_path, 'w') as file:
                file.write(text_input.value.strip())
            changed = False
            await exclusions_window.info_dialog("Success", "Exclusions file saved successfully.")
        except Exception as e:
            await exclusions_window.error_dialog("Error", f"Failed to save exclusions file: {e}")

    text_box.add(text_input)
    button_box = toga.Box(style=Pack(direction=ROW))
    save_button = toga.Button('Save', on_press=save_exclusions, style=Pack(padding=10))
    close_button = toga.Button('Close', on_press=close_handler, style=Pack(padding=10))
    button_box.add(save_button)
    button_box.add(close_button)
    text_box.add(button_box)

    exclusions_window.content = text_box
    exclusions_window.on_close = on_close_handler
    exclusions_window.show()
    self.main_window.hide()