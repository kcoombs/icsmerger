#import tkinter as tk
#from tkinter import messagebox

# Load exclusions from file
def load_exclusions(file_path):
    try:
        with open(file_path, 'r') as f:
            return [line.strip() for line in f]
    except Exception as e:
        #messagebox.showerror("Error", f"Failed to load exclusions file: {file_path}\n{e}")
        return []

# Filter events based on exclusions
def filter_exclusions(events, exclusions, output_text):
    count = 0;
    filtered_events = set()
    if exclusions:
        pass
        #output_text.insert(tk.END, "Excluded:\n\n")
    for event in events:
        if not any(excl.lower() in event[0].lower() for excl in exclusions):
            filtered_events.add(event)
        else:
            if exclusions:
                count += 1
                #output_text.insert(tk.END, f"  - {event[0]} on {event[1].date()}\n")
    if count == 0:
            pass
            #output_text.insert(tk.END, f"  - None\n")
    if exclusions:
        pass
        #output_text.insert(tk.END, "\n")
    return filtered_events
