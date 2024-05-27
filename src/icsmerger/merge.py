import os
from icalendar import Calendar
from .ical import load_ics, get_event_set, create_event
from .exclusions import load_exclusions, filter_exclusions, print_exclusions
from .descriptions import merge_descriptions
from .fileio import get_outdir, open_output_file
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER, BOLD

async def run_merge(self, ics1_path, ics2_path, exclusions_path, all_day):
    
    async def save_file_dialog(title, suggested):
        file_path = await merge_window.save_file_dialog(title, suggested_filename=suggested)
        return file_path

    async def save_suggestions(widget):
        suggestions_file_path = await save_file_dialog("Save Suggestions", "suggestions.txt")
        if suggestions_file_path:
            with open(suggestions_file_path, 'w') as f:
                f.write(remove_text.value)
            merge_window.info_dialog("Save Suggestions", "Suggestions saved successfully.")

    async def save_merge_results(widget):
        merge_results_file_path = await save_file_dialog("Save Merge Results", "merge.ics")
        if merge_results_file_path:
            with open(merge_results_file_path, 'w') as f:
                f.write(output_cal.to_ical().decode("utf-8").replace('\r\n', '\n').strip())
            merge_window.info_dialog("Save Merge Results", "Merge results saved successfully.")

    async def open_merge_results(widget):
        save_path = get_outdir()
        try:
            if save_path:
                with open(save_path, 'w') as f:
                    f.write(output_cal.to_ical().decode("utf-8").replace('\r\n', '\n').strip())
            open_output_file(merge_window, save_path)
        except Exception as e:
            merge_window.info_dialog("Error", f"An unknown error occurred during opening: {e}")

    def close_handler(widget):
        merge_window.close()
        self.main_window.show()

    # Create the merge window
    window_width, window_height = 1400, 800
    screen_width, screen_height = self.screens[0].size
    position_x = (screen_width - window_width) // 2
    position_y = (screen_height - window_height) // 2
    merge_window = toga.Window(title="Merge ICS Files", size=(window_width, window_height), position=(position_x, position_y))
    merge_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

    grid_box = toga.Box(style=Pack(direction=COLUMN, padding=0, flex=1))

    row1 = toga.Box(style=Pack(direction=ROW, padding=10))
    row2 = toga.Box(style=Pack(direction=ROW, padding=10, flex=1))
    row3 = toga.Box(style=Pack(direction=ROW, padding=10))

    excl_text = toga.MultilineTextInput(readonly=True, style=Pack(flex=1))
    remove_text = toga.MultilineTextInput(readonly=True, style=Pack(flex=1))
    merge_text = toga.MultilineTextInput(readonly=True, style=Pack(flex=1))

    row1.add(toga.Label("Exclusions", style=Pack(font_weight=BOLD, flex=1)))
    row1.add(toga.Label("Suggested Removals", style=Pack(font_weight=BOLD, flex=1)))
    row1.add(toga.Label("New Events", style=Pack(font_weight=BOLD, flex=1)))

    row2.add(excl_text)
    row2.add(remove_text)
    row2.add(merge_text)

    close_button_box = toga.Box(style=Pack(direction=ROW, alignment=CENTER, flex=1))
    save_suggestions_button_box = toga.Box(style=Pack(direction=ROW, alignment=CENTER, flex=1))
    save_merge_button_box = toga.Box(style=Pack(direction=ROW, alignment=CENTER, flex=1))

    close_button = toga.Button('Close', on_press=close_handler, style=Pack())
    save_suggestions_button = toga.Button("Save Suggested Removals", on_press=save_suggestions, style=Pack())
    save_merge_button = toga.Button("Save Events to .ics", on_press=save_merge_results, style=Pack(padding_top=0, padding_right=5,padding_bottom=0, padding_left=0))
    open_merge_button = toga.Button("Open Events in Calendar", on_press=open_merge_results, style=Pack(padding=(0,5)))

    close_button_box.add(close_button)
    save_suggestions_button_box.add(save_suggestions_button)
    save_merge_button_box.add(save_merge_button)
    save_merge_button_box.add(open_merge_button)

    row3.add(close_button_box)
    row3.add(save_suggestions_button_box)
    row3.add(save_merge_button_box)

    grid_box.add(row1)
    grid_box.add(row2)
    grid_box.add(row3)

    merge_box.add(grid_box)

    merge_window.content = merge_box
    merge_window.on_close = close_handler
    merge_window.show()
    self.main_window.hide()

    # Run the merge
    output_cal = merge(merge_window, ics1_path, ics2_path, exclusions_path, excl_text, remove_text, merge_text, all_day)

