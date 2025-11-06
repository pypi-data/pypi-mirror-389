![Static Badge](https://img.shields.io/badge/Python-3.13-brightgreen?logo=python)
![Static Badge](https://img.shields.io/badge/License-GPLv3-brightgreen)

# Mnemosyne Journaling

A simple encrypted journaling application. Named after the ancient Greek goddess of memories.

## Usage

This app exposes a command line utility at `siru-mnemosyne`. Use `siru-mnemosyne --help` to get more information about available command arguments. Or simply run `siru-mnemosyne` to use the app in an interactive manner.

As for the command name, it is rather long, but this avoids having namespace issues with other apps as it is using a preexisting name. It is always possible to alias this to something quicker to type on the target system. For Windows look into the `doskey` command, and for Unix/Linux/MacOS look into the `alias` command.

## Encryption

The user entered password is hashed using the Argon2 hashing algorithm ([2015 Password Hashing Competition Winner and current recomendation (last checked 2025-10-22)](https://www.password-hashing.net/)). The hashing parameters used are 64MiB or RAM, 3 iterations, and a parralelism of 4.

The actual encryption is done using aes256 bit, with a 15 bit nonce. The aes mode used is OCB (offset codebook) which include both encryption and authentication (using a MAC tag) of the encrypted jouranl entry.

## Storage

The journal entries are stored in the user home folder under a `.mnemosyne/entries` subdirectory. These are plain text files containing the various encrypted pieces of information. This allows for portability with other software and prevents so called "lock-in," as all the information needed for decryption (apart from the password) is stored directly with each journal entry.

## Documentation

See full code documentation at the wiki section of the repository. This is located at [wiki](https://codeberg.org/siru/mnemosyne-journal/wiki).

## Lastly

To follow in the footsteps of one of my professors, if you actually read this far, please send me a simple picture of a cute otter, and I will be pleasantly surprised that people would actually read all of this.
