"""
Main window, each instance representing one file.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import tkinter.ttk as ttk
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

if TYPE_CHECKING:
    from diffcrawler import DiffCrawler
from diffcrawler.widgets.action_pane import ActionPane
from diffcrawler.widgets.property_pane import PropertyPane
from diffcrawler.widgets.list_pane import ListPane
from diffcrawler.utils.data_controller import DataController
from diffcrawler.utils.misc import IncorrectFileFormatError
from diffcrawler.utils.misc import ShortcutFormatter


class MainWindow(tk.Toplevel):
    """
    Main window class. Each instance represents one open file (either in-memory DB or file on disk).
    """

    def __init__(self, parent: DiffCrawler, path=None, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self.parent = parent

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.minsize(width=750, height=400)

        # Main frame covering window as a whole
        self.mainframe = ttk.Frame(self)
        self.mainframe.columnconfigure(0, weight=0, minsize=100)
        self.mainframe.columnconfigure(1, weight=1, minsize=400)
        self.mainframe.columnconfigure(2, weight=0, minsize=250)
        self.mainframe.rowconfigure(0, weight=1, minsize=300)
        self.mainframe.grid(column=0, row=0, sticky='nsew')

        # Left frame, used for action pane
        self.left_frm = ttk.Frame(master=self.mainframe)
        self.left_frm.columnconfigure(0, weight=1)
        self.left_frm.rowconfigure(0, weight=1)
        self.left_frm.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

        # Middle frame, used for list of resources
        self.middle_frm = ttk.Frame(master=self.mainframe)
        self.middle_frm.columnconfigure(0, weight=1)
        self.middle_frm.rowconfigure(0, weight=1)
        self.middle_frm.grid(row=0, column=1, sticky='nsew')

        # Right frame, used for viewing and changing properties of selected items
        self.right_frm = ttk.Frame(master=self.mainframe)
        self.right_frm.columnconfigure(0, weight=1)
        self.right_frm.rowconfigure(0, weight=1)
        self.right_frm.grid(row=0, column=2, sticky='nsew', padx=10, pady=10)

        # Instantiate panes and put them into place
        self.action_pane = ActionPane(self.left_frm)
        self.action_pane.grid(column=0, row=0, sticky='nsew')

        self.property_pane = PropertyPane(self.right_frm)
        self.property_pane.grid(column=0, row=0, sticky='nsew')

        self.list_pane = ListPane(self.middle_frm)
        self.list_pane.grid(column=0, row=0, sticky='nsew')

        self.load_file(path)

        ## Create menus

        sf = ShortcutFormatter(ws=self.tk.call('tk', 'windowingsystem'))

        self.option_add('*tearOff', False)
        self.menubar = tk.Menu(self)

        # File menu
        self.menu_file = tk.Menu(self.menubar)
        self.menu_file.add_command(label='New', command=self.new, accelerator=sf.accel(key='N', mod1='Shift', mod2='Command'))
        self.menu_file.add_command(label='Open...', command=self.open, accelerator=sf.accel(key='O', mod1='Command'))
        self.menu_file.add_separator()
        self.menu_file.add_command(label='Save', command=self.save, accelerator=sf.accel(key='S', mod1='Command'))
        self.menu_file.add_command(label='Save As...', command=self.save_as, accelerator=sf.accel(key='S', mod1='Shift', mod2='Command'))
        self.menu_file.add_separator()
        self.menu_file.add_command(label='Close', command=self.close, accelerator=sf.accel(key='W', mod1='Command'))
        self.menu_file.add_command(label='Quit', command=self.quit, accelerator=sf.accel(key='Q', mod1='Command'))
        self.menubar.add_cascade(menu=self.menu_file, label='File')

        # Edit menu
        self.menu_edit = tk.Menu(self.menubar)
        self.menu_edit.add_command(label='Undo Fetch', command=self.controller.undo_fetch, accelerator=sf.accel(key='Z', mod1='Command'))
        self.menu_edit.add_separator()
        self.menu_edit.add_command(label='Copy', command=lambda: self.focus_get().event_generate('<<Copy>>'), accelerator=sf.accel(key='C', mod1='Command'))
        self.menu_edit.add_command(label='Paste', command=lambda: self.focus_get().event_generate('<<Paste>>'), accelerator=sf.accel(key='V', mod1='Command'))
        self.menu_edit.add_separator()
        self.menu_edit.add_command(label='Fetch', command=self.controller.fetch, accelerator=sf.accel(key='G', mod1='Command'))
        self.menu_edit.add_separator()
        self.menu_edit.add_command(label='Add', command=self.controller.new_resource, accelerator=sf.accel(key='N', mod1='Command'))
        self.menu_edit.add_command(label='Remove', command=self.controller.remove_resource, accelerator=sf.accel(key='Backspace', mod1='Command'))
        self.menu_edit.add_separator()
        self.menu_edit.add_command(label='Mark Read', command=self.controller.mark_read, accelerator=sf.accel(key='R', mod1='Command'))
        self.menubar.add_cascade(menu=self.menu_edit, label='Edit')

        # View menu
        self.menu_view = tk.Menu(self.menubar)
        self.menu_view.add_command(label='Show Diff', command=self.controller.show_diff, accelerator=sf.accel(key='D', mod1='Command'))
        self.menu_view.add_command(label='Open URL', command=self.controller.open_url, accelerator=sf.accel(key='U', mod1='Command'))
        self.menubar.add_cascade(menu=self.menu_view, label='View')

        self.configure(menu=self.menubar)

        # Set close handler for window manager
        self.protocol('WM_DELETE_WINDOW', self.close)

        ## Create keyboard shortcuts
        # File menu
        self.bind(sf.binding(key='N', mod1='Command'), lambda _: self.new())
        self.bind(sf.binding(key='o', mod1='Command'), lambda _: self.open())
        self.bind(sf.binding(key='s', mod1='Command'), lambda _: self.save())
        self.bind(sf.binding(key='S', mod1='Command'), lambda _: self.save_as())
        self.bind(sf.binding(key='w', mod1='Command'), lambda _: self.close())
        
        # Edit menu
        self.bind(sf.binding(key='z', mod1='Command'), lambda _: self.controller.undo_fetch())
        self.bind('<<Copy>>', self._copy_url)
        self.bind('<<Paste>>', self._paste_url)
        self.bind(sf.binding(key='g', mod1='Command'), lambda _: self.controller.fetch())
        self.bind(sf.binding(key='n', mod1='Command'), lambda _: self.controller.new_resource())
        self.bind(sf.binding(key='BackSpace', mod1='Command'), lambda _: self.controller.remove_resource())
        self.bind(sf.binding(key='r', mod1='Command'), lambda _: self.controller.mark_read())
        
        # View menu
        self.bind(sf.binding(key='d', mod1='Command'), lambda _: self.controller.show_diff())
        self.bind(sf.binding(key='u', mod1='Command'), lambda _: self.controller.open_url())

    def load_file(self, path: str) -> None:
        """Create controller with file at 'path'"""
        try: 
            self.controller =  self._create_controller(path=path)
        # If controller raises exception, inform user and create a controller with in-memory DB (empty new file)
        except IncorrectFileFormatError:
            messagebox.showerror(title='Wrong file format', message=f'The file at path "{path}" is not of correct format.')
            self.controller = self._create_controller(path='')

    def _create_controller(self, path: str) -> DataController:
        """Instantiate and return a new controller object."""
        controller = DataController(
            path=path,
            main_wdw=self,
            action_pane=self.action_pane,
            property_pane=self.property_pane,
            list_pane=self.list_pane
        )

        return controller

    def close(self) -> None:
        """Close this window checking if it is safe to do so (unsaved changes?)"""
        if self.controller.has_unsaved_changes:
            response = messagebox.askyesnocancel(title='Unsaved Changes', message='There are unsaved changes. Do you want to save before closing?')

            # Clicked 'Yes'
            if response:
                if self.save():
                    self.destroy()
                else:
                    return
            # Clicked 'Cancel'
            elif response is None:
                return
            # Clicked 'No'
            else:
                self.destroy()
        else:
            self.destroy()

    def quit(self) -> None:
        """Quit the application as a whole."""
        # Call method on root object to exit the application.
        self.parent.exit()

    def save(self) -> bool:
        """Save current file to disk."""
        # If in-memory DB, we don't have a file to save to, effectively is "save as"
        if self.controller.is_memory_db:
            return self.save_as()
        else:
            return self.controller.save()
        
    def save_as(self) -> bool:
        """Save current file to a new location on disk."""
        path = filedialog.asksaveasfilename(defaultextension='.dfc')

        if path:
            return self.controller.save_as(path)
        # Clicked "cancel"
        else:
            return False

    def open(self) -> None:
        """Open a file from disk."""
        # Ask parent (root application) to handle the open file action.
        self.parent.open_file(called_from=self)


    def _paste_url(self, event: tk.Event) -> None:
        """Create and insert a new resource with the URL from the system clipboard."""
        # All widgets have toplevel window in their bind tags, meaning pasting in an entry widget will not only apply
        # to that widget but also this main window. This could be stopped by returning "break" in the paste
        # event handler of the entry widget, but this function is pre-defined. So this hack (checking if
        # event came from an entry widget) helps mitigate this issue:
        if isinstance(event.widget, ttk.Entry):
            return
        
        # Empty clipbboards raise an exception
        try:
            content = self.clipboard_get()
        # Don't do anything if clipboard is empty
        except tk.TclError:
            pass
        # Otherwise paste
        else:
            self.controller.new_resource(url=content)

    def _copy_url(self, even: tk.Event) -> None:
        """Copy the URLs of the selected resources to the system clipboard."""
        # See comment in '_paste_url' method
        if isinstance(even.widget, ttk.Entry):
            return
        
        self.clipboard_clear()
        self.clipboard_append(self.controller.selected_urls())

    def new(self) -> None:
        """Create a new and empty main window."""
        # Ask root application to handle the new window action
        self.parent.new_window()

    def destroy(self, *args, **kwargs) -> None:
        """Destroy this main window and inform parent (root application) that it should be removed from list."""
        super().destroy(*args, **kwargs)
        self.parent.main_window_destroyed(main_window=self)