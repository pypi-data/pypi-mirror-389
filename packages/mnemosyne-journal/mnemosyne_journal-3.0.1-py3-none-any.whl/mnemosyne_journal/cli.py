import argparse
from datetime import datetime
from sys import stderr
import getpass
from mnemosyne_journal.journal import JournalEntry


__version__ = "3.0.1"


def show_license_details() -> None:
    print(
        "This app is licensed under the GPL v3 or later license. Please see\n<https://www.gnu.org/licenses/gpl-3.0.en.html> for a complete copy of the license, as well as the LICENSE.md\nfile included with this Python package."
    )


def show_copying() -> None:
    print(
        "For full information on what is and is not allowed in term of copying, distribution, and\nreuse of the code in this app, please see the full license at\n<https://www.gnu.org/licenses/gpl-3.0.en.html>."
    )


def get_user_entry_choice(journal_entries: list[str]) -> str:
    entry_count = len(journal_entries)
    print("Please select an entry to view:")
    for index, entry_name in enumerate(journal_entries, start=1):
        entry = datetime.strptime(entry_name, "%Y%m%d%H%M%S")
        print(f"{index}) {entry.strftime('%b %d %Y  %H:%M:%S')}")
    while True:
        selection = int(input(f"Please select a number between 1 and {entry_count}: "))
        if 1 <= selection and entry_count >= selection:
            break
    return journal_entries[selection - 1]


def get_user_password():
    prompt = "Please enter the password: "
    try:
        return getpass.getpass(prompt)
    except getpass.GetPassWarning:
        print(
            "[Warning] Could not control echo behavior for password entry.",
            file=stderr,
        )
        return input(prompt)


def cli() -> None:
    parser = argparse.ArgumentParser()
    program_flow_arguments_helper = parser.add_argument_group("Main Arguments:")
    program_flow_arguments = (
        program_flow_arguments_helper.add_mutually_exclusive_group()
    )
    program_flow_arguments.add_argument(
        "-c",
        "--content",
        help="The content of the journal entry. I.e. the text you are writing.",
    )
    program_flow_arguments.add_argument(
        "-o",
        "--open",
        help="Opens up a specific journal entry for reading given the entry timestamp in the YYYYMMDDHHMMSS format.",
    )
    program_flow_arguments.add_argument(
        "-r",
        "--read",
        help="Display a list of all journal entries and then select one for viewing.",
        action="store_true",
    )
    optional = parser.add_argument_group("Optional Arguments:")
    optional.add_argument(
        "-p", "--password", help="The password used for encryption/decryption."
    )
    program_info_arguments_helper = parser.add_argument_group("Misc Arguments:")
    program_info_arguments = (
        program_info_arguments_helper.add_mutually_exclusive_group()
    )
    program_info_arguments.add_argument(
        "-v",
        "--version",
        help="Show the version information for this app.",
        action="store_true",
    )
    program_info_arguments.add_argument(
        "-l",
        "--license-details",
        help="Print the working license for this app.",
        action="store_true",
    )
    program_info_arguments.add_argument(
        "-s",
        "--show-copying",
        help="Print the conditions under which the code for this app can be reused.",
        action="store_true",
    )
    args = parser.parse_args()

    provided_arguments = sum(
        [
            1
            for item in [
                args.content,
                args.open,
                args.read,
                args.version,
                args.license_details,
                args.show_copying,
            ]
            if item
        ]
    )
    if provided_arguments > 1:
        print(
            "Please select only one of the options: --content, --open, --read, --version, --license-details, --show_copying; at a time."
        )
        return

    if args.version:
        print(f"Mnemosyne Journaling by Siru: Version {__version__}")
        return

    if args.license_details:
        show_license_details()
        return

    if args.show_copying:
        show_copying()
        return

    if args.open is not None:
        if args.password is None:
            args.password = get_user_password()
        entry = JournalEntry.load_saved_journal_entry(args.open + ".txt")
        entry.decrypt_text(args.password)
        print(f"Entry Text:\n{entry.plaintext}")
        return

    if args.read:
        entry_id = get_user_entry_choice(JournalEntry.list_stored_journal_entries())
        entry = JournalEntry.load_saved_journal_entry(entry_id + ".txt")
        if args.password is None:
            args.password = get_user_password()
        entry.decrypt_text(args.password)
        print(f"Entry Text:\n{entry.plaintext}")
        return

    if args.content is not None:
        entry = JournalEntry(args.content)
        if args.password is None:
            args.password = get_user_password()
        entry.make_encryption_key(args.password)
        entry.encrypt_text()
        entry.store_journal_entry()
        print("The journal entry was stored succesfully.")
        return

    print("Please enter your journal entry and finish with two newlines:")
    plaintext = ""
    while True:
        line = input()
        plaintext += line + "\n"
        if len(plaintext) >= 3 and plaintext.endswith("\n\n\n"):
            break
    plaintext = plaintext[:-2]  # Ends in newline
    entry = JournalEntry(plaintext)
    if args.password is None:
        args.password = get_user_password()
    entry.make_encryption_key(args.password)
    entry.encrypt_text()
    entry.store_journal_entry()
    print("The journal entry was stored succesfully.")
