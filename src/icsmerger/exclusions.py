# Load exclusions from file
def load_exclusions(main_window, file_path):
    try:
        with open(file_path, 'r') as f:
            return [line.strip() for line in f]
    except Exception as e:
        main_window.info_dialog("Error", f"Failed to load exclusions file: {file_path}\n{e}")
        return []

# Filter events based on exclusions
def filter_exclusions(events, exclusions, excl_text):
    count = 0;
    filtered_events = set()
    if exclusions:
        excl_text.value += "Excluded:\n\n"
    for event in events:
        if not any(excl.lower() in event[0].lower() for excl in exclusions):
            filtered_events.add(event)
        else:
            if exclusions:
                count += 1
                excl_text.value += f"  - {event[0]} on {event[1].date()}\n"
    if count == 0:
            excl_text.value += f"  - None\n"
    if exclusions:
        excl_text.value += "\n"
    return filtered_events
