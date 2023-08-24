"""
Main app class used to instantiate application as a whole.
"""

from typing import List
import os
import argparse

import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox

from diffcrawler.widgets.main_window import MainWindow


class DiffCrawler(tk.Tk):
    """Main app class meant to represent app and is instantiated once."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Hide root window
        self.withdraw()

        # Set handlers for OS functions
        self.protocol('WM_DELETE_WINDOW', self.exit)
        self.createcommand('tk::mac::OpenDocument', lambda *paths: self.open_file(paths=paths))

        # Keep list of created main windows
        self._main_windows: List[MainWindow] = []
        
        self.new_window()

        # Must be called after main window is created, otherwise menu of main window overwrites this
        self.createcommand('tk::mac::Quit', self.exit)

        # Check if files were given via command line
        self._parse_args()
    
    def _parse_args(self) -> None:
        """Parse command-line arguments (paths to files to be opened)."""
        parser = argparse.ArgumentParser(
            prog='python -m diffcrawler',
            description='GUI tool to monitor website changes',
            )
        parser.add_argument('file_paths', type=str, nargs='*', help='Paths to DiffCrawler file(s) to open')
        self.args = parser.parse_args()
        if self.args.file_paths:
            self.open_file(paths=self.args.file_paths)

    def create_main_window(self, path: str) -> None:
        """Instantiate new main window and append it to main window list"""
        self._main_windows.append(MainWindow(self, path=path))
        
    def open_file(self, called_from: MainWindow = None, paths: List[str] = None) -> None:
        """Open files(s) from a list of paths or ask user to choose file."""
        
        # Ask for which file to open if none were passed
        if not paths:
            paths = []
            path = filedialog.askopenfilename(filetypes=[('DiffCrawler Files', '*.dfc')])
            # Return if user cancels open dialog
            if not path:
                return
            else:
                paths.append(path)

        # Slice index to make copy of list (original list modified during loop!)
        for path in paths[:]:
            if not os.path.exists(path):
                messagebox.showerror(title='File not found', message=f'The file at path "{path}" could not be found.')
                paths.remove(path)

        for path in paths:
            # If file already open, just switch to corresponding window
            already_open_wdw = self.already_open(path)
            if already_open_wdw:
                already_open_wdw.lift()
                continue

            # If open was called from certain window, open file inside it if window is empty
            if called_from:
                if self.is_empty_wdw(called_from):
                    called_from.load_file(path)
                else:
                    self.create_main_window(path)
            else:
                # Check if there are empty windows
                empty_wdw = None
                for wdw in self._main_windows:
                    if self.is_empty_wdw(wdw):
                        empty_wdw = wdw
                        break
                # Use empty window or create new one
                if empty_wdw:
                    empty_wdw.load_file(path)
                    empty_wdw.lift()
                else:
                    self.create_main_window(path)

    def already_open(self, path: str) -> MainWindow | None:
        """Check if window for that path already exists (meaning file is already open)."""
        for wdw in self._main_windows:
            if wdw.controller.path == path:
                return wdw
        return None
    
    def is_empty_wdw(self, wdw: MainWindow) -> bool:
        """Check if window is newly created empty window without any modifications."""
        if not wdw.controller.has_unsaved_changes and wdw.controller.is_memory_db:
            return True
        else:
            return False

    def new_window(self) -> None:
        """Create empty window."""
        self.create_main_window(path='')

    def main_window_destroyed(self, main_window: MainWindow) -> None:
        """Register that a main window was destroyed, remove it from list and exit if it was the last window."""
        self._main_windows.remove(main_window)
        if len(self._main_windows) == 0:
            self.destroy()
        
        
    def exit(self) -> None:
        """Close all windows and (consequently) exit the whole application."""
        for wdw in self._main_windows[:]: # Slice index to make copy (close() changes list during loop!)
            wdw.close()


   