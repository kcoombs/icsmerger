import logging

# Load exclusions from file
def load_exclusions(main_window, file_path):
    try:
        with open(file_path, 'r') as f:
            return [line.strip() for line in f]
    except Exception as e:
        main_window.info_dialog("Error", f"Failed to load exclusions file: {file_path}\n{e}")
        return []

# Filter events based on exclusions
def filter_exclusions(events, exclusions):
    filtered_events = set()
    excluded_events = set()
    for event in events:
        if not any(excl.lower() in event[0].lower() for excl in exclusions):
            filtered_events.add(event)
        else:
            excluded_events.add(event)
    return filtered_events, excluded_events

def print_exclusions(exclusions, excl, file):
    count = 0
    text = ""
    excl.value += f"\nExcluded from {file}:\n\n"
    for event in exclusions:
        text += f"  - {event[0]} on {event[1].date()}\n"
        count += 1
    if count == 0:
        excl.value += "  - Nothing Excluded.\n\n"
    else:
        excl.value += f"{text}"