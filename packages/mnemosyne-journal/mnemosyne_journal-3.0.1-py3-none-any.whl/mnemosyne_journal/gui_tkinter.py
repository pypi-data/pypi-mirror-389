"""
A tkinter/ttk based GUI frontend for the JournalEntry class.
"""

from datetime import datetime
import pathlib

import darkdetect
import sv_ttk
import tkinter as tk
from tkinter import ttk, messagebox

from mnemosyne_journal.journal import JournalEntry


def save_new_journal_entry(text: str, password: str) -> bool:
    """
    Given a text and a corresponding password, stores the text as a new journal entry on disk. If there are any issues and the saving cannot be completed, returns False. If the storing is successful, returns True.
    """

    # Create a new journal entry object
    entry = JournalEntry(text)

    # Try to create an encryption key based on the provided password
    if not entry.make_encryption_key(password):
        return False

    # Encrypt the journal entry with the new encryption key
    entry.encrypt_text()

    # Try to store the journal entry on disk
    if not entry.store_journal_entry():
        return False

    # Return true if saving was successful
    return True


def open_selected_entry(entry_time: str, password: str, text_widget: tk.Text):
    """
    Given an entry time id and a password, decrypts, opens, and displays this journal entry for reading.
    """

    # Check if a password was provided
    if not len(password):
        messagebox.showwarning(
            title="Password Error", message="Please provide a password."
        )
        return

    # Convert the entry time back to filename pattern
    entry_time = datetime.strptime(entry_time, "%b %d %Y - %H:%M:%S")
    file_id = entry_time.strftime("%Y%m%d%H%M%S.txt")

    # Load the entry object from the file
    entry: JournalEntry = JournalEntry.load_saved_journal_entry(file_id)

    # Attempt decryption
    decryption_success = entry.decrypt(password)
    if not decryption_success:
        messagebox.showwarning(
            title="Password Error", message="Please provide the correct password."
        )
        return

    # Uppon successful decryption set the text widget to the plaintext entry
    text_widget.configure(state="normal")
    text_widget.delete("1.0", "end")
    text_widget.insert("1.0", entry.plaintext)
    text_widget.configure(state="disabled")


def list_available_journal_entries(
    directory_path: pathlib.Path = JournalEntry.default_storage_location,
) -> list[str]:
    """
    Returns a list of all journal entries that could be found in a given directory.
    """

    # Get the raw filename for the journal entries
    raw_entry_names: list[str] = JournalEntry.list_stored_journal_entries(
        directory_path
    )

    # Check to make sure there are any journal entries
    if not len(raw_entry_names):
        # There are no journal entries available
        return []

    # Sort the entry names with the newest entry at the beginning
    sorted_raw_entry_names: list[str] = sorted(raw_entry_names, reverse=True)

    # Convert the filename into more humanly readable names (e.g. Oct 01 2025 - 12:45:00)
    formatted_entry_names: list[str] = [
        datetime.strptime(stem, "%Y%m%d%H%M%S").strftime("%b %d %Y - %H:%M:%S")
        for stem in sorted_raw_entry_names
    ]

    return formatted_entry_names


