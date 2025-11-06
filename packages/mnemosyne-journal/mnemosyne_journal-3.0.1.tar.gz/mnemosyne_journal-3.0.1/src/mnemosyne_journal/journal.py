"""
Classes and methods related to individual journal entries.
"""

import base64
from Cryptodome.Cipher import AES
import pathlib
from datetime import datetime
import argon2
from sys import stderr


class JournalEntry:
    """
    Structure to contain all the information necessary for the encryption/decryption of a single
    journal entry.
    """

    default_storage_location: pathlib.Path = (
        pathlib.Path().home() / ".mnemosyne" / "entries"
    )
    """A default, OS independent storage location for journal entries."""

    def __init__(self, plaintext: str = ""):
        """
        Create a new journal entry. Initialized with only the plain text of the journal entry or an
        empty string if no starting content was provided. No encrypted version present yet until
        the encryption method of this class is called.
        """
        self.plaintext: str = plaintext
        """The journal entry in un-encrypted plaintext human readable format."""
        self.ciphertext: bytes = None
        """The journal entry in encrypted ssafely storable format."""
        self.nonce: bytes = None
        """The nonce used in creating the encrypted version of the journal entry's content."""
        self.tag: bytes = None
        """The message authentication tag generated as part of the encryption process."""
        self.argon_type: str = None
        """The type of the argon2 password hashing algorithm used in the encryption process."""
        self.argon_version: str = None
        """The argon2-cffi version used for the password hashing."""
        self.argon_params: str = None
        """The parameters used for the argon2 hashing to make the hashing reproducible."""
        self.salt: str = None
        """The salt used for the argon2 password hashing."""
        self.password_hash: str = None
        """The argon2 computed hash of the user provided password."""
        self.log_messages: list[str] = []
        """List of error messages that have been caused by this object"""

    def __str__(self) -> str:
        """Returns a user readable presentation of the journal entry. If neither a ciphertext nor a plaintext version exists, an error message is returned. If a plaintext exists, then this is returned. And if only an encrypted verison exists, then the encryption parameters (mac, argon2, salt, nonce) are returned, along with all existing error messages."""
        if not self.plaintext and not self.ciphertext:
            return "This journal entry has no content."

        if self.plaintext:
            return self.plaintext

        representation = (
            "Is encrypted: √\n"
            + "Is MAC tagged: √\n"
            + f"Argon2: {self.argon_type};{self.argon_version};{self.argon_params}\n"
            + f"Argon Salt: {self.salt}\n"
            + f"AES Nonce: {base64.b64encode(self.nonce).decode('utf-8')}\n"
        )

        if len(self.log_messages) > 0:
            representation += "Error Messages for this object:\n"
            for item in self.log_messages:
                representation += f"  - {item}\n"

        return representation

    def create_storage_representation(self) -> str:
        """Returns a string representation of all the encrypted/encryption information attached to
        this string that can be used for long term storage outside of the running application. The format is as follows:
        ```
        Nonce$...\n
        Tag$...\n
        Argon Type$...\n
        Argon Version$...\n
        Argon Params$...\n
        Argon Salt$...\n
        Ciphertext$...\n
        ```
        with each of the entries (the ...) being base64 encoded.

        If this method is called before the journal entry was encrypted it will return an empty string and log an error message in `.log_messages`.
        """
        # Log an error if there is no ciphertext, and thus this entry is not ready to be stored
        if not self.ciphertext:
            error_message = f"[ERROR] JournalEntry {id(self)} tried to be stored before being encrypted."
            self.log_messages.append(error_message)
            print(error_message, file=stderr)
            return ""

        # Convert the bytes type attributes to base64 utf-8 text
        nonce_b64: str = base64.b64encode(self.nonce).decode("utf-8")
        tag_b64: str = base64.b64encode(self.tag).decode("utf-8")
        ciphertext_b64: str = base64.b64encode(self.ciphertext).decode("utf-8")

        # Return everything required to be long term stored for the decryption of this journal entry
        return (
            f"Nonce${nonce_b64}\n"
            + f"Tag${tag_b64}\n"
            + f"Argon Type${self.argon_type}\n"
            + f"Argon Version${self.argon_version}\n"
            + f"Argon Params${self.argon_params}\n"
            + f"Argon Salt${self.salt}\n"
            + f"Ciphertext${ciphertext_b64}\n"
        )

    def encrypt_text(self) -> None:
        """
        Takes the `.plaintext` & `.password_hash` attributes of this object and encrypt the journal text using aes256 bit open codebook mode. Stores the result of the encryption in the `.ciphertext` attribute, as well as the cipher nonce (in `.nonce`) and the message authentication tag (in `.tag`).
        """
        # Convert the password hash into binary representation
        # More info on padding: <https://stackoverflow.com/questions/2941995/>
        password_hash_binary = base64.b64decode(
            self.password_hash + "=" * (-len(self.password_hash) % 4)
        )
        # Create an AES cipher object
        cipher = AES.new(password_hash_binary, AES.MODE_OCB)
        assert len(cipher.nonce) == 15
        self.nonce = cipher.nonce
        # Convert plaintext into binary representation
        data = self.plaintext.encode("utf-8")
        # Encrypt
        ciphertext, tag = cipher.encrypt_and_digest(data)
        # Save
        self.ciphertext = ciphertext
        self.tag = tag

    def store_journal_entry(
        self,
        directory_path: pathlib.Path = default_storage_location,
        file_name: str = "",
    ) -> bool:
        """
        Using the `create_storage_representation` method stores a representation of this object either in the provided path and file name, or in the default storage location of `<[user-home|~]>/.mnemosyne/entries/<datetime>.txt`, where `<datetime> is the current date and time of storage. The format of the representation can be found in the documentation for `create_Storage_representation`. If storage succeeds, a value of true is returned, if storage fails (due to inability to create a representaiton, or file IO issues) a value of false is returned.
        """
        # APIQ How does this app handle the computers timezone changing?

        # Make sure that the base directories actually exist
        directory_path.mkdir(parents=True, exist_ok=True)

        # Create a default file name if no filename is provided
        if not file_name:
            file_path = directory_path / datetime.now().strftime("%Y%m%d%H%M%S.txt")
        else:
            file_path = directory_path / file_name

        # Get the object representation
        representation = self.create_storage_representation()

        # Exit out of this method if a storage representation could not be generated
        if not representation:
            return False

        try:
            with open(file_path, "w") as my_file:
                my_file.write(representation)
                return True
        except IOError:
            # APIQ Should this generate a new obj error message to trace?
            return False

    def make_encryption_key(self, password: str) -> bool:
        """
        Uses the Argon2 hashing algorithm to hash the given text password into a 256bit hash that can be used as an encryption key, and on success stores the hash and parameters into this JournalEntry object. Exits with True if hashing succeeds, or gracefully exists with False if a hashing error occured. If a hashing error occurred, an error message will be logged into `.log_messages`. Providing an empty string as password will lead to a hashing error.
        """
        if not password:
            error_message = "[ERROR] No password provided to make_encryption_key fn."
            self.log_messages.append(error_message)
            print(error_message, file=stderr)
            return False

        # Hash the given text password
        argon2_helper = argon2.PasswordHasher()
        try:
            argon2_hash = argon2_helper.hash(password)
        except argon2.exceptions.HashingError:
            # Exit gracefully if a hashing error occured (e.g. time or memory constraints)
            error_message = f"[ERROR] Argon2 hashing failed for password <{password}>."
            self.log_messages.append(error_message)
            print(error_message, file=stderr)
            return False

        # Split the Argon2 return into its components
        _, type, version, params, salt, password_hash = argon2_hash.split("$")

        # Store the components as part of this object
        self.argon_type = type
        self.argon_version = version
        self.argon_params = params
        self.salt = salt
        self.password_hash = password_hash

        # Return if all went well
        return True  # Password hashing succesful

    def decrypt(self, password: str) -> bool:
        """
        Takes the object attributes `.plaintext`, `.password`, `.ciphertext`, `.nonce`, and `.salt` to try to attempt decrypting and verifying the integrity of the journal entry. If any of the attributes are missing in this object, it will gracefully return False and log a new error message in the `.log_messages` attribute of this object. If the decryption fails (either due to incorrect MAC or incorrect password), it will log a new error message in the `.log_messages` attribute and gracefully return False. If decryption succeeds, the decrypted context will be set to the `.plaintext` attribute and the method will return True.
        """
        # If .plaintext has contents already
        if self.plaintext:
            error_message = f"[ERROR] This JournalEntry object {id(self)} already has decrypted contents."
            self.log_messages.append(error_message)
            print(error_message, file=stderr)
            return False

        # Empty/Non-existant password string
        if not password:
            error_message = "[ERROR] No password str was provided to decrypt fn."
            self.log_messages.append(error_message)
            print(error_message, file=stderr)
            return False

        # Empty/Non-existant .ciphertext (--> nothing to decrypt)
        if not self.ciphertext:
            error_message = (
                f"[ERROR] No ciphertext present in this JournalEntry object {id(self)}"
            )
            self.log_messages.append(error_message)
            print(error_message, file=stderr)
            return False

        # Non-existent nonce (--> no decryption possible)
        if not self.nonce:
            error_message = (
                f"[ERROR] No nonce present in this JournalEntry object {id(self)}"
            )
            self.log_messages.append(error_message)
            print(error_message, file=stderr)
            return False

        # Non-existent salt (--> no decryption possible)
        if not self.salt:
            error_message = (
                f"[ERROR] No salt present in this JournalEntry object {id(self)}"
            )
            self.log_messages.append(error_message)
            print(error_message, file=stderr)
            return False

        # Get password hash using Argon2
        argon2_helper = argon2.PasswordHasher()
        password_hash = argon2_helper.hash(
            password, salt=base64.b64decode(self.salt + "=" * (-len(self.salt) % 4))
        ).split("$")[-1]

        # APIQ
        #  Q: Should this method also check whether the Argon2 version & other params are still the same as the ones that were originally used for encryption?
        #  Q: How should it handle if there are no Argon2 params present in the object? A hard fail seems incorrect in this case, as decryption might still be possible anyway.

        # Decrypt & Verify the ciphertext
        password_bytes = base64.b64decode(
            password_hash + "=" * (-len(password_hash) % 4)
        )
        cipher = AES.new(password_bytes, mode=AES.MODE_OCB, nonce=self.nonce)
        try:
            self.plaintext = cipher.decrypt_and_verify(
                self.ciphertext, self.tag
            ).decode("utf-8")
        except ValueError:
            error_message = f"[ERROR] Decryption of JournalEntry {id(self)} failed. Either wrong key or ciphertext was modified."
            self.log_messages.append(error_message)
            print(error_message, file=stderr)
            return False

        return True  # Decryption was successful

    @staticmethod
    def load_saved_journal_entry(
        file_name: str, directory_path: pathlib.Path = default_storage_location
    ):
        # TODO Add type (JournalEntry|None) with Python3.14 (See https://stackoverflow.com/questions/33533148/)
        """
        Using either the provided directory path or the default storage location at `<[user-home|~]/.mnemosyne/entries/>` looks for the entry using the given filename. If no entry can be found this method returns `None`. If the file is not a valid save file, this method will return `None`. Otherwise it will return an instance of JournalEntry with the contents of the save file.
        """

        file_path = directory_path / file_name

        # Ensure that the file exists before trying to read the file
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r") as my_file:
                # Read in the total file contents
                data = my_file.read()

                # Split the file into the different attributes (1 line per attribute)
                content = data.split("\n")

                # Rudimentary check if sufficient attributes were stored in the file
                if len(content) < 7:
                    # This file did not contain a valid JournalEntry storage
                    return None

                # Decode the text back into a JournalEntry object
                entry = JournalEntry()
                entry.nonce = base64.b64decode(content[0].split("$")[1])
                entry.tag = base64.b64decode(content[1].split("$")[1])
                entry.argon_type = content[2].split("$")[1]
                entry.argon_version = content[3].split("$")[1]
                entry.argon_params = content[4].split("$")[1]
                entry.salt = content[5].split("$")[1]
                entry.ciphertext = base64.b64decode(content[6].split("$")[1])
                return entry
        except IOError:
            # If there is some other issue with reading the file
            return None

    @staticmethod
    def list_stored_journal_entries(
        directory_path: pathlib.Path = default_storage_location,
    ) -> list[str]:
        """
        Returns a list of the file name stems (no suffix) of all the journal entries (text files) located in the default storage location at `<[user-home|~]/.mnemosyne/entries/>` or the provided directory path. This method ignores non `txt|text` files.
        """
        # APIQ Should this check the validity of the file name structure?

        # Ensure that the provided storage directory actually exists as a path
        directory_path.mkdir(parents=True, exist_ok=True)

        # List the stems (no suffix) of all text files in this directory
        entries_raw = [
            file_path.stem
            for file_path in directory_path.iterdir()
            if file_path.is_file() and file_path.suffix in [".txt", ".text"]
        ]

        # Check that each file entry name has a valid length
        entries_lengthchecked: list[str] = []
        for entry in entries_raw:
            if len(entry) == 14:
                entries_lengthchecked.append(entry)

        # Check that each file entry is a valid datetime
        entries_final: list[str] = []
        for entry in entries_lengthchecked:
            try:
                _ = datetime.strptime(entry, "%Y%m%d%H%M%S")
                entries_final.append(entry)
            except ValueError:
                # APIQ Is there a faster way to just drop invalid entries?
                pass

        # Return all valid entries
        return entries_final
