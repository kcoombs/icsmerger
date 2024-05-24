import os
from icalendar import Calendar
from .ical import load_ics, get_event_set, create_all_day_event
from .exclusions import load_exclusions, filter_exclusions
from .descriptions import merge_descriptions
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER

# Main function to merge calendars
def merge(ics1_path, ics2_path, exclusions_path, excl_text, remove_text, merge_text):
    try:
        # Load the calendars from the input files
        cal1 = load_ics(ics1_path) if os.path.exists(ics1_path) else Calendar()
        cal2 = load_ics(ics2_path) if os.path.exists(ics2_path) else None

        # Sanity check
        if cal1 is None and cal2 is None:
            merge_text.value += merge_descriptions["no_reach"]
            return

        # Load and the exclusions
        if not exclusions_path:
            excl_text.value += "No EXCL file provided.\n\n"
            exclusions = []
        else:
            exclusions = load_exclusions(exclusions_path)
            if exclusions:
                excl_text.value += f"Excluding any event(s) matching:\n\n"
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
        filtered_events = filter_exclusions(unique_events_ics2, exclusions, excl_text)

        # Create a new calendar of all-day events from the filtered_events
        output_cal = Calendar()
        for event in filtered_events:
            output_cal.add_component(create_all_day_event(event))

        # If there was an ics1, report any event that exists in cal1 but not cal2 as possible removals, in sorted order
        if os.path.exists(ics1_path):
            if unique_events_ics1:
                remove_text.value += f"Consider removing the following events from your calendar.\n\nThey existed in ICS1 but are not in ICS2 and thus may no longer be relevant:\n\n"
                for event in sorted(unique_events_ics1, key=lambda x: x[1]):
                    remove_text.value += f"  - {event[0]} on {event[1].date()}\n"
            else:
                remove_text.value += "No suggested removals from the current calendar were found in ICS1."
        else:
            remove_text.value += "First run detected. No removals from the current calendar are suggested."

        # Report overall result
        if filtered_events:
            merge_text.value += f"There are {len(filtered_events)} new event(s) in ICS2 that do not exist in ICS1. These event(s) are:\n\n"
            # Print out events in sorted order
            for event in sorted(filtered_events, key=lambda x: x[1]):
                merge_text.value += f"  - {event[0]} on {event[1].date()}\n"
        else:
            merge_text.value += "No new events were found in ICS2.\n"

        return output_cal

    except Exception as e:
        merge_text.value += f"An unknown error occurred during the merge process: {e}\n"

# Run merge process
async def run_merge(main_window, ics1_path, ics2_path, exclusions_path):
    if not ics2_path:
        main_window.error_dialog("Error", "ICS2 field must be filled out.")
        return

    if ics1_path and not os.path.exists(ics1_path):
        main_window.error_dialog("Error", f"File not found: {ics1_path}")
        return

    if not os.path.exists(ics2_path):
        main_window.error_dialog("Error", f"File not found: {ics2_path}")
        return

    if exclusions_path and not os.path.exists(exclusions_path):
        main_window.error_dialog("Error", f"File not found: {exclusions_path}")
        return

    async def save_suggestions(widget):
        suggestions_file_path = await save_file_dialog("Save Suggestions", "suggestions.txt")
        if suggestions_file_path:
            with open(suggestions_file_path, 'w') as f:
                f.write(remove_text.value)
            main_window.info_dialog("Save Suggestions", "Suggestions saved successfully.")

    async def save_merge_results(widget):
        merge_results_file_path = await save_file_dialog("Save Merge Results", "merge.ics")
        if merge_results_file_path:
            with open(merge_results_file_path, 'w') as f:
                f.write(merge_text.value)
            main_window.info_dialog("Save Merge Results", "Merge results saved successfully.")

    async def open_merge_results(widget):
        merge_results_file_path = await main_window.open_file_dialog("Open Merge Results")
        if merge_results_file_path:
            with open(merge_results_file_path, 'r') as f:
                merge_content = f.read()
            await show_content_in_window(merge_content, "Merge Results")

    def on_close(widget):
        merge_window.close()
        main_window.enabled = True

    # Create the merge window
    merge_window = toga.Window(title="Merge ICS Files", size=(1200, 800))
    merge_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

    grid_box = toga.Box(style=Pack(direction=COLUMN, padding=0, flex=1))

    row1 = toga.Box(style=Pack(direction=ROW, padding=10))
    row2 = toga.Box(style=Pack(direction=ROW, padding=10, flex=1))
    row3 = toga.Box(style=Pack(direction=ROW, padding=10))

    excl_text = toga.MultilineTextInput(readonly=True, style=Pack(flex=1))
    remove_text = toga.MultilineTextInput(readonly=True, style=Pack(flex=1))
    merge_text = toga.MultilineTextInput(readonly=True, style=Pack(flex=1))

    row1.add(toga.Label("Exclusions", style=Pack(flex=1)))
    row1.add(toga.Label("Suggested Removals", style=Pack(flex=1)))
    row1.add(toga.Label("New Events", style=Pack(flex=1)))

    row2.add(excl_text)
    row2.add(remove_text)
    row2.add(merge_text)

    spacer = toga.Box(style=Pack(flex=1))
    save_suggestions_button_box = toga.Box(style=Pack(direction=ROW, alignment=CENTER, flex=1))
    save_merge_button_box = toga.Box(style=Pack(direction=ROW, alignment=CENTER, flex=1))

    save_suggestions_button = toga.Button("Save Suggested Removals", on_press=save_suggestions, style=Pack(padding=(0,5)))
    save_merge_button = toga.Button("Save Events to .ics", on_press=save_merge_results, style=Pack(padding=(0,5)))
    open_merge_button = toga.Button("Open Events in Calendar", on_press=open_merge_results, style=Pack(padding=(0,5)))

    save_suggestions_button_box.add(save_suggestions_button)
    save_merge_button_box.add(save_merge_button)
    save_merge_button_box.add(open_merge_button)

    row3.add(spacer)
    row3.add(save_suggestions_button_box)
    row3.add(save_merge_button_box)

    grid_box.add(row1)
    grid_box.add(row2)
    grid_box.add(row3)

    merge_box.add(grid_box)

    merge_window.on_close = on_close
    merge_window.content = merge_box
    merge_window.show()

    main_window.enabled = False

    # Run the merge
    merge(ics1_path, ics2_path, exclusions_path, excl_text, remove_text, merge_text)

async def save_file_dialog(title, suggested):
    file_path = await toga.App.app.main_window.save_file_dialog(title, suggested_filename=suggested)
    return file_path

async def show_content_in_window(content, title):
    content_window = toga.Window(title=title, size=(800, 600))
    content_box = toga.Box(style=Pack(direction=COLUMN, padding=10, flex=1))

    text_area = toga.MultilineTextInput(value=content, readonly=True, style=Pack(flex=1))
    scroll_container = toga.ScrollContainer(content=text_area, style=Pack(flex=1))

    content_box.add(scroll_container)
    content_box.add(toga.Button('Close', on_press=lambda w: content_window.close(), style=Pack(padding=5)))

    content_window.content = content_box
    content_window.show()
