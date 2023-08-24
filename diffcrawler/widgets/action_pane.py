"""
Action widget.
"""

import tkinter.ttk as ttk


class ActionPane(ttk.Frame):
    """
    Class representing the UI for the action widget. Containing buttons for the most common actions.
    Displayed as a pane in the left frame in the main window.
    """
    
    def __init__(self, parent, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self.fetch_btn = ttk.Button(self, text='Fetch', command=lambda: self.controller.fetch())
        self.fetch_btn.grid(column=0, row=0, sticky='we')

        self.open_btn = ttk.Button(self, text='Open URL', command=lambda: self.controller.open_url())
        self.open_btn.grid(column=0, row=1, sticky='we')
        

        self.add_btn = ttk.Button(self, text='Add', command=lambda: self.controller.new_resource())
        self.add_btn.grid(column=0, row=3, sticky='we')

        self.remove_btn = ttk.Button(self, text='Remove', command=lambda: self.controller.remove_resource())
        self.remove_btn.grid(column=0, row=4, sticky='we')