# Main function to merge calendars
def merge(merge_window, ics1_path, ics2_path, exclusions_path, excl_text, remove_text, merge_text, all_day):
    try:
        # Load the calendars from the input files
        cal1 = load_ics(merge_window, ics1_path) if os.path.exists(ics1_path) else Calendar()
        cal2 = load_ics(merge_window, ics2_path) if os.path.exists(ics2_path) else None
        if cal1 is None and cal2 is None:   # Sanity check
            merge_text.value += f"{merge_descriptions["no_reach"]}"
            return

        # Load and print the exclusions
        if not exclusions_path:
            excl_text.value += "No EXCL file provided.\n\n"
            exclusions = []
        else:
            exclusions = load_exclusions(merge_window, exclusions_path)
            if exclusions:
                excl_text.value += f"Excluding any new event(s) matching:\n\n"
                for excl in exclusions:
                    excl_text.value += f"  - '{excl}'\n"
                excl_text.value += "\n"
            else:
                excl_text.value += "EXCL file was provided, but it was empty.\n\n"

        # Create a set of events from each calendar
        events1 = get_event_set(cal1) if cal1 else set()
        events2 = get_event_set(cal2) if cal2 else set()

        # Generate unique events for each calendar
        unique_events_ics2 = events2 - events1  # These are the initial new events to be added to the output ical
        unique_events_ics1 = events1 - events2  # These are used to report possible events to manually remove

        # Remove exclusions from the unique_events_ics2
        filtered_events_ics2, excluded_events = filter_exclusions(unique_events_ics2, exclusions)
        filtered_events_ics1, excluded_events = filter_exclusions(unique_events_ics1, exclusions)
        print_exclusions(excluded_events,excl_text)

        # Create a new calendar from the filtered_events
        output_cal = Calendar()
        for event in filtered_events_ics2:
            output_cal.add_component(create_event(event, all_day))
            
        # If there was an ICS1, report any event that exists in ICS1 but not ICS2 as possible removals, in sorted order
        if os.path.exists(ics1_path):
            if filtered_events_ics1:
                remove_text.value += f"Consider removing the following events from your calendar.\n\nThey existed in ICS1 but are not in ICS2 and thus may no longer be relevant.\n\nThese event(s) are:\n\n"
                for event in sorted(filtered_events_ics1, key=lambda x: x[1]):
                    remove_text.value += f"  - {event[0]} on {event[1].date()}\n"
            else:
                remove_text.value += "No suggested removals from the current calendar were found in ICS1."
        else:
            remove_text.value += "First run detected. No removals from the current calendar are suggested."

        # Report overall result
        if filtered_events_ics2:
            merge_text.value += f"There are {len(filtered_events_ics2)} new event(s) in ICS2 that do not exist in ICS1.\n\nThese event(s) are:\n\n"
            for event in sorted(filtered_events_ics2, key=lambda x: x[1]):
                merge_text.value += f"  - {event[0]} on {event[1].date()}\n"
        else:
            merge_text.value += "No new events were found in ICS2.\n"

        return output_cal

    except Exception as e:
        merge_text.value += f"An unknown error occurred during the merge process: {e}\n"
