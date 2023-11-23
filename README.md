## Features

Run command: Install Missing Imports

Command will scan python file, gets list of missing pip modules and installs them.

## Requirements

Python extension for Visual Studio Code (Pylance)

## Extension Settings

This extension contributes the following settings:

* `pip-installer.enable`: Enable/disable this extension.

## Release Notes

Added command to scan python file, get list of missing modules and suggests installation.

### 0.0.1

Initial release

### 0.0.3

Fixed dot notation, script takes only package before first dot

### 0.0.4

Removed duplicates from missing imports array, changed the prompt message.