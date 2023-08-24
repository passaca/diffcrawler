"""
Window used to display a string in a textbox.
"""

import tkinter as tk
import tkinter.ttk as ttk


class TextWindow(tk.Toplevel):
    """
    Toplevel window containing only a scrollable textbox. Used to display (possibly long) strings/text.
    """

    def __init__(self, parent: tk.Tk, text: str = '', title: str = '', *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.minsize(300, 300)
        self.title(title)


        self._txt_wdgt = tk.Text(self, width=300, height=300, wrap='none')
        self._txt_wdgt.insert('1.0', text)
        # Disable possibility to edit displayed text
        self._txt_wdgt.configure(state='disabled')
        self._txt_wdgt.grid(column=0, row=0, sticky='nsew')

        self._vsb = ttk.Scrollbar(self, orient='vertical', command=self._txt_wdgt.yview)
        self._vsb.grid(row=0, column=1, sticky='ns')
        self._hsb = ttk.Scrollbar(self, orient='horizontal', command=self._txt_wdgt.xview)
        self._hsb.grid(row=1, column=0, sticky='we')
        self._txt_wdgt.configure(yscrollcommand=self._vsb.set)
        self._txt_wdgt.configure(xscrollcommand=self._hsb.set)

        # Allow closing window with shortcuts
        self.bind('<Command-w>', lambda _: self.destroy())
        self.bind('<Escape>', lambda _: self.destroy())