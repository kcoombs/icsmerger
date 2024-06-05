import logging
from icalendar import Calendar, Event
from datetime import datetime

# Load iCalendar file
def load_ics(window, file_path):
    try:
        with open(file_path, 'rb') as f:
            return Calendar.from_ical(f.read())
    except Exception as e:
        window.info_dialog("Error", f"Failed to load iCal file: {file_path}\n{e}")
        return None
    
# Get set of events from calendar
def get_event_set(cal):
    return {
        (str(component.get('summary')), component.get('dtstart').dt, component.get('dtend').dt)
        for component in cal.walk() if component.name == "VEVENT"
    }

# Get set of events from calendar
def get_event_set_full(cal):
    return {
        (str(component.get('summary')), component.get('dtstart').dt, component.get('dtend').dt, component.get('dtstamp').dt, component.get('uid'), component.get('description'))
        for component in cal.walk() if component.name == "VEVENT"
    }

# Create event
def create_event(event, all_day):
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
