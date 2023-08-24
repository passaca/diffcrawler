"""
Property widget.
"""

from typing import List
import tkinter.ttk as ttk
import tkinter as tk

from diffcrawler.utils.dbscheme import Resource
from diffcrawler.utils.misc import format_date
from diffcrawler.utils.misc import is_valid_url


class PropertyPane(ttk.Frame):
    """
    Class representing the UI for the property widget. Used to inspect and change properties of the selected resources.
    Displayed as a pane in the right frame in the main window.
    """

    def __init__(self, parent, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        self.columnconfigure(0, weight=1, minsize=200)

        # URL property        
        self._url = ''
        self._url_ent_value = tk.StringVar()
        self._url_lbl = ttk.Label(self, text='URL')
        self._url_ent = ttk.Entry(self, textvariable=self._url_ent_value)
        # Methodos for applying or canceling modifications by user
        self._url_ent.bind('<FocusOut>', lambda _: self._validate_edit('url'))
        self._url_ent.bind('<Return>', lambda _: self._validate_edit('url'))
        self._url_ent.bind('<Escape>', lambda _: self._reject_edit('url'))

        # Timeout property
        self._timeout = ''
        self._timeout_ent_value = tk.StringVar()
        self._timeout_lbl = ttk.Label(self, text='Timeout (sec)')
        self._timeout_spbx = ttk.Spinbox(self, textvariable=self._timeout_ent_value, from_=1, to=9999, increment=1, command=lambda: self._validate_edit('timeout'))
        # Methodos for applying or canceling modifications by user
        self._timeout_spbx.bind('<FocusOut>', lambda _: self._validate_edit('timeout'))
        self._timeout_spbx.bind('<Return>', lambda _: self._validate_edit('timeout'))
        self._timeout_spbx.bind('<Escape>', lambda _: self._reject_edit('timeout'))
        
        # Diff threshold property
        self._diff_thresh = ''
        self._diff_thresh_ent_value = tk.StringVar()
        self._diff_thresh_lbl = ttk.Label(self, text='Diff Threshold')
        self._diff_thresh_spbx = ttk.Spinbox(self, textvariable=self._diff_thresh_ent_value, from_=1, to=9999, increment=1, command=lambda: self._validate_edit('diff_thresh'))
        # Methodos for applying or canceling modifications by user
        self._diff_thresh_spbx.bind('<FocusOut>', lambda _: self._validate_edit('diff_thresh'))
        self._diff_thresh_spbx.bind('<Return>', lambda _: self._validate_edit('diff_thresh'))
        self._diff_thresh_spbx.bind('<Escape>', lambda _: self._reject_edit('diff_thresh'))

        # Favorite property
        self._is_fav = tk.IntVar()
        self._fav_box = ttk.Checkbutton(self, text='Favorite', variable=self._is_fav, command=lambda : self._property_changed('is_fav'))

        # Added date property
        self._added_lbl = ttk.Label(self, text='Added')
        self._date_lbl = ttk.Label(self, text='')

        # Widget starts out invisible (empty window with empty list)
        self._show_fields(hidden=True)

    def _show_fields(self, hidden=False) -> None:
        """Show or hide the property fields."""
        # Show all fields
        if not hidden:
            self._url_lbl.grid(column=0, row=0, sticky='ew')
            self._url_ent.grid(column=0, row=1, sticky='ew', pady=(0,20))
            self._timeout_lbl.grid(column=0, row=2, sticky='ew')
            self._timeout_spbx.grid(column=0, row=3, sticky='ew', pady=(0,20)) 
            self._diff_thresh_lbl.grid(column=0, row=4, sticky='ew')
            self._diff_thresh_spbx.grid(column=0, row=5, sticky='ew', pady=(0,20)) 
            self._fav_box.grid(column=0, row=6, sticky='ew')
            self._added_lbl.grid(column=0, row=7, sticky='ew', pady=(30,5))
            self._date_lbl.grid(column=0, row=8, sticky='ew')
        # Hide all fields
        else:
            for field in self.grid_slaves():
                field.grid_remove()

    def show_properties(self, resources: List[Resource]) -> None:
        """Show the properties of the passed resource."""
        # Single item selection mode -> show all property fields
        if len(resources) == 1:
            self._url = resources[0].url if resources[0].url is not None else ''
            self._url_ent_value.set(self._url)
            self._timeout = str(resources[0].timeout)
            self._timeout_ent_value.set(resources[0].timeout)
            self._diff_thresh = str(resources[0].diff_thresh)
            self._diff_thresh_ent_value.set(resources[0].diff_thresh)
            self._is_fav.set(1 if resources[0].is_fav else 0)
            date_string = format_date(resources[0].added_date)
            self._date_lbl.config(text=date_string)
            self._show_fields()
        # No selection -> hide all fields
        elif len(resources) == 0:
            self._show_fields(hidden=True)
        # Multiple item selection mode -> only timeout, diff-threshold and favorite-state changeable
        else:
            self._timeout = ''
            self._timeout_ent_value.set('')
            self._diff_thresh = ''
            self._diff_thresh_ent_value.set('')
            self._is_fav.set(0)
            self._url_lbl.grid_remove()
            self._url_ent.grid_remove()
            self._added_lbl.grid_remove()
            self._date_lbl.grid_remove()
   
    def _validate_edit(self, property: str) -> None:
        """Check the validity of the new property value and accept or reject the change."""
        edit_valid = False

        if property == 'url':
            valid_url = is_valid_url(self._url_ent_value.get())
            # Entry must be valid URL or nothing AND entry field must be on grid (single item selection).
            # For multiple item selection with shift or cmd after single selection, the entry field does not lose focus
            # (maybe a bug in treeview). This causes a bug in which on next focus loss (clicking anywhere else), there is
            # a url change triggered although we're in multi item mode and the URL field is invisible. Checking for
            # grid_info() fixes this (returns empty dict if not on grid):
            edit_valid = (self._url_ent_value.get() == '' or valid_url) and self._url_ent.grid_info()
        elif property == 'timeout' or property == 'diff_thresh':
            try:
                int_val = int(getattr(self, f'_{property}_ent_value').get())
            except ValueError:
                edit_valid = False
            else:
                edit_valid = True if int_val > 0 else False

        if edit_valid:
            self._accept_edit(property)
        else:
            self._reject_edit(property)
    
    def _accept_edit(self, property: str) -> None:
        """"Accept and set the new property value."""
        setattr(self, f'_{property}', getattr(self, f'_{property}_ent_value').get())
        self._property_changed(property)
        # Make field lose focus
        self.focus_set()
    
    def _reject_edit(self, property: str) -> None:
        """Reject the new property value and revert field to 'old' value."""
        getattr(self, f'_{property}_ent_value').set(getattr(self, f'_{property}'))
        # Make field lose focus
        self.focus_set()

    def _property_changed(self, property: str) -> None:
        """Inform controller about property change and pass the correctly formatted new value."""
        if property == 'url':
            new_value = self._url
        elif property == 'timeout':
            new_value = int(self._timeout)
        elif property == 'diff_thresh':
            new_value = int(self._diff_thresh)
        elif property == 'is_fav':
            new_value = True if self._is_fav.get() == 1 else False
        
        self.controller.property_changed(property, new_value)

    def focus_url_field(self) -> None:
        """Set focus to the URL field."""
        self._url_ent.focus_set()