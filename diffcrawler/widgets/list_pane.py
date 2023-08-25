"""
List widget holding the resources (website list).
"""

from typing import Tuple
from typing import List

import tkinter.ttk as ttk

from diffcrawler.utils.dbscheme import Resource
from diffcrawler.utils.misc import format_date


class ListPane(ttk.Frame):
    """
    Main and central UI widget holding the list of resources (websites).
    Displayed as a pane in the middle of the main window.
    """

    def __init__(self, parent, *args, **kwargs):
        ttk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        # Column names and UI text, in order from left to right
        self._cols = {
            'is_fav': 'Fav',
            'url': 'URL',
            'timeout': 'Timeout',
            'prev_date': 'Prev. Date',
            'cur_date': 'Cur. Date',
            'diff_thresh': 'Thresh',
            'diff_lines': 'Diff',
            'status': 'Status'

        }

        self.columnconfigure(0, weight=1, minsize=100)
        self.columnconfigure(1, weight=1, minsize=100)
        self.columnconfigure(2, weight=0, minsize=0)
        self.rowconfigure(0, weight=1, minsize=100)

        self.list_box = ttk.Treeview(self, columns=list(self._cols.keys()), show='headings')
        self._vsb = ttk.Scrollbar(self, orient='vertical', command=self.list_box.yview)
        self._vsb.grid(column=2, row=0, sticky='nsew')
        self.list_box.configure(yscrollcommand=self._vsb.set)

        # Create columns
        for col, text in self._cols.items():
            self.list_box.heading(col, text=text)

        # Adjust sizes
        self.list_box.column('is_fav', width=40, minwidth=40, stretch=False)
        self.list_box.column('timeout', width=80, minwidth=60, stretch=False)
        self.list_box.column('diff_lines', width=60, minwidth=60, stretch=False)
        self.list_box.column('status', width=60, minwidth=60, stretch=False)
        self.list_box.column('cur_date', width=200, minwidth=200, stretch=False)
        self.list_box.column('diff_thresh', width=80, minwidth=60, stretch=False)
        self.list_box.column('prev_date', width=200, minwidth=200, stretch=False)

        # Inform data controller of changed selection
        self.list_box.bind('<<TreeviewSelect>>', self._selection_changed)

        # Allow keyboard shortcut to select all
        self.list_box.bind('<Command-a>', self._select_all)

        self.list_box.grid(row=0, column=0, columnspan=2, sticky='nsew')

        # Items with tag 'unread' are shown in bold font
        self.list_box.tag_configure('unread', font=('', 0, 'bold'))

    def insert_resource(self, resource: Resource) -> None:
        """Insert a resource into list at its order position."""
        self.list_box.insert('', resource.order, values=self._values_for_cols(resource), iid=resource.id_, tags=self._tags(resource))
    
    def update_resource(self, resource: Resource) -> None:
        """Update an existing resource."""
        self.list_box.item(resource.id_, values=self._values_for_cols(resource), tags=self._tags(resource))
        
    def remove_resource(self, resource: Resource) -> None:
        """"Delete the resource from the list."""
        self.list_box.delete(resource.id_)
        
    def _values_for_cols(self, resource: Resource) -> list:
        """Format the properties of the passed resource for display in the columns and return the list of formatted values."""        
        # For each column, read out corresponding attribute from resource, default is empty string
        values = {col: getattr(resource, col, '') for col in self._cols}

        for date in ['cur_date', 'prev_date']:
            values[date] = format_date(values[date]) if values[date] else ''

        # Change 'None' attributes to empty string, otherwise 'None' is shown in widget
        values = {col: value if value is not None else '' for col, value in values.items()}

        # Format boolean favorite value to unicode star character if True
        values['is_fav'] = '\N{black star}' if values['is_fav'] else ''
        
        if resource.in_process:
            values['status'] = '\N{midline horizontal ellipsis}'
        elif resource.fetch_successful:
            values['status'] = '\N{heavy check mark}'
        elif resource.fetch_successful is False: # 'None' is also falsy so we need to check with 'is' here!
            values['status'] = '\N{heavy ballot x}'
        else: # Here we catch the 'None' case, which is falsy but means "no fetch recorded" and not a failed fetch
            values['status'] = ''
        
        return list(values.values())
    
    def _tags(self, resource: Resource) -> Tuple[str|None]:
        """Return tags for resource (currently only 'unread' available)."""
        tags = ('unread') if resource.is_unread else tuple()
        return tags

    def _selection_changed(self, _) -> None:
        """Inform controller of the selection change."""
        self.controller.selection_changed(list(self.list_box.selection()))

    def select_resource(self, resource: Resource) -> None:
        """Change selection to a certain resource."""
        self.list_box.selection_set(resource.id_)
    
    def _select_all(self, _) -> None:
        """Select all resources in list."""
        self.list_box.selection_set(self.list_box.get_children())