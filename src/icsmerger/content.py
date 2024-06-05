
import logging
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

async def show_content_in_window(self, content, title, key):
    def close_handler(widget):
        content_window.close()
        if key == 'ics1': 
            self.ics1_clear_button.enabled = True
            self.ics1_browse_button.enabled = True
            self.ics1_view_button.enabled = True
        elif key == 'ics2': 
            self.ics2_clear_button.enabled = True
            self.ics2_browse_button.enabled = True
            self.ics2_view_button.enabled = True
    
    window_width, window_height = 800, 600
    position_x, position_y = self.window_position(window_width, window_height)
    content_window = toga.Window(title=title, size=(window_width, window_height), position=(position_x, position_y))
    
    content_box = toga.Box(style=Pack(direction=COLUMN, padding=10, flex=1), children=[
        toga.ScrollContainer(
            content = toga.MultilineTextInput(value=content, readonly=True, style=Pack(flex=1), placeholder="Empty File."), 
            style=Pack(flex=1)),
        inner := toga.Box(style=Pack(direction=ROW, padding=10), children=[
            toga.Label("", style=Pack(flex=1)),
            toga.Button('Close', on_press=close_handler, style=Pack(padding=10)),
            toga.Label("", style=Pack(flex=1))
        ])
    ])

    content_window.content = content_box
    content_window.on_close = close_handler
    content_window.show()
    if key == 'ics1': 
        self.ics1_clear_button.enabled = False 
        self.ics1_browse_button.enabled = False 
        self.ics1_view_button.enabled = False
    elif key == 'ics2': 
        self.ics2_clear_button.enabled = False 
        self.ics2_browse_button.enabled = False 
        self.ics2_view_button.enabled = False

async def edit_exclusions_window(self, content, file_path):
    changed = False
    
    def change_handler(widget):
        nonlocal changed
        if changed == False:
            title = self.current_window.title
            self.current_window.title = f"{title} (Changed)"
            changed = True

    async def close_handler(widget):
        if changed:
            result = await exclusions_window.question_dialog("Save Exclusions File?", "Contents changed. Save changes to EXCL before closing?")
            if result:
                await save_exclusions(widget)
        exclusions_window.close()
        self.exclusions_clear_button.enabled = True
        self.exclusions_browse_button.enabled = True
        self.exclusions_edit_button.enabled = True
        self.analyze_button.enabled = True
        self.merge_button.enabled = True

    async def on_close_handler(widget):
        if changed:
            result = await exclusions_window.question_dialog("Save File?", "Contents changed. Save Changes to EXCL before closing?")
            if result:
                await save_exclusions(widget)
        exclusions_window.close()
        self.exclusions_clear_button.enabled = True
        self.exclusions_browse_button.enabled = True
        self.exclusions_edit_button.enabled = True
        self.analyze_button.enabled = True
        self.merge_button.enabled = True

    window_width, window_height = 800, 600
    position_x, position_y = self.window_position(window_width, window_height)
    exclusions_window = toga.Window(title="Exclusions Editor", size=(window_width, window_height), position=(position_x, position_y))

    text_input = toga.MultilineTextInput(value=content, style=Pack(flex=1), on_change=change_handler, placeholder="Enter one string per line. When matched to an event's Summary, these strings will cause that event to be excluded from the output.")

    async def save_exclusions(widget):
        nonlocal changed
        try:
            with open(file_path, 'w') as file:
                file.write(text_input.value.strip())
            changed = False
            await exclusions_window.info_dialog("Success", "Exclusions file saved successfully.")
        except Exception as e:
            await exclusions_window.error_dialog("Error", f"Failed to save exclusions file: {e}")

    edit_box = toga.Box(style=Pack(direction=COLUMN, padding=10, flex=1), children=[
        toga.ScrollContainer(content=text_input, style=Pack(flex=1)),
        inner := toga.Box(style=Pack(direction=ROW, padding=10), children=[
            toga.Label("", style=Pack(flex=1)),
            toga.Button('Save', on_press=save_exclusions, style=Pack(padding=(0,5))),
            toga.Button('Close', on_press=close_handler, style=Pack(padding=(0,5))),
            toga.Label("", style=Pack(flex=1))
        ])
    ])

    exclusions_window.content = edit_box
    exclusions_window.on_close = on_close_handler
    exclusions_window.show()
    self.exclusions_clear_button.enabled = False
    self.exclusions_browse_button.enabled = False
    self.exclusions_edit_button.enabled = False
    self.analyze_button.enabled = False
    self.merge_button.enabled = False