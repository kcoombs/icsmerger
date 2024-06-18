import logging
from icalendar import Calendar, Event
from datetime import datetime

def load_ics(window, file_path):
    """
    Load an iCalendar file.

    Args:
        window: The window object to display error messages.
        file_path: The path to the iCalendar file.

    Returns:
        The loaded iCalendar object if successful, None otherwise.
    """
    try:
        with open(file_path, 'rb') as f:
            return Calendar.from_ical(f.read())
    except Exception as e:
        window.info_dialog("Error", f"Failed to load iCal file: {file_path}\n{e}")
        return None
    
def get_event_set(cal):
    """
    Get a set of events from a calendar.

    Args:
        cal: The iCalendar object.

    Returns:
        A set of events, where each event is represented as a tuple of (summary, dtstart, dtend).
    """
    return {
        (str(component.get('summary')), component.get('dtstart').dt, component.get('dtend').dt)
        for component in cal.walk() if component.name == "VEVENT"
    }

def get_event_set_full(cal):
    """
    Get a set of events with additional details from a calendar.

    Args:
        cal: The iCalendar object.

    Returns:
        A set of events, where each event is represented as a tuple of (summary, dtstart, dtend, dtstamp, uid, description).
    """
    return {
        (str(component.get('summary')), component.get('dtstart').dt, component.get('dtend').dt, component.get('dtstamp').dt, component.get('uid'), component.get('description'))
        for component in cal.walk() if component.name == "VEVENT"
    }

def create_event(event, all_day):
    """
    Create a new event.

    Args:
        event: A tuple representing the event with (summary, dtstart, dtend).
        all_day: A boolean indicating if the event is an all-day event.

    Returns:
        The newly created Event object.
    """
    new_event = Event()
    new_event.add('summary', event[0])
    if all_day:
        new_event.add('dtstart', event[1].date())
        new_event.add('dtend', event[2].date())
    else:
        new_event.add('dtstart', event[1])
        new_event.add('dtend', event[2])
    new_event.add('dtstamp', datetime.now())
    new_event.add('comment', "Processed by ICSMERGER")
    return new_event