class GUIApp:
    def __init__(self, root):
        # Set instance variables
        self.root: tk.Tk = root
        self.default_grid_gap: int = 5

        # Perform setup methods
        self.root.title("Mnemosyne Journal")
        self.init_tab_book()
        self.init_writing_tab()
        self.init_reading_tab()
        self.set_theme()
        self.init_custom_menubar()

    def writing_save(self) -> None:
        """
        Takes the text input and the password input from the writing tab and attempts to permanently save this as a new journal entry. If either the text or the password entries are empty, then a warning message is displayed to the user, and further processing is halted. If the saving is successful, then a positive message is shown to the user. If saving is unsuccessful, then an error message is shown to the user and the content & password are kept in the text & entry GUI widgets.
        """

        # Extract the password
        password: str = self.writing_password_entry.get()

        # Check if a password has been provided
        if not len(password):
            messagebox.showwarning(
                title="Password Needed",
                message="Please provide a password in the password entry box.",
            )
            return

        # Extract the text content
        text: str = self.writing_content.get("1.0", "end-1c")

        # Check that text content was provided
        if not len(text):
            messagebox.showwarning(
                title="Content Needed",
                message="Please provide a journal entry in the text entry box.",
            )
            return

        # Call a method to save the text content as a new journal entry
        if not save_new_journal_entry(text, password):
            messagebox.showwarning(
                title="Saving Failed", message="The journal entry could not be saved."
            )
            return

        # Reload the reading tab saved journal entries list to reflect the newest entry
        self.rjournal_selector.configure(values=list_available_journal_entries())

        # Report successful save to the user
        messagebox.showinfo(
            title="Entry Saved", message="The journal entry was successfully saved."
        )

        # Remove text and password content from screen
        self.writing_content.delete("1.0", "end")
        self.writing_password_entry.delete(0, "end")

    def reading_open(self):
        # TODO Implement
        pass

    def init_tab_book(self):
        self.tab_anchor: ttk.Notebook = ttk.Notebook(self.root)
        self.tab_anchor.pack(expand=True, fill="both")

    def init_writing_tab(self):
        # Writing Tab Layout:
        #   [ ] [0]            [1]            [2]            [3]
        #   [0] <content.........................................>
        #   [1] <wpassw_label> <wpassw_entry> <w_submit_btn> <...>

        # Setup the tab itself
        self.writing_tab: ttk.Frame = ttk.Frame(self.tab_anchor)
        self.tab_anchor.add(self.writing_tab, text="Writing")

        # Setup the writing tab widgets
        self.writing_content: tk.Text = tk.Text(
            self.writing_tab, width=80, height=10, font="sans-serif", wrap="word"
        )
        self.writing_password_entry_label: ttk.Label = ttk.Label(
            self.writing_tab, text="Password:"
        )
        self.writing_password_entry: ttk.Entry = ttk.Entry(self.writing_tab, show="*")
        self.writing_submit_button: ttk.Button = ttk.Button(
            self.writing_tab, text="Save Entry", command=self.writing_save
        )

        # Position writing tab widgets
        self.writing_content.grid(
            column=0,
            row=0,
            padx=self.default_grid_gap,
            pady=self.default_grid_gap,
            columnspan=4,
            sticky="nsew",
        )
        self.writing_password_entry_label.grid(
            column=0,
            row=1,
            padx=self.default_grid_gap,
            pady=self.default_grid_gap,
            sticky="nsew",
        )
        self.writing_password_entry.grid(
            column=1,
            row=1,
            padx=self.default_grid_gap,
            pady=self.default_grid_gap,
            sticky="nsew",
        )
        self.writing_submit_button.grid(
            column=2,
            row=1,
            padx=self.default_grid_gap,
            pady=self.default_grid_gap,
            sticky="nsew",
        )

        # Configure writing tab stretching
        self.writing_tab.columnconfigure(3, weight=1)
        self.writing_tab.rowconfigure(0, weight=1)

    def init_reading_tab(self):
        # Reading Tab Layout:
        #   [ ] [0]              [1]                 [2]           [3]
        #   [0] <rjournal_label> <rjournal_selector> <rsubmit_btn> <...>
        #   [1] <rpassw_label>   <rpassw_entry>      <...>         <...>
        #   [2] <rcontent .............................................>

        # Set up the tab itself
        self.reading_tab: ttk.Frame = ttk.Frame(self.tab_anchor)
        self.tab_anchor.add(self.reading_tab, text="Reading")

        # Set up the widgets in the tab
        self.rjournal_label = ttk.Label(self.reading_tab, text="Entry:")
        self.rjournal_selector = ttk.Combobox(
            self.reading_tab, values=list_available_journal_entries()
        )
        self.rsubmit_btn = ttk.Button(
            self.reading_tab,
            text="Open Entry",
            command=lambda: open_selected_entry(
                self.rjournal_selector.get(), self.rpassw_entry.get(), self.rcontent
            ),
        )
        self.rpassw_label = ttk.Label(self.reading_tab, text="Password:")
        self.rpassw_entry = ttk.Entry(self.reading_tab, show="*")
        self.rcontent = tk.Text(
            self.reading_tab,
            state="disabled",
            width=80,
            height=10,
            highlightthickness=0,
            font="sans-serif",
            wrap="word",
        )

        # Perform grid layout in the tab
        self.rjournal_label.grid(
            column=0,
            row=0,
            padx=self.default_grid_gap,
            pady=self.default_grid_gap,
            sticky="nsew",
        )
        self.rjournal_selector.grid(
            column=1,
            row=0,
            padx=self.default_grid_gap,
            pady=self.default_grid_gap,
            sticky="nsew",
        )
        self.rsubmit_btn.grid(
            column=2,
            row=0,
            padx=self.default_grid_gap,
            pady=self.default_grid_gap,
            sticky="nsew",
        )
        self.rpassw_label.grid(
            column=0,
            row=1,
            padx=self.default_grid_gap,
            pady=self.default_grid_gap,
            sticky="nsew",
        )
        self.rpassw_entry.grid(
            column=1,
            row=1,
            padx=self.default_grid_gap,
            pady=self.default_grid_gap,
            sticky="nsew",
        )
        self.rcontent.grid(
            column=0,
            row=2,
            padx=self.default_grid_gap,
            pady=self.default_grid_gap,
            sticky="nsew",
            columnspan=4,
        )

        # Configure tab stretching
        self.reading_tab.columnconfigure(3, weight=1)
        self.reading_tab.rowconfigure(2, weight=1)

    def set_theme(self):
        # Apply the special tkinter theme. See more at: https://github.com/rdbende/Sun-Valley-ttk-theme
        #   License: MIT
        # Potentially use darkmode. See more at: https://github.com/albertosottile/darkdetect
        #   License BSD-3-Clause
        sv_ttk.set_theme(darkdetect.theme())

    def start_app(self):
        self.root.mainloop()

    def init_custom_menubar(self) -> None:
        """
        Create an empty menubar, and attach it as the default to this GUI window.
        """
        self.menubar: tk.Menu = tk.Menu(self.root)
        self.root.configure(menu=self.menubar)


def start_tk_themed_gui():
    """
    Starts up a tkinter GUI to use the mnemosyne journal application graphically.
    """
    root: tk.Tk = tk.Tk()
    app: GUIApp = GUIApp(root)
    app.start_app()
