from icalendar import Calendar, Event
from datetime import datetime
#from tkinter import messagebox

# Load iCalendar file
def load_ics(file_path):
    try:
        with open(file_path, 'rb') as f:
            return Calendar.from_ical(f.read())
    except Exception as e:
        #messagebox.showerror("Error", f"Failed to load iCal file: {file_path}\n{e}")
        return None
    
# Get set of events from calendar
def get_event_set(cal):
    return {
        (str(component.get('summary')), component.get('dtstart').dt, component.get('dtend').dt)
        for component in cal.walk() if component.name == "VEVENT"
    }

# Create all-day event
def create_all_day_event(event):
    new_event = Event()
    new_event.add('summary', event[0])
    new_event.add('dtstart', event[1].date())
    new_event.add('dtend', event[2].date())
    new_event.add('dtstamp', datetime.now())
    new_event.add('comment', "Processed by CPIMERGE")
    return new_event
