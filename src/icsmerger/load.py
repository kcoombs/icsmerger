import os
from icalendar import Calendar
from .ical import load_ics, get_event_set
from .exclusions import load_exclusions

# Load files and display information
def load_files(ics1_path, ics2_path, exclusions_path, ics_text, excl_text):
    if ics1_path and not os.path.exists(ics1_path):
        ics_text.value += f"File not found (ICS1): {ics1_path}\n"
        return
    
    if not ics2_path:
        ics_text.value += "ICS2 file must be provided\n"
        return

    if not os.path.exists(ics2_path):
        ics_text.value += f"File not found (ICS2): {ics2_path}\n"
        return

    if exclusions_path and not os.path.exists(exclusions_path):
        ics_text.value += f"File not found (exclusion): {exclusions_path}\n"
        return

    cal1 = load_ics(ics1_path) if ics1_path else Calendar()
    cal2 = load_ics(ics2_path)

    if cal2 is None:
        return

    events1 = get_event_set(cal1) if cal1 else set()
    events2 = get_event_set(cal2)

    earliest_event_ics1 = (min(events1, key=lambda x: x[1])[1]).date() if events1 else None
    latest_event_ics1 = (max(events1, key=lambda x: x[1])[1]).date() if events1 else None
    earliest_event_ics2 = (min(events2, key=lambda x: x[1])[1]).date() if events2 else None
    latest_event_ics2 = (max(events2, key=lambda x: x[1])[1]).date() if events2 else None

    if ics1_path:
        ics_text.value += f"ICS1 contains {len(events1)} events:\n\n"
        if earliest_event_ics1 and latest_event_ics1:
            ics_text.value += f"  - Earliest event in ICS1: {earliest_event_ics1}\n"
            ics_text.value += f"  - Latest event in ICS1: {latest_event_ics1}\n"

    if cal2:
        ics_text.value += f"\nICS2 contains {len(events2)} events:\n\n"
        if earliest_event_ics2 and latest_event_ics2:
            ics_text.value += f"  - Earliest event in ICS2: {earliest_event_ics2}\n"
            ics_text.value += f"  - Latest event in ICS2: {latest_event_ics2}\n"

        if earliest_event_ics2 and earliest_event_ics1 and earliest_event_ics2 < earliest_event_ics1:
            ics_text.value += "\nWarning: ICS2 has events before the earliest event in ICS1\n"
        if latest_event_ics2 and latest_event_ics1 and latest_event_ics1 > latest_event_ics2:
            ics_text.value += "\nWarning: ICS1 has events after the latest event in ICS2\n"

    # Load the exclusions
    exclusions = load_exclusions(exclusions_path) if exclusions_path else []
    if not exclusions_path:
        excl_text.value += "No EXCL file provided.\n\n"
    else:
        exclusions = load_exclusions(exclusions_path)
        if exclusions:
            excl_text.value += f"EXCL contains {len(exclusions)} exclusions:\n\n"
            for excl in exclusions:
                excl_text.value += f"  - '{excl}'\n"
        else:
            excl_text.value += "EXCL file was provided, but it was empty.\n\n"
